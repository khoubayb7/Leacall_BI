import AppShell from "../components/layouts/AppShell";

const clientMenu = [
  { to: "/client/dashboard", label: "Client Dashboard", icon: "grid", end: false },
  { to: "/client/my-calls", label: "My Calls", icon: "phone", end: false },
  { to: "/client/reports", label: "Reports", icon: "chart", end: false },
  { to: "/client/tasks", label: "Tasks", icon: "file", end: false },
  { to: "/client/support", label: "Support", icon: "bell", end: false },
];

export default function ClientLayout() {
  return <AppShell brandName="CallTracker" brandInitial="C" menuItems={clientMenu} />;
}
