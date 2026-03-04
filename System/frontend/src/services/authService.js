import api from "./api";

export async function loginUser(payload) {
  const response = await api.post("/api/login/", payload);
  return response.data;
}
