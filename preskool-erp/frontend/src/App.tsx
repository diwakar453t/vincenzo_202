import { useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import DashboardLayout, { NavItem } from "./layouts/DashboardLayout";
import { RoleProtectedRoute, roleDashboard } from "./components/auth/RoleProtectedRoute";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ResourcePage from "./pages/ResourcePage";
import { hydrateUser } from "./store/slices/authSlice";
import type { AppDispatch, RootState } from "./store/store";

const theme = createTheme({
  typography: { fontFamily: "Outfit, sans-serif" },
  shape: { borderRadius: 12 },
  palette: {
    primary: { main: "#3D5EE1" },
    success: { main: "#10b981" },
    warning: { main: "#f59e0b" },
    background: { default: "#f4f7fb" },
  },
});

const adminNav: NavItem[] = [
  { label: "Dashboard", path: "/admin-dashboard" },
  { label: "Students", path: "/students" },
  { label: "Teachers", path: "/teachers" },
  { label: "Classes", path: "/classes" },
  { label: "Subjects", path: "/subjects" },
  { label: "Departments", path: "/departments" },
  { label: "Timetable", path: "/timetable" },
  { label: "Attendance", path: "/attendance" },
  { label: "Exams", path: "/exams" },
  { label: "Grades", path: "/grades" },
  { label: "Fees", path: "/fees" },
  { label: "Payroll", path: "/payroll" },
  { label: "Leave", path: "/leave" },
  { label: "Library", path: "/library" },
  { label: "Hostel", path: "/hostel" },
  { label: "Transport", path: "/transport" },
  { label: "Sports", path: "/sports" },
  { label: "Rooms", path: "/rooms" },
  { label: "Guardians", path: "/guardians" },
  { label: "Reports", path: "/reports" },
  { label: "Notifications", path: "/notifications" },
  { label: "Files", path: "/files" },
  { label: "Payments", path: "/payments" },
  { label: "Settings", path: "/settings" },
  { label: "Plugins", path: "/plugins" }
];

const teacherNav: NavItem[] = [
  { label: "Dashboard", path: "/teacher-dashboard" },
  { label: "Classes", path: "/classes" },
  { label: "Attendance", path: "/attendance" },
  { label: "Grades", path: "/grades" },
  { label: "Timetable", path: "/timetable" },
  { label: "Syllabus", path: "/syllabus" },
  { label: "Leave", path: "/leave" },
  { label: "Notifications", path: "/notifications" },
  { label: "Profile", path: "/profile" },
];

const studentNav: NavItem[] = [
  { label: "Dashboard", path: "/student-dashboard" },
  { label: "Timetable", path: "/timetable" },
  { label: "Subjects", path: "/subjects" },
  { label: "Syllabus", path: "/syllabus" },
  { label: "Files", path: "/files" },
  { label: "Grades", path: "/grades" },
  { label: "Attendance", path: "/attendance" },
  { label: "Fees", path: "/fees" },
  { label: "Library", path: "/library" },
  { label: "Notifications", path: "/notifications" },
  { label: "Profile", path: "/profile" },
];

const parentNav: NavItem[] = [
  { label: "Dashboard", path: "/parent-dashboard" },
  { label: "Children", path: "/guardians" },
  { label: "Attendance", path: "/attendance" },
  { label: "Grades", path: "/grades" },
  { label: "Fees", path: "/fees" },
  { label: "Notifications", path: "/notifications" },
  { label: "Profile", path: "/profile" },
];

const superAdminNav: NavItem[] = [
  { label: "Super Admin Dashboard", path: "/super-admin-dashboard" },
  { label: "Admin Panel", path: "/admin-dashboard" },
  { label: "Settings", path: "/settings" },
  { label: "Plugins", path: "/plugins" },
  { label: "Students", path: "/students" },
  { label: "Teachers", path: "/teachers" },
  { label: "Departments", path: "/departments" },
  { label: "Fees", path: "/fees" },
  { label: "Payroll", path: "/payroll" },
  { label: "Payments", path: "/payments" },
  { label: "Reports", path: "/reports" },
];

const resourceMap: Record<string, { title: string; fields: string[] }> = {
  students: { title: "Students", fields: ["student_id", "first_name", "last_name", "date_of_birth", "gender", "email", "enrollment_date"] },
  teachers: { title: "Teachers", fields: ["employee_id", "first_name", "last_name", "date_of_birth", "gender", "hire_date", "email"] },
  classes: { title: "Classes", fields: ["name", "grade_level", "section", "academic_year", "room_number", "capacity"] },
  subjects: { title: "Subjects", fields: ["name", "code", "description", "credits"] },
  departments: { title: "Departments", fields: ["name", "code", "description"] },
  timetable: { title: "Timetable", fields: ["class_id", "subject_id", "teacher_id", "day_of_week", "start_time", "end_time", "period_number", "academic_year"] },
  attendance: { title: "Attendance", fields: ["student_id", "class_id", "date", "status", "academic_year"] },
  exams: { title: "Exams", fields: ["name", "exam_type", "class_id", "subject_id", "date", "total_marks", "passing_marks", "academic_year"] },
  grades: { title: "Grades", fields: ["student_id", "exam_id", "subject_id", "marks_obtained", "grade", "academic_year"] },
  fees: { title: "Student Fee Assignments", fields: ["student_id", "fee_type_id", "amount", "discount", "net_amount", "paid_amount", "balance", "status"] },
  payroll: { title: "Salary Structures", fields: ["teacher_id", "basic_salary", "hra", "da", "ta", "net_salary", "effective_from"] },
  leave: { title: "Leave Requests", fields: ["user_id", "leave_type", "start_date", "end_date", "reason", "status"] },
  library: { title: "Books", fields: ["title", "isbn", "author", "publisher", "total_copies", "available_copies", "status"] },
  hostel: { title: "Hostels", fields: ["name", "code", "hostel_type", "total_rooms", "total_beds", "monthly_fee"] },
  transport: { title: "Transport Routes", fields: ["route_name", "route_code", "start_point", "end_point", "distance_km", "status"] },
  sports: { title: "Sports", fields: ["name", "code", "category", "coach_name", "venue", "status"] },
  rooms: { title: "Rooms", fields: ["name", "room_number", "building", "floor", "capacity", "room_type"] },
  guardians: { title: "Guardians", fields: ["user_id", "student_id", "relationship", "phone", "occupation"] },
  reports: { title: "Reports", fields: ["title", "report_type", "generated_by", "format", "file_path"] },
  notifications: { title: "Notifications", fields: ["title", "message", "notification_type", "priority", "sender_id"] },
  files: { title: "Files", fields: ["filename", "original_filename", "file_size", "file_path", "uploaded_by"] },
  payments: { title: "Payments", fields: ["student_id", "amount", "payment_method", "payment_date", "status", "transaction_id"] },
  settings: { title: "Settings", fields: ["key", "value", "category", "description"] },
  plugins: { title: "Plugins", fields: ["name", "version", "description", "is_enabled", "config"] },
  syllabus: { title: "Syllabus", fields: ["subject_id", "class_id", "title", "description", "topics", "academic_year", "completion_percentage"] },
  profile: { title: "Profile", fields: ["full_name", "email", "role"] },
};

function LayoutForRole({ role, children }: { role?: string; children: React.ReactNode }) {
  const items = role === "super_admin" ? superAdminNav : role === "admin" ? adminNav : role === "teacher" ? teacherNav : role === "student" ? studentNav : parentNav;
  return <DashboardLayout items={items} title="PreSkool ERP">{children}</DashboardLayout>;
}

export default function App() {
  const dispatch = useDispatch<AppDispatch>();
  const role = useSelector((state: RootState) => state.auth.user?.role);

  useEffect(() => {
    dispatch(hydrateUser());
  }, [dispatch]);

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to={roleDashboard(role)} replace />} />

          <Route element={<RoleProtectedRoute allowedRoles={["admin", "super_admin", "superadmin"]} role={role} />}>
            <Route path="/admin-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Admin Dashboard" /></LayoutForRole>} />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={["super_admin", "superadmin"]} role={role} />}>
            <Route path="/super-admin-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Super Admin Dashboard" /></LayoutForRole>} />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={["teacher"]} role={role} />}>
            <Route path="/teacher-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Teacher Dashboard" /></LayoutForRole>} />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={["student"]} role={role} />}>
            <Route path="/student-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Student Dashboard" /></LayoutForRole>} />
          </Route>
          <Route element={<RoleProtectedRoute allowedRoles={["parent"]} role={role} />}>
            <Route path="/parent-dashboard" element={<LayoutForRole role={role}><DashboardPage title="Parent Dashboard" /></LayoutForRole>} />
          </Route>

          {Object.entries(resourceMap).map(([path, config]) => (
            <Route
              key={path}
              path={`/${path}`}
                      element={<LayoutForRole role={role}><ResourcePage resource={path === "fees" ? "student-fee-assignments" : path === "payroll" ? "salary-structures" : path === "library" ? "books" : path === "hostel" ? "hostel" : path === "transport" ? "transport" : path} title={config.title} fields={config.fields} /></LayoutForRole>}
            />
          ))}

          <Route path="*" element={<Navigate to={roleDashboard(role)} replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
