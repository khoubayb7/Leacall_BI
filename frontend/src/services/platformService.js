import api from "./api";

export async function getClientPlatformData() {
  const response = await api.get("/api/client/platform/");
  return response.data;
}
