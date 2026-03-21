import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AlertBox from "../../components/ui/AlertBox";
import AppButton from "../../components/ui/AppButton";
import DataTable from "../../components/ui/DataTable";
import PageHeader from "../../components/ui/PageHeader";
import StatCard from "../../components/ui/StatCard";
import SurfaceCard from "../../components/ui/SurfaceCard";
import TableActions from "../../components/ui/TableActions";
import { logoutUser } from "../../services/authService";
import { getDataSources, getETLRuns, triggerSync } from "../../services/etlService";

const DEFAULT_COPY = {
  eyebrow: "ETL Pipeline",
  title: "Data synchronisation",
  sourcesTitle: "Data sources",
  emptySourcesMessage: "No data sources configured yet.",
  showClientColumn: false,
};

function StatusBadge({ value }) {
  const map = {
    success: { label: "Success", color: "var(--success)" },
    running: { label: "Running", color: "var(--accent)" },
    pending: { label: "Pending", color: "#f0c040" },
    failed: { label: "Failed", color: "var(--danger)" },
  };

  const status = map[value] || { label: value, color: "var(--text-soft)" };
  return <span style={{ color: status.color, fontWeight: 700 }}>{status.label}</span>;
}

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString();
}

export default function ETLPipelineBase({ copy = {} }) {
  const labels = { ...DEFAULT_COPY, ...copy };
  const navigate = useNavigate();

  const [sources, setSources] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loadingSources, setLoadingSources] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [syncingId, setSyncingId] = useState(null);
  const [syncMsg, setSyncMsg] = useState({ type: "", text: "" });
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoadingSources(true);
      try {
        setSources(await getDataSources());
      } catch (err) {
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setPageError("Could not load data sources.");
      } finally {
        setLoadingSources(false);
      }
    };

    load();
  }, [navigate]);

  const loadRuns = async () => {
    setLoadingRuns(true);
    try {
      const fetchedRuns = await getETLRuns();
      setRuns(fetchedRuns);

      // Clear stale error banner once runs can be refreshed successfully.
      setSyncMsg((current) => (current.type === "error" ? { type: "", text: "" } : current));
    } catch {
      // non critical
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    const hasActiveRuns = runs.some((run) => run.status === "pending" || run.status === "running");
    if (!hasActiveRuns) return;

    const intervalId = setInterval(() => {
      loadRuns();
    }, 5000);

    return () => clearInterval(intervalId);
  }, [runs]);

  const handleSync = async (sourceId, sourceName) => {
    setSyncingId(sourceId);
    setSyncMsg({ type: "", text: "" });

    try {
      const run = await triggerSync(sourceId);
      setSyncMsg({
        type: "success",
        text: `Sync for "${sourceName}" queued - Run #${run?.run_id ?? "?"} (${run?.status ?? "pending"}).`,
      });
      await loadRuns();
    } catch (err) {
      // Reconcile with latest runs before showing a failure banner.
      try {
        const refreshedRuns = await getETLRuns();
        setRuns(refreshedRuns);
        const latestRunForSource = refreshedRuns.find((runItem) => runItem.data_source === sourceId);

        if (latestRunForSource?.status === "success") {
          setSyncMsg({
            type: "success",
            text: `Sync for "${sourceName}" completed successfully (Run #${latestRunForSource.id}).`,
          });
          return;
        }
      } catch {
        // Keep original trigger error if reconciliation fails.
      }

      const detail = err?.response?.data?.detail || "Sync failed. Check the server logs.";
      setSyncMsg({ type: "error", text: detail });
    } finally {
      setSyncingId(null);
    }
  };

  const successRuns = runs.filter((run) => run.status === "success").length;
  const failedRuns = runs.filter((run) => run.status === "failed").length;

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
            onClick={loadRuns}
            disabled={loadingRuns}
          >
            {loadingRuns ? "Refreshing..." : "Refresh runs"}
          </AppButton>
        )}
      />

      {pageError ? <AlertBox type="error">{pageError}</AlertBox> : null}
      {syncMsg.text ? (
        <AlertBox type={syncMsg.type === "error" ? "error" : "success"}>{syncMsg.text}</AlertBox>
      ) : null}

      <div className="stats-grid">
        <StatCard label="Data sources" value={loadingSources ? "..." : sources.length} />
        <StatCard
          label="Successful runs"
          value={loadingRuns ? "..." : successRuns}
          valueStyle={{ color: "var(--success)" }}
        />
        <StatCard
          label="Failed runs"
          value={loadingRuns ? "..." : failedRuns}
          valueStyle={{ color: failedRuns ? "var(--danger)" : "inherit" }}
        />
      </div>

      <SurfaceCard title={labels.sourcesTitle}>
        <div className="table-wrap">
          <DataTable
            loading={loadingSources}
            loadingMessage="Loading campaigns..."
            rows={sources}
            emptyMessage={labels.emptySourcesMessage}
            columns={[
              "Campaign",
              "Type",
              ...(labels.showClientColumn ? ["Client"] : []),
              "Last synced",
              "Status",
              "",
            ]}
            getRowKey={(src) => src.id}
            renderRow={(src) => (
              <>
                <td>
                  <strong>{src.campaign_name || src.campaign_id}</strong>
                  <br />
                  <span style={{ fontSize: "0.8rem", color: "var(--text-soft)" }}>{src.campaign_id}</span>
                </td>
                <td>{src.campaign_type}</td>
                {labels.showClientColumn ? <td>{src.client_username ?? src.client ?? "-"}</td> : null}
                <td style={{ fontSize: "0.85rem", color: "var(--text-soft)" }}>{formatDate(src.last_synced_at)}</td>
                <td>
                  <span style={{ color: src.is_active ? "var(--success)" : "var(--text-soft)" }}>
                    {src.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td>
                  <TableActions>
                    <AppButton
                      style={{ width: "auto", padding: "7px 14px", fontSize: "0.84rem" }}
                      type="button"
                      disabled={syncingId === src.id || !src.is_active}
                      onClick={() => handleSync(src.id, src.campaign_name || src.campaign_id)}
                    >
                      {syncingId === src.id ? "Syncing..." : "Run ETL"}
                    </AppButton>
                  </TableActions>
                </td>
              </>
            )}
          />
        </div>
      </SurfaceCard>

      <SurfaceCard title="Recent ETL runs">
        <div className="table-wrap">
          <DataTable
            loading={loadingRuns}
            loadingMessage="Loading runs..."
            rows={runs}
            emptyMessage="No runs yet."
            columns={["#", "Campaign", "Status", "Extracted", "Transformed", "Loaded", "Started", "Duration"]}
            getRowKey={(run) => run.id}
            renderRow={(run) => {
              const started = run.started_at ? new Date(run.started_at) : null;
              const completed = run.completed_at ? new Date(run.completed_at) : null;
              const durationSec = started && completed ? ((completed - started) / 1000).toFixed(1) : null;

              return (
                <>
                  <td style={{ color: "var(--text-soft)" }}>#{run.id}</td>
                  <td>{run.data_source_name ?? run.data_source ?? "-"}</td>
                  <td>
                    <StatusBadge value={run.status} />
                  </td>
                  <td>{run.raw_count ?? "-"}</td>
                  <td>{run.transformed_count ?? "-"}</td>
                  <td>{run.loaded_count ?? "-"}</td>
                  <td style={{ fontSize: "0.82rem", color: "var(--text-soft)" }}>{formatDate(run.started_at)}</td>
                  <td style={{ fontSize: "0.82rem", color: "var(--text-soft)" }}>
                    {durationSec != null ? `${durationSec}s` : "-"}
                  </td>
                </>
              );
            }}
          />
        </div>
      </SurfaceCard>
    </section>
  );
}
