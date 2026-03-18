export const CLIENT_MODULE_OPTIONS = [
  { key: "dashboard", label: "Client Dashboard", route: "/client/dashboard", icon: "grid" },
  { key: "etl_pipeline", label: "ETL Pipeline", route: "/client/etl-pipeline", icon: "chart" },
  { key: "kpi_dashboard", label: "KPI Dashboard", route: "/client/kpi-dashboard", icon: "chart" },
];

const CLIENT_MODULE_KEYS = new Set(CLIENT_MODULE_OPTIONS.map((module) => module.key));

export function normalizeEnabledModules(modules) {
  if (!Array.isArray(modules)) {
    return ["dashboard"];
  }

  const uniqueModules = [];
  for (const moduleKey of modules) {
    if (CLIENT_MODULE_KEYS.has(moduleKey) && !uniqueModules.includes(moduleKey)) {
      uniqueModules.push(moduleKey);
    }
  }

  return uniqueModules.length > 0 ? uniqueModules : ["dashboard"];
}

export function getFirstEnabledModuleRoute(modules) {
  const firstModule = normalizeEnabledModules(modules)[0];
  const foundModule = CLIENT_MODULE_OPTIONS.find((module) => module.key === firstModule);
  return foundModule?.route || "/client/dashboard";
}

export function getClientModuleLabel(moduleKey) {
  const foundModule = CLIENT_MODULE_OPTIONS.find((module) => module.key === moduleKey);
  return foundModule?.label || moduleKey;
}
