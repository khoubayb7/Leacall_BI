import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { getClients } from "../services/clientService";
import { PlatformHealthChart } from "../components/charts/PlatformHealthChart";
import { ClientActivityChart } from "../components/charts/ClientActivityChart";
import { ResourceUsageChart } from "../components/charts/ResourceUsageChart";
import "../styles/charts.css";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0 });
  const [adminKPIs, setAdminKPIs] = useState({
    platform_health: {
      total_active_clients: 0,
      total_calls_processed_global: 0,
      platform_uptime_percentage: 99.9,
      api_response_time_ms: 0,
      api_error_rate: 0,
    },
    client_activity: {
      most_active_clients: [],
      churn_rate: 0,
      avg_calls_per_client: 0,
    },
    quality_monitoring: {
      failed_call_analysis: {},
      technical_failures: 0,
      dropped_calls: 0,
    },
    resource_management: {
      infrastructure_costs_total: 0,
      cost_per_call: 0,
      compute_usage_cpu_percent: 0,
      compute_usage_memory_percent: 0,
      storage_total_gb: 0,
      storage_growth_rate_percent: 0,
    },
    anomaly_detection: {
      alerts_triggered: 0,
      unusual_call_volume_spikes: [],
      conversion_rate_drops: [],
      security_anomalies: [],
      sla_breach_warnings: [],
    },
  });

  useEffect(() => {
    const loadStats = async () => {
      setLoading(true);
      setError("");

      try {
        const clients = await getClients();
        const active = clients.filter((client) => client.is_active).length;

        setStats({
          total: clients.length,
          active,
          inactive: clients.length - active,
        });

        // Simulate KPI data - would come from API in production
        setAdminKPIs((prev) => ({
          ...prev,
          platform_health: {
            ...prev.platform_health,
            total_active_clients: active,
            total_calls_processed_global: Math.floor(Math.random() * 50000) + 10000,
          },
          client_activity: {
            ...prev.client_activity,
            most_active_clients: clients.slice(0, 3).map((c, i) => ({
              client_id: c.id,
              username: c.username,
              call_volume: Math.floor(Math.random() * 5000) + 500,
            })),
            avg_calls_per_client: Math.floor(Math.random() * 3000) + 500,
            churn_rate: (Math.random() * 10).toFixed(2),
          },
        }));
      } catch (err) {
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setError("Unable to load dashboard metrics.");
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [navigate]);

  return (
    <section className="workspace-content">
      <header className="content-header">
        <div>
          <p className="eyebrow">Admin Area</p>
          <h1>Dashboard Overview</h1>
        </div>
        <button className="secondary-btn compact" onClick={() => navigate("/admin/create-client")} type="button">
          Create Client
        </button>
      </header>

      {error ? <div className="error-box">{error}</div> : null}

      {/* Platform Health KPIs */}
      <div className="kpi-section">
        <h2>Platform Health & Usage</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Active Clients</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.platform_health.total_active_clients}</strong>
            <span className="card-desc">Currently active</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Total Calls Processed</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.platform_health.total_calls_processed_global.toLocaleString()}</strong>
            <span className="card-desc">This period</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Platform Uptime</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.platform_health.platform_uptime_percentage}%</strong>
            <span className="card-desc">SLA compliance</span>
          </article>
          <article className="stats-card">
            <p className="card-label">API Response Time</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.platform_health.api_response_time_ms.toFixed(1)}ms</strong>
            <span className="card-desc">Average latency</span>
          </article>
        </div>
        <div className="surface-card">
          {!loading && <PlatformHealthChart data={adminKPIs.platform_health} />}
        </div>
      </div>

      {/* Client Activity KPIs */}
      <div className="kpi-section">
        <h2>Client Activity Analytics</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Avg Calls/Client</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.client_activity.avg_calls_per_client}</strong>
            <span className="card-desc">Average per user</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Churn Rate</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.client_activity.churn_rate}%</strong>
            <span className="card-desc">Monthly churn</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Total Clients</p>
            <strong className="card-value">{loading ? "..." : stats.total}</strong>
            <span className="card-desc">All registered users</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Active Clients</p>
            <strong className="card-value">{loading ? "..." : stats.active}</strong>
            <span className="card-desc">Currently active</span>
          </article>
        </div>
        {!loading && adminKPIs.client_activity.most_active_clients.length > 0 && (
          <>
            <div className="surface-card">
              <ClientActivityChart clients={adminKPIs.client_activity.most_active_clients} />
            </div>
            <div className="surface-card">
              <h3>Most Active Clients</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Client</th>
                      <th>Call Volume</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminKPIs.client_activity.most_active_clients.map((client) => (
                      <tr key={client.client_id}>
                        <td>{client.username}</td>
                        <td>{client.call_volume.toLocaleString()}</td>
                        <td><span className="badge active">Active</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Quality Monitoring KPIs */}
      <div className="kpi-section">
        <h2>Quality Monitoring</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Technical Failures</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.quality_monitoring.technical_failures}</strong>
            <span className="card-desc">Network/server issues</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Dropped Calls</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.quality_monitoring.dropped_calls}</strong>
            <span className="card-desc">Disconnected calls</span>
          </article>
        </div>
      </div>

      {/* Resource Management KPIs */}
      <div className="kpi-section">
        <h2>Resource Management</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Infrastructure Cost</p>
            <strong className="card-value">${loading ? "..." : adminKPIs.resource_management.infrastructure_costs_total.toFixed(2)}</strong>
            <span className="card-desc">Total period cost</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Cost per Call</p>
            <strong className="card-value">${loading ? "..." : adminKPIs.resource_management.cost_per_call.toFixed(4)}</strong>
            <span className="card-desc">Average cost</span>
          </article>
          <article className="stats-card">
            <p className="card-label">CPU Usage</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.resource_management.compute_usage_cpu_percent.toFixed(1)}%</strong>
            <span className="card-desc">Current utilization</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Memory Usage</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.resource_management.compute_usage_memory_percent.toFixed(1)}%</strong>
            <span className="card-desc">Current utilization</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Storage Used</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.resource_management.storage_total_gb.toFixed(1)}GB</strong>
            <span className="card-desc">Total storage</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Storage Growth</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.resource_management.storage_growth_rate_percent.toFixed(1)}%</strong>
            <span className="card-desc">Month-over-month</span>
          </article>
        </div>
        {!loading && (
          <div className="surface-card">
            <ResourceUsageChart
              cpuUsage={adminKPIs.resource_management.compute_usage_cpu_percent}
              memoryUsage={adminKPIs.resource_management.compute_usage_memory_percent}
              storageUsage={35}
            />
          </div>
        )}
      </div>

      {/* Anomaly Detection KPIs */}
      <div className="kpi-section">
        <h2>Anomalies & Alerts</h2>
        <div className="stats-grid">
          <article className="stats-card alert">
            <p className="card-label">Alerts Triggered</p>
            <strong className="card-value">{loading ? "..." : adminKPIs.anomaly_detection.alerts_triggered}</strong>
            <span className="card-desc">Active alerts</span>
          </article>
        </div>
      </div>

      <article className="surface-card">
        <h2>Quick Actions</h2>
        <p>Use the left sidebar to navigate between admin modules. View client details, ETL pipelines, and KPI analytics.</p>
      </article>
    </section>
  );
}
