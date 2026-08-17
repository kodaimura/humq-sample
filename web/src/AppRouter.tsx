import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";
import { useAuth } from "@contexts/AuthContext";
import { buildLoginPathWithFrom, ROUTES } from "@/routes";
import LayoutPublic from "@layouts/LayoutPublic";
import LayoutPrivate from "@layouts/LayoutPrivate";
import Processing from "@ui/Processing";
import Login from "@pages/login/Login";
import Signup from "@pages/signup/Signup";
import ForgotPassword from "@pages/forgot-password/ForgotPassword";
import ResetPassword from "@pages/reset-password/ResetPassword";
import ChangePassword from "@pages/change-password/ChangePassword";
import Dashboard from "@pages/dashboard/Dashboard";
import Organizations from "@pages/organizations/Organizations";
import Catalog from "@pages/catalog/Catalog";
import Inventory from "@pages/inventory/Inventory";
import Orders from "@pages/orders/Orders";
import Shipments from "@pages/shipments/Shipments";
import NotFound from "@pages/notfound/NotFound";

const PrivateRoute = () => {
  const { account, loading } = useAuth();
  const location = useLocation();
  const currentPath = `${location.pathname}${location.search}${location.hash}`;

  if (loading) return <Processing text="読み込み中..." />;
  if (!account)
    return <Navigate to={buildLoginPathWithFrom(currentPath)} replace />;

  return (
    <LayoutPrivate>
      <Outlet />
    </LayoutPrivate>
  );
};

const GuestRoute = () => {
  const { account, loading } = useAuth();

  if (loading) return <Processing text="読み込み中..." />;
  if (account) return <Navigate to={ROUTES.dashboard} replace />;

  return <Outlet />;
};

const PublicLayoutRoute = () => {
  return (
    <LayoutPublic>
      <Outlet />
    </LayoutPublic>
  );
};

const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayoutRoute />}>
          <Route element={<GuestRoute />}>
            <Route path={ROUTES.login} element={<Login />} />
            <Route path={ROUTES.signup} element={<Signup />} />
            <Route path={ROUTES.forgotPassword} element={<ForgotPassword />} />
          </Route>
          <Route path={ROUTES.resetPassword} element={<ResetPassword />} />
        </Route>

        <Route element={<PrivateRoute />}>
          <Route path={ROUTES.home} element={<Dashboard />} />
          <Route path={ROUTES.changePassword} element={<ChangePassword />} />
          <Route path={ROUTES.organizations} element={<Organizations />} />
          <Route path={ROUTES.catalog} element={<Catalog />} />
          <Route path={ROUTES.inventory} element={<Inventory />} />
          <Route path={ROUTES.orders} element={<Orders />} />
          <Route path={ROUTES.shipments} element={<Shipments />} />
          <Route
            path={ROUTES.dashboard}
            element={<Navigate to={ROUTES.home} replace />}
          />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
