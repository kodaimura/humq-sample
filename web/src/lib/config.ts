type RuntimeConfig = {
  API_URL?: string;
};

let runtimeConfig: RuntimeConfig = {};

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");

export const loadRuntimeConfig = async () => {
  const baseUrl = import.meta.env.BASE_URL || "/";
  const configUrl = `${baseUrl.replace(/\/?$/, "/")}env.json`;

  try {
    const response = await fetch(configUrl, { cache: "no-store" });
    if (!response.ok) return;

    runtimeConfig = (await response.json()) as RuntimeConfig;
  } catch {
    runtimeConfig = {};
  }
};

const resolveApiUrl = () => {
  const runtimeApiUrl = runtimeConfig.API_URL;
  const buildTimeApiUrl = import.meta.env.VITE_API_URL;
  const apiUrl = runtimeApiUrl || buildTimeApiUrl || "/api";

  return trimTrailingSlash(apiUrl);
};

export const appConfig = {
  get apiUrl() {
    return resolveApiUrl();
  },
};
