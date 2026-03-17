import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { generateKPI, getKPICampaignOptions, getKPIExecutionByTask, listKPIExecutions } from "../services/kpiService";

const INITIAL_FORM = {
  campaign_name: "",
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

export default function KPIDashboard() {
  const navigate = useNavigate();
  const pollRef = useRef(null);

  const [form, setForm] = useState(INITIAL_FORM);
  const [creating, setCreating] = useState(false);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [pageError, setPageError] = useState("");
  const [history, setHistory] = useState([]);
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
      <header className="content-header">
        <div>
          <p className="eyebrow">Agent KPIs</p>
          <h1>KPI dashboard</h1>
        </div>
        <button
          className="secondary-btn compact"
          type="button"
          onClick={handleGenerate}
          disabled={creating || loadingCampaigns || !form.campaign_name}
        >
          {creating ? "Refreshing..." : "Refresh KPI values"}
        </button>
      </header>

      <div className="stats-grid">
        <article className="stats-card">
          <p>Total executions</p>
          <strong>{loadingHistory ? "..." : history.length}</strong>
        </article>
        <article className="stats-card">
          <p>Success</p>
          <strong style={{ color: "var(--success)" }}>
            {loadingHistory ? "..." : history.filter((x) => x.status === "success").length}
          </strong>
        </article>
        <article className="stats-card">
          <p>Failed</p>
          <strong style={{ color: "var(--danger)" }}>
            {loadingHistory ? "..." : history.filter((x) => x.status === "failed").length}
          </strong>
        </article>
      </div>

      <article className="surface-card">
        <h2>Generate or refresh KPI</h2>
        <form className="grid-form" onSubmit={handleGenerate}>
          {pageError ? (
            <div className="full-row">
              <div className="error-box">{pageError}</div>
            </div>
          ) : null}

          <label className="form-label">
            <span>Campaign name (from datasource)</span>
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
              <div className="success-box">Campaign id used: {selectedCampaignId}</div>
            </div>
          ) : null}

          {activeTaskId ? (
            <div className="full-row">
              <div className="success-box">Task in progress: {activeTaskId}</div>
            </div>
          ) : null}

          {message.text ? (
            <div className="full-row">
              <div className={message.type === "error" ? "error-box" : "success-box"}>{message.text}</div>
            </div>
          ) : null}

          <button className="primary-btn full-row" type="submit" disabled={creating || loadingCampaigns || !form.campaign_name}>
            {creating ? "Queuing..." : "Generate or refresh KPIs"}
          </button>
        </form>
      </article>

      <article className="surface-card">
        <h2>Latest KPI output (template values)</h2>
        {!latestExecution ? (
          <p>No execution yet.</p>
        ) : (
          <div className="table-wrap">
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
          </div>
        )}

        {payloadRows.length > 0 ? (
          <div className="table-wrap" style={{ marginTop: 12 }}>
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {payloadRows.map((row) => (
                  <tr key={row.key}>
                    <td>{row.key}</td>
                    <td>{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {latestExecution?.error_message ? (
          <div className="error-box" style={{ marginTop: 12 }}>{latestExecution.error_message}</div>
        ) : null}
      </article>

      <article className="surface-card">
        <h2>Execution history (persistent)</h2>
        <div className="table-wrap">
          {loadingHistory ? (
            <p>Loading...</p>
          ) : history.length === 0 ? (
            <p>No KPI executions yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Status</th>
                  <th>Campaign</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {history.map((row) => (
                  <tr key={row.id} onClick={() => setLatestExecution(row)} style={{ cursor: "pointer" }}>
                    <td>{row.id}</td>
                    <td>{row.status}</td>
                    <td>{row.campaign_name || row.campaign_id || "-"}</td>
                    <td>{new Date(row.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </article>
    </section>
  );
}
