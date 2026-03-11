import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { getDataSources, getETLRuns, triggerSync } from "../services/etlService";

// ── Helpers ───────────────────────────────────────────────────────────────────

function StatusBadge({ value }) {
  const map = {
    success: { label: "Success", color: "var(--success)" },
    running: { label: "Running", color: "var(--accent)" },
    pending: { label: "Pending", color: "#f0c040" },
    failed:  { label: "Failed",  color: "var(--danger)" },
  };
  const s = map[value] || { label: value, color: "var(--text-soft)" };
  return (
    <span style={{ color: s.color, fontWeight: 700 }}>{s.label}</span>
  );
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ETLPipeline() {
  const navigate = useNavigate();

  const [sources, setSources]       = useState([]);
  const [runs, setRuns]             = useState([]);
  const [loadingSources, setLoadingSources] = useState(true);
  const [loadingRuns, setLoadingRuns]       = useState(true);
  const [syncingId, setSyncingId]   = useState(null);   // which source is syncing
  const [syncMsg, setSyncMsg]       = useState({ type: "", text: "" });
  const [pageError, setPageError]   = useState("");

  // ── Load data sources ──────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoadingSources(true);
      try {
        setSources(await getDataSources());
      } catch (err) {
        const s = err?.response?.status;
        if (s === 401 || s === 403) { await logoutUser(); navigate("/login", { replace: true }); return; }
        setPageError("Could not load data sources.");
      } finally {
        setLoadingSources(false);
      }
    };
    load();
  }, [navigate]);

  // ── Load recent runs ───────────────────────────────────────────────────────
  const loadRuns = async () => {
    setLoadingRuns(true);
    try {
      setRuns(await getETLRuns());
    } catch {
      // non-critical — page still usable
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => { loadRuns(); }, []);

  // ── Trigger sync ───────────────────────────────────────────────────────────
  const handleSync = async (sourceId, sourceName) => {
    setSyncingId(sourceId);
    setSyncMsg({ type: "", text: "" });
    try {
      const run = await triggerSync(sourceId);
      setSyncMsg({
        type: "success",
        text: `Sync for "${sourceName}" completed — Run #${run?.run_id ?? "?"} (${run?.status ?? "done"}).`,
      });
      await loadRuns();          // refresh run history
    } catch (err) {
      const detail = err?.response?.data?.detail || "Sync failed. Check the server logs.";
      setSyncMsg({ type: "error", text: detail });
    } finally {
      setSyncingId(null);
    }
  };

  // ── Stats derived from runs ────────────────────────────────────────────────
  const totalRuns   = runs.length;
  const successRuns = runs.filter((r) => r.status === "success").length;
  const failedRuns  = runs.filter((r) => r.status === "failed").length;

  return (
    <section className="workspace-content">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className="content-header">
        <div>
          <p className="eyebrow">ETL Pipeline</p>
          <h1>Data synchronisation</h1>
        </div>
        <button
          className="secondary-btn compact"
          type="button"
          onClick={loadRuns}
          disabled={loadingRuns}
        >
          {loadingRuns ? "Refreshing…" : "Refresh runs"}
        </button>
      </header>

      {pageError && <div className="error-box">{pageError}</div>}
      {syncMsg.text && (
        <div className={syncMsg.type === "error" ? "error-box" : "success-box"}>
          {syncMsg.text}
        </div>
      )}

      {/* ── Stats row ───────────────────────────────────────────────────── */}
      <div className="stats-grid">
        <article className="stats-card">
          <p>Data sources</p>
          <strong>{loadingSources ? "…" : sources.length}</strong>
        </article>
        <article className="stats-card">
          <p>Successful runs</p>
          <strong style={{ color: "var(--success)" }}>{loadingRuns ? "…" : successRuns}</strong>
        </article>
        <article className="stats-card">
          <p>Failed runs</p>
          <strong style={{ color: failedRuns ? "var(--danger)" : "inherit" }}>
            {loadingRuns ? "…" : failedRuns}
          </strong>
        </article>
      </div>

      {/* ── Data sources table ───────────────────────────────────────────── */}
      <article className="surface-card">
        <h2>Data sources — LeaCall campaigns</h2>
        <div className="table-wrap">
          {loadingSources ? (
            <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>Loading sources…</p>
          ) : sources.length === 0 ? (
            <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>
              No data sources configured yet. Ask an admin to add a LeaCall campaign.
            </p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Type</th>
                  <th>Client</th>
                  <th>Last synced</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {sources.map((src) => (
                  <tr key={src.id}>
                    <td>
                      <strong>{src.campaign_name || src.campaign_id}</strong>
                      <br />
                      <span style={{ fontSize: "0.8rem", color: "var(--text-soft)" }}>
                        {src.campaign_id}
                      </span>
                    </td>
                    <td>{src.campaign_type}</td>
                    <td>{src.client_username ?? src.client ?? "—"}</td>
                    <td style={{ fontSize: "0.85rem", color: "var(--text-soft)" }}>
                      {formatDate(src.last_synced_at)}
                    </td>
                    <td>
                      <span style={{ color: src.is_active ? "var(--success)" : "var(--text-soft)" }}>
                        {src.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="primary-btn"
                          style={{ width: "auto", padding: "7px 14px", fontSize: "0.84rem" }}
                          type="button"
                          disabled={syncingId === src.id || !src.is_active}
                          onClick={() => handleSync(src.id, src.campaign_name || src.campaign_id)}
                        >
                          {syncingId === src.id ? "Syncing…" : "▶ Run ETL"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </article>

      {/* ── Recent runs table ───────────────────────────────────────────── */}
      <article className="surface-card">
        <h2>Recent ETL runs</h2>
        <div className="table-wrap">
          {loadingRuns ? (
            <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>Loading runs…</p>
          ) : runs.length === 0 ? (
            <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>No runs yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Campaign</th>
                  <th>Status</th>
                  <th>Extracted</th>
                  <th>Transformed</th>
                  <th>Loaded</th>
                  <th>Started</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => {
                  const started = run.started_at ? new Date(run.started_at) : null;
                  const completed = run.completed_at ? new Date(run.completed_at) : null;
                  const durationSec = started && completed
                    ? ((completed - started) / 1000).toFixed(1)
                    : null;

                  return (
                    <tr key={run.id}>
                      <td style={{ color: "var(--text-soft)" }}>#{run.id}</td>
                      <td>{run.data_source_name ?? run.data_source ?? "—"}</td>
                      <td><StatusBadge value={run.status} /></td>
                      <td>{run.raw_count ?? "—"}</td>
                      <td>{run.transformed_count ?? "—"}</td>
                      <td>{run.loaded_count ?? "—"}</td>
                      <td style={{ fontSize: "0.82rem", color: "var(--text-soft)" }}>
                        {formatDate(run.started_at)}
                      </td>
                      <td style={{ fontSize: "0.82rem", color: "var(--text-soft)" }}>
                        {durationSec != null ? `${durationSec}s` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </article>

    </section>
  );
}
