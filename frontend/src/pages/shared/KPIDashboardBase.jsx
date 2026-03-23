import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import AlertBox from "../../components/ui/AlertBox";
import AppButton from "../../components/ui/AppButton";
import DataTable from "../../components/ui/DataTable";
import PageHeader from "../../components/ui/PageHeader";
import StatCard from "../../components/ui/StatCard";
import SurfaceCard from "../../components/ui/SurfaceCard";
import { logoutUser } from "../../services/authService";
import { getETLRuns } from "../../services/etlService";
import {
  generateKPI,
  getKPICampaignOptions,
  getKPIExecutionByTask,
  listKPIExecutions,
} from "../../services/kpiService";

const INITIAL_FORM = {
  campaign_name: "",
};

const DEFAULT_COPY = {
  eyebrow: "Agent KPIs",
  title: "KPI dashboard",
  campaignFieldLabel: "Campaign name (from datasource)",
  selectedCampaignIdLabel: "Campaign id used",
  formSectionTitle: "Generate or refresh KPI",
  latestSectionTitle: "Latest KPI output (template values)",
  historySectionTitle: "Execution history (persistent)",
};

function extractApiError(error, fallbackMessage) {
  const apiError = error?.response?.data;
  if (!apiError || typeof apiError !== "object") {
    return fallbackMessage;
  }

  const firstKey = Object.keys(apiError)[0];
  const firstValue = apiError[firstKey];
  if (Array.isArray(firstValue)) {
    return firstValue[0];
  }
  if (typeof firstValue === "string") {
    return firstValue;
  }

  return fallbackMessage;
}

function renderPayloadRows(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return [];
  }

  return Object.entries(payload).map(([key, value]) => {
    const pretty = typeof value === "object" ? JSON.stringify(value) : String(value);
    return { key, value: pretty };
  });
}

