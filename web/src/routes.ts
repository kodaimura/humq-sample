export const ROUTES = {
  catalog: "/catalog",
  changePassword: "/change-password",
  dashboard: "/dashboard",
  forgotPassword: "/forgot-password",
  home: "/",
  inventory: "/inventory",
  login: "/login",
  orders: "/orders",
  organizations: "/organizations",
  resetPassword: "/reset-password",
  shipments: "/shipments",
  signup: "/signup",
} as const;

export const PUBLIC_ROUTE_PATHS = [
  ROUTES.login,
  ROUTES.signup,
  ROUTES.forgotPassword,
  ROUTES.resetPassword,
] as const;

export const PRIVATE_ROUTE_PATHS = [
  ROUTES.home,
  ROUTES.dashboard,
  ROUTES.changePassword,
  ROUTES.organizations,
  ROUTES.catalog,
  ROUTES.inventory,
  ROUTES.orders,
  ROUTES.shipments,
] as const;

export const REDIRECT_PARAM = "from";
export const PASSWORD_CHANGED_PARAM = "password_changed";

export const isPublicRoutePath = (pathname: string) =>
  PUBLIC_ROUTE_PATHS.some((path) => path === pathname);

export const isPrivateRoutePath = (pathname: string) =>
  PRIVATE_ROUTE_PATHS.some((path) => path === pathname);

export const buildLoginPathWithFrom = (from: string) => {
  const params = new URLSearchParams({ [REDIRECT_PARAM]: from });
  return `${ROUTES.login}?${params.toString()}`;
};

export const getSafeRedirectPath = (
  from: string | null,
  fallback = ROUTES.dashboard,
) => {
  if (!from || from.includes("\\") || from.startsWith("//")) {
    return fallback;
  }

  try {
    const url = new URL(from, "http://app.local");
    if (url.origin !== "http://app.local") return fallback;
    if (isPublicRoutePath(url.pathname)) return fallback;

    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return fallback;
  }
};
