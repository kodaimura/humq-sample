import { appConfig } from "@lib/config";
import { buildLoginPathWithFrom, isPrivateRoutePath } from "@/routes";

export interface HttpErrorDetails {
  [key: string]: unknown;
}

export class HttpError extends Error {
  status: number;
  code: string;
  details: HttpErrorDetails;

  constructor(
    status: number,
    code: string,
    message: string,
    details: HttpErrorDetails = {},
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.name = "HttpError";
  }
}

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;
type RequestBody = Record<string, unknown> | FormData | null;

interface FetchOptions {
  method: HttpMethod;
  headers: Record<string, string>;
  credentials: RequestCredentials;
  body?: BodyInit;
}

export class Api {
  private refreshPromise: Promise<boolean> | null = null;
  private url: string;
  private accessToken: string | null = null;
  private onAccessTokenRefresh?: (token: string) => void;

  constructor(url: string, onAccessTokenRefresh?: (token: string) => void) {
    this.url = url;
    this.onAccessTokenRefresh = onAccessTokenRefresh;
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  setAccessTokenCallback(callback?: (token: string) => void) {
    this.onAccessTokenRefresh = callback;
  }

  private createFetchOptions(
    method: HttpMethod,
    body?: RequestBody,
  ): FetchOptions {
    const headers: Record<string, string> = {};

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    const options: FetchOptions = {
      method,
      headers,
      credentials: "include",
    };

    if (body instanceof FormData) {
      options.body = body;
    } else if (body) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }

    return options;
  }

  private normalizeEndpoint(endpoint: string): string {
    return endpoint.startsWith("/") ? endpoint.slice(1) : endpoint;
  }

  private async fetchWithTokenRefresh(
    endpoint: string,
    method: HttpMethod,
    body?: RequestBody,
    retry = true,
  ): Promise<Response> {
    const normalizedEndpoint = this.normalizeEndpoint(endpoint);
    const response = await fetch(
      `${this.url}/${normalizedEndpoint}`,
      this.createFetchOptions(method, body),
    );

    const canRefresh =
      response.status === 401 &&
      retry &&
      !normalizedEndpoint.endsWith("auth/login");

    if (!canRefresh || !(await this.tryRefreshToken())) {
      return response;
    }

    return this.fetchWithTokenRefresh(normalizedEndpoint, method, body, false);
  }

  private async createHttpError(response: Response): Promise<HttpError> {
    let errorData: {
      code?: string;
      detail?: string;
      message?: string;
      details?: HttpErrorDetails;
      errors?: HttpErrorDetails;
    } = {
      message: "Unknown error",
      details: {},
    };

    try {
      errorData = await response.json();
    } catch {
      // ignore parse error
    }

    return new HttpError(
      response.status,
      errorData.code || "UNKNOWN_ERROR",
      errorData.message ||
        errorData.code ||
        errorData.detail ||
        "Unknown error",
      errorData.details || errorData.errors || {},
    );
  }

  private async apiFetch<T>(
    endpoint: string,
    method: HttpMethod,
    body?: RequestBody,
    retry = true,
  ): Promise<T> {
    const response = await this.fetchWithTokenRefresh(
      endpoint,
      method,
      body,
      retry,
    );

    if (!response.ok) {
      const error = await this.createHttpError(response);
      this.handleHttpError(error);
      throw error;
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  private async tryRefreshToken(): Promise<boolean> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      try {
        const response = await fetch(`${this.url}/auth/refresh`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (!response.ok) return false;

        const data = (await response.json()) as { access_token?: unknown };
        const newToken = data.access_token;
        if (typeof newToken !== "string" || !newToken) return false;

        this.accessToken = newToken;
        this.onAccessTokenRefresh?.(newToken);

        return true;
      } catch {
        return false;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  async get<TResponse = void, TParams extends QueryParams = QueryParams>(
    endpoint: string,
    params?: TParams | null,
  ): Promise<TResponse> {
    if (params && typeof params === "object") {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          query.set(key, String(value));
        }
      });
      const queryString = query.toString();
      if (queryString) endpoint += `?${queryString}`;
    }
    return this.apiFetch<TResponse>(endpoint, "GET");
  }

  async post<TResponse = void, TBody extends RequestBody = RequestBody>(
    endpoint: string,
    body?: TBody,
  ): Promise<TResponse> {
    return this.apiFetch<TResponse>(endpoint, "POST", body);
  }

  async put<TResponse = void, TBody extends RequestBody = RequestBody>(
    endpoint: string,
    body?: TBody,
  ): Promise<TResponse> {
    return this.apiFetch<TResponse>(endpoint, "PUT", body);
  }

  async delete<TResponse = void, TBody extends RequestBody = RequestBody>(
    endpoint: string,
    body?: TBody,
  ): Promise<TResponse> {
    return this.apiFetch<TResponse>(endpoint, "DELETE", body);
  }

  async patch<TResponse = void, TBody extends RequestBody = RequestBody>(
    endpoint: string,
    body?: TBody,
  ): Promise<TResponse> {
    return this.apiFetch<TResponse>(endpoint, "PATCH", body);
  }

  async getBlob(endpoint: string, retry = true): Promise<Blob> {
    const response = await this.fetchWithTokenRefresh(
      endpoint,
      "GET",
      undefined,
      retry,
    );

    if (!response.ok) {
      throw new HttpError(
        response.status,
        "BLOB_ERROR",
        "Blob request failed",
        {},
      );
    }

    return response.blob();
  }

  private handleHttpError(error: HttpError): void {
    console.error(error);
    const status = error.status;

    if (
      status === 401 &&
      (error.code.startsWith("AUTH_") || error.code.startsWith("REFRESH_")) &&
      isPrivateRoutePath(window.location.pathname)
    ) {
      const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      window.location.replace(buildLoginPathWithFrom(currentPath));
    }
  }
}

export const api = new Api(appConfig.apiUrl);
