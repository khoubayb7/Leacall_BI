import api from "./api";

export async function getClients() {
  const response = await api.get("/api/admin/clients/");
  return response.data;
}

export async function createClient(payload) {
  const response = await api.post("/api/admin/clients/", payload);
  return response.data;
}
