import api from "./api";
import { getFirstEnabledModuleRoute } from "../constants/clientModules";

export function getDefaultRouteForRole(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "client") return getFirstEnabledModuleRoute(["dashboard"]);
  return "/login";
}

export function getDefaultRouteForUser(user) {
  if (user?.role === "admin") return "/admin/dashboard";
  if (user?.role === "client") return getFirstEnabledModuleRoute(user?.enabled_modules);
  return "/login";
}

export async function loginUser(payload) {
  const response = await api.post("/api/login/", payload);
  const data = response.data;

  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  localStorage.setItem("user", JSON.stringify(data.user));

  return data;
}

export async function logoutUser() {
  const refresh = localStorage.getItem("refresh_token");
  if (refresh) {
    try {
      await api.post("/api/logout/", { refresh });
    } catch {
      // Ignore logout API errors and clear local session anyway.
    }
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getStoredUser() {
  const raw = localStorage.getItem("user");
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function getDefaultRouteForStoredUser() {
  return getDefaultRouteForUser(getStoredUser());
}
