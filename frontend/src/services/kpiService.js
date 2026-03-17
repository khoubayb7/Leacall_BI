import api from "./api";

export async function generateKPI(payload) {
  const response = await api.post("/api/kpis/generate/", payload);
  return response.data;
}

export async function getKPICampaignOptions() {
  const response = await api.get("/api/kpis/campaign-options/");
  return response.data?.campaigns || [];
}

export async function listKPIExecutions({ limit = 20, campaignName = "", campaignId = "" } = {}) {
  const params = { limit };
  if (campaignName) {
    params.campaign_name = campaignName;
  }
  if (campaignId) {
    params.campaign_id = campaignId;
  }
  const response = await api.get("/api/kpis/executions/", { params });
  return response.data?.results || [];
}

export async function getKPIExecution(executionId) {
  const response = await api.get(`/api/kpis/executions/${executionId}/`);
  return response.data;
}

export async function getKPIExecutionByTask(taskId) {
  const response = await api.get(`/api/kpis/executions/by-task/${taskId}/`);
  return response.data;
}
