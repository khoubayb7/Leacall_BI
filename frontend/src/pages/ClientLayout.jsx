import AppShell from "../components/layouts/AppShell";
import { CLIENT_MODULE_OPTIONS, normalizeEnabledModules } from "../constants/clientModules";
import { getStoredUser } from "../services/authService";

export default function ClientLayout() {
  const user = getStoredUser();
  const enabledModules = new Set(normalizeEnabledModules(user?.enabled_modules));

  const clientMenu = CLIENT_MODULE_OPTIONS
    .filter((module) => enabledModules.has(module.key))
    .map((module) => ({ to: module.route, label: module.label, icon: module.icon, end: false }));

  return <AppShell brandName="Leacall BI" brandInitial="L" menuItems={clientMenu} />;
}
