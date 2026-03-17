import AppShell from "../components/layouts/AppShell";

const adminMenu = [
  { to: "/admin/dashboard",     label: "Admin Dashboard", icon: "grid",    end: false },
  { to: "/admin/create-client", label: "Create Clients",  icon: "users",   end: false },
  { to: "/admin/etl-pipeline",  label: "ETL Pipeline",    icon: "chart",   end: false },
  { to: "/admin/kpi-dashboard", label: "KPI Dashboard",   icon: "chart",   end: false },
];

export default function AdminLayout() {
  return <AppShell brandName="Leacall BI" brandInitial="L" menuItems={adminMenu} />;
}
