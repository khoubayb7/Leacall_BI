import { Navigate, Route, Routes } from "react-router-dom";

import AdminClients from "./pages/AdminClients";
import AdminDashboard from "./pages/AdminDashboard";
import AdminLayout from "./pages/AdminLayout";
import ClientLayout from "./pages/ClientLayout";
import ClientPlatform from "./pages/ClientPlatform";
import Login from "./pages/Login";
import ModulePlaceholder from "./pages/shared/ModulePlaceholder";
import { getDefaultRouteForStoredUser, getStoredUser } from "./services/authService";

function RequireAuth({ children }) {
  const user = getStoredUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function RoleGuard({ children, allowedRoles }) {
  const user = getStoredUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={getDefaultRouteForStoredUser()} replace />;
  }

  return children;
}

function PublicOnly({ children }) {
  const user = getStoredUser();
  if (user && ["admin", "client"].includes(user.role)) {
    return <Navigate to={getDefaultRouteForStoredUser()} replace />;
  }

  return children;
}

function CatchAllRoute() {
  const user = getStoredUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={getDefaultRouteForStoredUser()} replace />;
}

export default function AppRouter() {
  return (
    <Routes>
      <Route
        path="/login"
        element={(
          <PublicOnly>
            <Login />
          </PublicOnly>
        )}
      />

      <Route
        path="/admin"
        element={(
          <RoleGuard allowedRoles={["admin"]}>
            <AdminLayout />
          </RoleGuard>
        )}
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboard />} />
        <Route path="create-client" element={<AdminClients />} />
        <Route path="clients" element={<Navigate to="/admin/create-client" replace />} />
        <Route path="module-3" element={<ModulePlaceholder title="Button 3" description="This is a reserved admin module." />} />
        <Route path="module-4" element={<ModulePlaceholder title="Button 4" description="This module can host your admin settings or integrations." />} />
        <Route path="module-5" element={<ModulePlaceholder title="Button 5" description="This section can display admin notifications and alerts." />} />
      </Route>

      <Route
        path="/client"
        element={(
          <RoleGuard allowedRoles={["client"]}>
            <ClientLayout />
          </RoleGuard>
        )}
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<ClientPlatform />} />
        <Route path="platform" element={<Navigate to="/client/dashboard" replace />} />
        <Route path="my-calls" element={<ModulePlaceholder title="My Calls" description="Use this client module to track calls assigned to your account." />} />
        <Route path="reports" element={<ModulePlaceholder title="Reports" description="This client report area can show your conversion and pipeline metrics." />} />
        <Route path="tasks" element={<ModulePlaceholder title="Tasks" description="This task board can list your daily client actions." />} />
        <Route path="support" element={<ModulePlaceholder title="Support" description="This support module can display tickets and contact channels." />} />
      </Route>

      <Route
        path="/"
        element={(
          <RequireAuth>
            <Navigate to={getDefaultRouteForStoredUser()} replace />
          </RequireAuth>
        )}
      />

      <Route path="*" element={<CatchAllRoute />} />
    </Routes>
  );
}
