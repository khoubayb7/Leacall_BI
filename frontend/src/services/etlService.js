import api from "./api";

// ── Data sources ──────────────────────────────────────────────────────────────

export async function getDataSources() {
  const response = await api.get("/api/etl/sources/");
  return response.data;
}

export async function createDataSource(payload) {
  const response = await api.post("/api/etl/sources/", payload);
  return response.data;
}

// ── ETL runs ─────────────────────────────────────────────────────────────────

export async function getETLRuns() {
  const response = await api.get("/api/etl/runs/");
  return response.data;
}

// ── Trigger sync ──────────────────────────────────────────────────────────────

export async function triggerSync(dataSourceId) {
  const response = await api.post("/api/etl/sync/", { data_source_id: dataSourceId });
  return response.data;
}
