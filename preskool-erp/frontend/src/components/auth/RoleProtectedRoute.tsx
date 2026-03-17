import { Navigate, Outlet } from "react-router-dom";

const dashboardByRole: Record<string, string> = {
  super_admin: "/super-admin-dashboard",
  superadmin: "/super-admin-dashboard",
  admin: "/admin-dashboard",
  teacher: "/teacher-dashboard",
  student: "/student-dashboard",
  parent: "/parent-dashboard",
};

export function RoleProtectedRoute({ allowedRoles, role }: { allowedRoles: string[]; role?: string }) {
  if (!role) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles.includes(role)) {
    return <Outlet />;
  }
  return <Navigate to={dashboardByRole[role] ?? "/profile"} replace />;
}

export function roleDashboard(role?: string) {
  return (role && dashboardByRole[role]) || "/profile";
}
