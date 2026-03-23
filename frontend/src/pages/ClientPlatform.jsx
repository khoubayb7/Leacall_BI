import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { getClientPlatformData } from "../services/platformService";

export default function ClientPlatform() {
  const navigate = useNavigate();
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [clientKPIs, setClientKPIs] = useState({
    campaign_performance: {
      total_calls_made: 0,
      calls_connected: 0,
      call_success_rate: 0,
      leads_converted: 0,
      conversion_rate: 0,
      avg_call_duration_seconds: 0,
      cost_per_lead: 0,
      campaign_roi: 0,
    },
    lead_quality: {
      lead_status_distribution: {},
      response_rate_by_time: {},
      peak_calling_hours: [],
      peak_calling_days: [],
    },
    conversation_intelligence: {
      sentiment_trends: {},
      common_objections: [],
      talk_to_listen_ratio: 0,
      key_topics_mentioned: {},
    },
    operational_efficiency: {
      calls_per_day: 0,
      calls_per_week: 0,
      calls_per_month: 0,
      peak_hours_heatmap: {},
      calls_completed_on_time: 0,
      average_wait_time_seconds: 0,
    },
  });

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError("");

      try {
        const data = await getClientPlatformData();
        setClientData(data);

        // Simulate KPI data - would come from API in production
        setClientKPIs((prev) => ({
          ...prev,
          campaign_performance: {
            total_calls_made: Math.floor(Math.random() * 1000) + 100,
            calls_connected: Math.floor(Math.random() * 800) + 50,
            call_success_rate: (Math.random() * 0.4 + 0.5).toFixed(4),
            leads_converted: Math.floor(Math.random() * 150) + 10,
            conversion_rate: (Math.random() * 0.2 + 0.08).toFixed(4),
            avg_call_duration_seconds: Math.floor(Math.random() * 600) + 300,
            cost_per_lead: (Math.random() * 20 + 5).toFixed(2),
            campaign_roi: (Math.random() * 3 + 1.5).toFixed(2),
          },
          lead_quality: {
            lead_status_distribution: {
              not_contacted: Math.floor(Math.random() * 200),
              contacted: Math.floor(Math.random() * 300),
              interested: Math.floor(Math.random() * 150),
              converted: Math.floor(Math.random() * 100),
              rejected: Math.floor(Math.random() * 50),
            },
            response_rate_by_time: {
              "09_AM": (Math.random() * 0.3).toFixed(2),
              "10_AM": (Math.random() * 0.3).toFixed(2),
              "14_PM": (Math.random() * 0.2).toFixed(2),
              "16_PM": (Math.random() * 0.25).toFixed(2),
            },
            peak_calling_hours: [9, 10, 11, 14],
            peak_calling_days: ["Monday", "Tuesday", "Wednesday"],
          },
          conversation_intelligence: {
            sentiment_trends: {
              week_1: { positive: 45, neutral: 120, negative: 15 },
              week_2: { positive: 52, neutral: 110, negative: 18 },
              week_3: { positive: 48, neutral: 125, negative: 12 },
              week_4: { positive: 55, neutral: 105, negative: 10 },
            },
            common_objections: [
              { objection: "Too expensive", count: 34, resolution_rate: 0.24 },
              { objection: "Not interested now", count: 28, resolution_rate: 0.32 },
              { objection: "Already have solution", count: 22, resolution_rate: 0.18 },
            ],
            talk_to_listen_ratio: 0.45,
            key_topics_mentioned: {
              product_features: 234,
              pricing: 189,
              implementation: 78,
              support: 92,
            },
          },
          operational_efficiency: {
            calls_per_day: (Math.random() * 100 + 50).toFixed(2),
            calls_per_week: (Math.random() * 700 + 350).toFixed(2),
            calls_per_month: (Math.random() * 3000 + 1500).toFixed(2),
            peak_hours_heatmap: {
              "09": 120,
              "10": 145,
              "11": 135,
              "14": 110,
              "15": 130,
            },
            calls_completed_on_time: 0.95,
            average_wait_time_seconds: (Math.random() * 60 + 30).toFixed(1),
          },
        }));
      } catch (err) {
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setError("Impossible de charger votre espace client.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [navigate]);

  return (
    <section className="workspace-content">
      <header className="content-header">
        <div>
          <p className="eyebrow">Client Area</p>
          <h1>Campaign Dashboard</h1>
        </div>
      </header>

      {error ? <div className="error-box">{error}</div> : null}

      {/* Campaign Performance KPIs */}
      <div className="kpi-section">
        <h2>Campaign Performance</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Total Calls Made</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.campaign_performance.total_calls_made}</strong>
            <span className="card-desc">All calls</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Connected Calls</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.campaign_performance.calls_connected}</strong>
            <span className="card-desc">Successful connections</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Success Rate</p>
            <strong className="card-value">{loading ? "..." : (clientKPIs.campaign_performance.call_success_rate * 100).toFixed(1)}%</strong>
            <span className="card-desc">Connected / Attempted</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Leads Converted</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.campaign_performance.leads_converted}</strong>
            <span className="card-desc">Qualified leads</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Conversion Rate</p>
            <strong className="card-value">{loading ? "..." : (clientKPIs.campaign_performance.conversion_rate * 100).toFixed(2)}%</strong>
            <span className="card-desc">Leads / Calls</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Avg Call Duration</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.campaign_performance.avg_call_duration_seconds}s</strong>
            <span className="card-desc">Average length</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Cost per Lead</p>
            <strong className="card-value">${loading ? "..." : clientKPIs.campaign_performance.cost_per_lead}</strong>
            <span className="card-desc">Cost efficiency</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Campaign ROI</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.campaign_performance.campaign_roi}x</strong>
            <span className="card-desc">Return on investment</span>
          </article>
        </div>
      </div>

      {/* Lead Quality KPIs */}
      <div className="kpi-section">
        <h2>Lead Quality & Segmentation</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Peak Calling Hours</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.lead_quality.peak_calling_hours.join(", ")}</strong>
            <span className="card-desc">Best performing hours</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Peak Days</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.lead_quality.peak_calling_days.slice(0, 2).join(", ")}</strong>
            <span className="card-desc">Most active days</span>
          </article>
        </div>
        {!loading && Object.keys(clientKPIs.lead_quality.lead_status_distribution).length > 0 && (
          <div className="surface-card">
            <h3>Lead Status Distribution</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(clientKPIs.lead_quality.lead_status_distribution).map(([status, count]) => (
                    <tr key={status}>
                      <td className="capitalize">{status.replace(/_/g, " ")}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Conversation Intelligence KPIs */}
      <div className="kpi-section">
        <h2>Conversation Intelligence</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Talk-to-Listen Ratio</p>
            <strong className="card-value">{loading ? "..." : (clientKPIs.conversation_intelligence.talk_to_listen_ratio * 100).toFixed(0)}%</strong>
            <span className="card-desc">Agent speaking time</span>
          </article>
        </div>
        {!loading && clientKPIs.conversation_intelligence.common_objections.length > 0 && (
          <div className="surface-card">
            <h3>Common Objections</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Objection</th>
                    <th>Count</th>
                    <th>Resolution Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {clientKPIs.conversation_intelligence.common_objections.map((obj, idx) => (
                    <tr key={idx}>
                      <td>{obj.objection}</td>
                      <td>{obj.count}</td>
                      <td>{(obj.resolution_rate * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {!loading && Object.keys(clientKPIs.conversation_intelligence.key_topics_mentioned).length > 0 && (
          <div className="surface-card">
            <h3>Key Topics Mentioned</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Topic</th>
                    <th>Mentions</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(clientKPIs.conversation_intelligence.key_topics_mentioned).map(([topic, count]) => (
                    <tr key={topic}>
                      <td className="capitalize">{topic.replace(/_/g, " ")}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Operational Efficiency KPIs */}
      <div className="kpi-section">
        <h2>Operational Efficiency</h2>
        <div className="stats-grid">
          <article className="stats-card">
            <p className="card-label">Calls per Day</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.operational_efficiency.calls_per_day}</strong>
            <span className="card-desc">Daily average</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Calls per Week</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.operational_efficiency.calls_per_week}</strong>
            <span className="card-desc">Weekly total</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Calls per Month</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.operational_efficiency.calls_per_month}</strong>
            <span className="card-desc">Monthly projection</span>
          </article>
          <article className="stats-card">
            <p className="card-label">SLA Compliance</p>
            <strong className="card-value">{loading ? "..." : (clientKPIs.operational_efficiency.calls_completed_on_time * 100).toFixed(0)}%</strong>
            <span className="card-desc">On-time completion</span>
          </article>
          <article className="stats-card">
            <p className="card-label">Avg Wait Time</p>
            <strong className="card-value">{loading ? "..." : clientKPIs.operational_efficiency.average_wait_time_seconds}s</strong>
            <span className="card-desc">Average queue wait</span>
          </article>
        </div>
      </div>

      {/* User Profile */}
      <article className="surface-card">
        <h2>Your Profile</h2>
        <div className="table-wrap">
          <table>
            <tbody>
              <tr>
                <th>Username</th>
                <td>{loading ? "..." : clientData?.username || "-"}</td>
              </tr>
              <tr>
                <th>Email</th>
                <td>{loading ? "..." : clientData?.email || "-"}</td>
              </tr>
              <tr>
                <th>Status</th>
                <td>{loading ? "..." : (clientData?.is_active ? "Active" : "Inactive")}</td>
              </tr>
              <tr>
                <th>Role</th>
                <td>{loading ? "..." : clientData?.role || "-"}</td>
              </tr>
              <tr>
                <th>LeaCall Tenancy URL</th>
                <td>{loading ? "..." : clientData?.leacall_tenancy_url || "-"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