export default function KPIDashboardBase({ copy = {} }) {
  const labels = { ...DEFAULT_COPY, ...copy };
  const navigate = useNavigate();
  const pollRef = useRef(null);

  const [form, setForm] = useState(INITIAL_FORM);
  const [creating, setCreating] = useState(false);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [pageError, setPageError] = useState("");
  const [history, setHistory] = useState([]);
  const [etlRuns, setEtlRuns] = useState([]);
  const [loadingEtlRuns, setLoadingEtlRuns] = useState(true);
  const [etlRunsUnavailable, setEtlRunsUnavailable] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [latestExecution, setLatestExecution] = useState(null);
  const [activeTaskId, setActiveTaskId] = useState("");
  const [message, setMessage] = useState({ type: "", text: "" });

  const payloadRows = useMemo(() => renderPayloadRows(latestExecution?.kpi_payload), [latestExecution]);
  const selectedCampaign = useMemo(
    () => campaigns.find((item) => item.campaign_name === form.campaign_name),
    [campaigns, form.campaign_name],
  );

  const selectedCampaignId = selectedCampaign?.campaign_id || "";
  const selectedCampaignType = selectedCampaign?.campaign_type || "";
  const selectedDataSourceId = selectedCampaign?.data_source_id;

  const hasSuccessfulKpiForSelectedCampaign = useMemo(() => {
    if (!selectedCampaignId) {
      return false;
    }
    return history.some(
      (row) => row.campaign_id === selectedCampaignId && row.status === "success",
    );
  }, [history, selectedCampaignId]);

  const hasLoadedEtlData = useMemo(() => {
    if (!selectedDataSourceId) {
      return false;
    }
    const hasSuccessfulLoadedRun = etlRuns.some(
      (run) => Number(run.data_source) === Number(selectedDataSourceId)
        && run.status === "success"
        && Number(run.loaded_count || 0) > 0,
    );
    return hasSuccessfulLoadedRun || hasSuccessfulKpiForSelectedCampaign;
  }, [etlRuns, selectedDataSourceId, hasSuccessfulKpiForSelectedCampaign]);

  const upsertHistoryRow = (execution) => {
    if (!execution?.id) {
      return;
    }
    setHistory((prev) => {
      const withoutRow = prev.filter((row) => row.id !== execution.id);
      return [execution, ...withoutRow].slice(0, 20);
    });
  };

  const loadHistory = async (campaignFilter = {}) => {
    setLoadingHistory(true);
    try {
      const rows = await listKPIExecutions(campaignFilter);
      setHistory(rows);
      setLatestExecution(rows[0] || null);
      setPageError("");
    } catch (err) {
      const s = err?.response?.status;
      if (s === 401 || s === 403) {
        await logoutUser();
        navigate("/login", { replace: true });
        return;
      }
      setPageError("Unable to load KPI history.");
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    const loadCampaigns = async () => {
      setLoadingCampaigns(true);
      try {
        const rows = await getKPICampaignOptions();
        setCampaigns(rows);
        setPageError("");
        setForm((prev) => ({
          ...prev,
          campaign_name: prev.campaign_name || (rows[0]?.campaign_name || ""),
        }));
      } catch (err) {
        const s = err?.response?.status;
        if (s === 401 || s === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setPageError("Unable to load campaign dropdown options.");
      } finally {
        setLoadingCampaigns(false);
      }
    };

    loadCampaigns();

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, [navigate]);

  useEffect(() => {
    const loadEtlRuns = async () => {
      setLoadingEtlRuns(true);
      setEtlRunsUnavailable(false);
      try {
        const rows = await getETLRuns();
        setEtlRuns(rows || []);
      } catch (err) {
        const s = err?.response?.status;
        if (s === 401 || s === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setEtlRuns([]);
        setEtlRunsUnavailable(true);
      } finally {
        setLoadingEtlRuns(false);
      }
    };

    loadEtlRuns();
  }, [navigate]);

  useEffect(() => {
    if (!form.campaign_name && !selectedCampaignId) {
      return;
    }
    loadHistory({
      campaignName: form.campaign_name,
      campaignId: selectedCampaignId,
    });
  }, [form.campaign_name, selectedCampaignId]);

  const onFormChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = (taskId) => {
    stopPolling();
    const startedAt = Date.now();

    pollRef.current = setInterval(async () => {
      try {
        const execution = await getKPIExecutionByTask(taskId);
        setLatestExecution(execution);

        if (
          (execution.status === "queued" || execution.status === "running")
          && Date.now() - startedAt > 120000
        ) {
          stopPolling();
          setActiveTaskId("");
          setMessage({
            type: "error",
            text: "KPI task is taking too long (over 2 minutes). Check Celery worker logs and try refreshing KPI values.",
          });
          return;
        }

        if (execution.status === "success" || execution.status === "failed") {
          stopPolling();
          setActiveTaskId("");
          setMessage({
            type: execution.status === "success" ? "success" : "error",
            text: execution.status === "success" ? "KPI execution completed." : "KPI execution failed.",
          });
          upsertHistoryRow(execution);
          await loadHistory({
            campaignName: form.campaign_name,
            campaignId: selectedCampaignId,
          });
        }
      } catch (err) {
        if (err?.response?.status === 404) {
          if (Date.now() - startedAt > 45000) {
            stopPolling();
            setActiveTaskId("");
            setMessage({
              type: "error",
              text: "KPI task is still not visible after 45s. Check that Celery worker is running and restarted.",
            });
          }
          return;
        }

        stopPolling();
        setActiveTaskId("");
        setMessage({ type: "error", text: "Polling failed while waiting for KPI execution." });
      }
    }, 2000);
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });
    setLatestExecution(null);
    setCreating(true);

    try {
      const response = await generateKPI({
        campaign_name: form.campaign_name,
        campaign_id: selectedCampaignId,
        campaign_type: selectedCampaignType,
      });

      if (response.execution) {
        setActiveTaskId("");
        setLatestExecution(response.execution);
        setMessage({ type: "success", text: "KPI values refreshed." });
        await loadHistory({
          campaignName: form.campaign_name,
          campaignId: selectedCampaignId,
        });
        return;
      }

      const taskId = response.task_id;
      setActiveTaskId(taskId || "");
      setMessage({ type: "success", text: `KPI generation queued. Task id: ${taskId}` });
      if (taskId) {
        startPolling(taskId);
      }
    } catch (err) {
      const s = err?.response?.status;
      if (s === 401 || s === 403) {
        await logoutUser();
        navigate("/login", { replace: true });
        return;
      }
      setMessage({ type: "error", text: extractApiError(err, "Unable to queue KPI generation.") });
    } finally {
      setCreating(false);
    }
  };

  return (
    <section className="workspace-content">
      <PageHeader
        eyebrow={labels.eyebrow}
        title={labels.title}
        action={(
          <AppButton
            variant="secondary"
            compact
            type="button"
            onClick={handleGenerate}
            disabled={creating || loadingCampaigns || !form.campaign_name}
          >
            {creating ? "Refreshing..." : "Refresh KPI values"}
          </AppButton>
        )}
      />

      <div className="stats-grid">
        <StatCard label="Total executions" value={loadingHistory ? "..." : history.length} />
        <StatCard
          label="Success"
          value={loadingHistory ? "..." : history.filter((x) => x.status === "success").length}
          valueStyle={{ color: "var(--success)" }}
        />
        <StatCard
          label="Failed"
          value={loadingHistory ? "..." : history.filter((x) => x.status === "failed").length}
          valueStyle={{ color: "var(--danger)" }}
        />
      </div>

      <SurfaceCard title={labels.formSectionTitle}>
        <form className="grid-form" onSubmit={handleGenerate}>
          {pageError ? (
            <div className="full-row">
              <AlertBox type="error">{pageError}</AlertBox>
            </div>
          ) : null}

          <label className="form-label">
            <span>{labels.campaignFieldLabel}</span>
            <select
              className="form-input"
              name="campaign_name"
              value={form.campaign_name}
              onChange={onFormChange}
              disabled={loadingCampaigns}
              required
            >
              <option value="">Select campaign</option>
              {campaigns.map((item) => (
                <option key={`${item.campaign_name}-${item.campaign_id}`} value={item.campaign_name}>
                  {item.campaign_name}
                </option>
              ))}
            </select>
          </label>

          {selectedCampaignId ? (
            <div className="full-row">
              <AlertBox type="success">{labels.selectedCampaignIdLabel}: {selectedCampaignId}</AlertBox>
            </div>
          ) : null}

          {!loadingEtlRuns && !etlRunsUnavailable && selectedCampaignId && !hasLoadedEtlData ? (
            <div className="full-row">
              <AlertBox type="error">
                No loaded ETL records yet for this campaign. Run ETL first, then generate KPI.
              </AlertBox>
            </div>
          ) : null}

          {activeTaskId ? (
            <div className="full-row">
              <AlertBox type="success">Task in progress: {activeTaskId}</AlertBox>
            </div>
          ) : null}

          {message.text ? (
            <div className="full-row">
              <AlertBox type={message.type === "error" ? "error" : "success"}>{message.text}</AlertBox>
            </div>
          ) : null}

          <AppButton
            className="full-row"
            type="submit"
            disabled={creating || loadingCampaigns || loadingEtlRuns || !form.campaign_name || !hasLoadedEtlData}
          >
            {creating ? "Queuing..." : "Generate or refresh KPIs"}
          </AppButton>
        </form>
      </SurfaceCard>

      <SurfaceCard title={labels.latestSectionTitle}>
        {!latestExecution ? (
          <p>No execution yet.</p>
        ) : (
          <div className="table-wrap kpi-table-wrap">
            <table>
              <tbody>
                <tr>
                  <th>Execution ID</th>
                  <td>{latestExecution.id}</td>
                </tr>
                <tr>
                  <th>Status</th>
                  <td>{latestExecution.status}</td>
                </tr>
                <tr>
                  <th>Campaign</th>
                  <td>{latestExecution.campaign_name || latestExecution.campaign_id || "-"}</td>
                </tr>
                <tr>
                  <th>Campaign ID</th>
                  <td>{latestExecution.campaign_id || "-"}</td>
                </tr>
                <tr>
                  <th>Created</th>
                  <td>{new Date(latestExecution.created_at).toLocaleString()}</td>
                </tr>
              </tbody>
            </table>

            {payloadRows.length > 0 ? (
              <div className="table-wrap kpi-table-wrap" style={{ marginTop: 12 }}>
                <DataTable
                  rows={payloadRows}
                  columns={["Metric", "Value"]}
                  getRowKey={(row) => row.key}
                  renderRow={(row) => (
                    <>
                      <td>{row.key}</td>
                      <td>{row.value}</td>
                    </>
                  )}
                />
              </div>
            ) : null}

            {latestExecution?.error_message ? (
              <AlertBox type="error" style={{ marginTop: 12 }}>
                {latestExecution.error_message}
              </AlertBox>
            ) : null}
          </div>
        )}
      </SurfaceCard>

      <SurfaceCard title={labels.historySectionTitle}>
        <div className="table-wrap kpi-table-wrap">
          <DataTable
            loading={loadingHistory}
            rows={history}
            loadingMessage="Loading..."
            emptyMessage="No KPI executions yet."
            columns={["ID", "Status", "Campaign", "Created"]}
            getRowKey={(row) => row.id}
            getRowProps={(row) => ({ onClick: () => setLatestExecution(row), style: { cursor: "pointer" } })}
            renderRow={(row) => (
              <>
                <td>{row.id}</td>
                <td>{row.status}</td>
                <td>{row.campaign_name || row.campaign_id || "-"}</td>
                <td>{new Date(row.created_at).toLocaleString()}</td>
              </>
            )}
          />
        </div>
      </SurfaceCard>
    </section>
  );
}
