import api from "./api";

export async function getClients() {
  const response = await api.get("/api/admin/clients/");
  return response.data;
}

export async function createClient(payload) {
  const response = await api.post("/api/admin/clients/", payload);
  return response.data;
}

export async function updateClient(clientId, payload) {
  const response = await api.put(`/api/admin/clients/${clientId}/`, payload);
  return response.data;
}

export async function deleteClient(clientId) {
  await api.delete(`/api/admin/clients/${clientId}/`);
}
