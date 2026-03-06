import AppShell from "../components/layouts/AppShell";

const adminMenu = [
  { to: "/admin/dashboard", label: "Admin Dashboard", icon: "grid", end: false },
  { to: "/admin/create-client", label: "Create Clients", icon: "users", end: false },
  { to: "/admin/module-3", label: "Button 3", icon: "file", end: false },
  { to: "/admin/module-4", label: "Button 4", icon: "settings", end: false },
  { to: "/admin/module-5", label: "Button 5", icon: "bell", end: false },
];

export default function AdminLayout() {
  return <AppShell brandName="Leacall BI" brandInitial="L" menuItems={adminMenu} />;
}
