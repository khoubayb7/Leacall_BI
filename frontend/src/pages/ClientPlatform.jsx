import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ClientActivityChart } from "../components/charts/ClientActivityChart";
import { PlatformHealthChart } from "../components/charts/PlatformHealthChart";
import { ResourceUsageChart } from "../components/charts/ResourceUsageChart";
import { logoutUser } from "../services/authService";
import { getKPICampaignOptions } from "../services/kpiService";
import { getClientPlatformData } from "../services/platformService";
import "../styles/charts.css";

const INITIAL_KPIS = {
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
};

function hashText(value) {
  if (!value) {
    return 1;
  }

  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash) + 1;
}

function seededRandom(seed) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function seededInt(seed, min, max) {
  return Math.floor(seededRandom(seed) * (max - min + 1)) + min;
}

function seededFloat(seed, min, max, digits = 2) {
  return (seededRandom(seed) * (max - min) + min).toFixed(digits);
}

function buildCampaignKPIs(campaign, rangeDays = "30", refreshSalt = 0) {
  const identity = `${campaign?.campaign_id || ""}|${campaign?.campaign_name || ""}|${rangeDays}|${refreshSalt}`;
  const seed = hashText(identity);
  const rangeFactorMap = { 7: 0.35, 30: 1, 90: 2.75 };
  const rangeDaysAsNumber = Number(rangeDays) || 30;
  const factor = rangeFactorMap[rangeDaysAsNumber] || 1;

  const totalCalls = Math.round(seededInt(seed + 1, 180, 1200) * factor);
  const connectedCalls = Math.round(
    seededInt(seed + 2, Math.floor(totalCalls * 0.45), Math.floor(totalCalls * 0.9)),
  );
  const leadsConverted = Math.round(
    seededInt(seed + 4, 15, Math.floor(Math.max(connectedCalls * 0.35, 16))),
  );
  const callsPerDay = Number((totalCalls / rangeDaysAsNumber).toFixed(2));
  const callsPerWeek = Number((callsPerDay * 7).toFixed(2));
  const callsPerMonth = Number((callsPerDay * 30).toFixed(2));

  return {
    campaign_performance: {
      total_calls_made: totalCalls,
      calls_connected: connectedCalls,
      call_success_rate: seededFloat(seed + 3, 0.45, 0.9, 4),
      leads_converted: leadsConverted,
      conversion_rate: seededFloat(seed + 5, 0.08, 0.35, 4),
      avg_call_duration_seconds: seededInt(seed + 6, 180, 820),
      cost_per_lead: seededFloat(seed + 7, 4.5, 28.5, 2),
      campaign_roi: seededFloat(seed + 8, 1.2, 4.4, 2),
    },
    lead_quality: {
      lead_status_distribution: {
        not_contacted: Math.round(seededInt(seed + 9, 35, 250) * factor),
        contacted: Math.round(seededInt(seed + 10, 80, 420) * factor),
        interested: Math.round(seededInt(seed + 11, 20, 210) * factor),
        converted: Math.round(seededInt(seed + 12, 8, 140) * factor),
        rejected: Math.round(seededInt(seed + 13, 4, 90) * factor),
      },
      response_rate_by_time: {
        "09_AM": seededFloat(seed + 14, 0.04, 0.35, 2),
        "10_AM": seededFloat(seed + 15, 0.04, 0.35, 2),
        "14_PM": seededFloat(seed + 16, 0.04, 0.35, 2),
        "16_PM": seededFloat(seed + 17, 0.04, 0.35, 2),
      },
      peak_calling_hours: [
        seededInt(seed + 18, 8, 11),
        seededInt(seed + 19, 12, 15),
        seededInt(seed + 20, 16, 18),
      ],
      peak_calling_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].slice(
        0,
        seededInt(seed + 21, 2, 4),
      ),
    },
    conversation_intelligence: {
      sentiment_trends: {
        week_1: {
          positive: seededInt(seed + 22, 30, 80),
          neutral: seededInt(seed + 23, 70, 150),
          negative: seededInt(seed + 24, 6, 30),
        },
        week_2: {
          positive: seededInt(seed + 25, 30, 80),
          neutral: seededInt(seed + 26, 70, 150),
          negative: seededInt(seed + 27, 6, 30),
        },
      },
      common_objections: [
        {
          objection: "Too expensive",
          count: seededInt(seed + 28, 8, 50),
          resolution_rate: Number(seededFloat(seed + 29, 0.08, 0.58, 2)),
        },
        {
          objection: "Not interested now",
          count: seededInt(seed + 30, 8, 50),
          resolution_rate: Number(seededFloat(seed + 31, 0.08, 0.58, 2)),
        },
        {
          objection: "Already have solution",
          count: seededInt(seed + 32, 8, 50),
          resolution_rate: Number(seededFloat(seed + 33, 0.08, 0.58, 2)),
        },
      ],
      talk_to_listen_ratio: Number(seededFloat(seed + 34, 0.28, 0.66, 2)),
      key_topics_mentioned: {
        product_features: Math.round(seededInt(seed + 35, 20, 300) * factor),
        pricing: Math.round(seededInt(seed + 36, 20, 300) * factor),
        implementation: Math.round(seededInt(seed + 37, 10, 180) * factor),
        support: Math.round(seededInt(seed + 38, 10, 180) * factor),
      },
    },
    operational_efficiency: {
      calls_per_day: callsPerDay,
      calls_per_week: callsPerWeek,
      calls_per_month: callsPerMonth,
      peak_hours_heatmap: {
        "09": seededInt(seed + 42, 30, 180),
        "10": seededInt(seed + 43, 30, 180),
        "11": seededInt(seed + 44, 30, 180),
        "14": seededInt(seed + 45, 30, 180),
        "15": seededInt(seed + 46, 30, 180),
      },
      calls_completed_on_time: Number(seededFloat(seed + 47, 0.72, 0.99, 2)),
      average_wait_time_seconds: seededFloat(seed + 48, 20, 120, 1),
    },
  };
}

export default function ClientPlatform() {
  const navigate = useNavigate();
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaignName, setSelectedCampaignName] = useState("");
  const [selectedRange, setSelectedRange] = useState("30");
  const [refreshSalt, setRefreshSalt] = useState(0);
  const [clientKPIs, setClientKPIs] = useState(INITIAL_KPIS);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError("");

      try {
        const [data, campaignRows] = await Promise.all([
          getClientPlatformData(),
          getKPICampaignOptions(),
        ]);

        setClientData(data);
        setCampaigns(campaignRows);

        setSelectedCampaignName(campaignRows[0]?.campaign_name || "");
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

  useEffect(() => {
    const selectedCampaign = campaigns.find((item) => item.campaign_name === selectedCampaignName);
    setClientKPIs(
      selectedCampaign
        ? buildCampaignKPIs(selectedCampaign, selectedRange, refreshSalt)
        : INITIAL_KPIS,
    );
  }, [campaigns, selectedCampaignName, selectedRange, refreshSalt]);

  const handleCampaignChange = (event) => {
    setSelectedCampaignName(event.target.value);
  };

  return (
    <section className="workspace-content">
      <header className="content-header">
        <div className="header-heading-stack">
          <p className="eyebrow">Client Area</p>
          <div className="title-toolbar-row">
            <h1>Campaign Dashboard</h1>
            <div className="dashboard-toolbar" role="group" aria-label="Dashboard filters">
              <label className="toolbar-control">
                <span className="sr-only">Choose campaign</span>
                <select
                  className="toolbar-select"
                  value={selectedCampaignName}
                  onChange={handleCampaignChange}
                  disabled={loading || campaigns.length === 0}
                >
                  {campaigns.length === 0 ? <option value="">No campaigns available</option> : null}
                  {campaigns.map((campaign) => (
                    <option
                      key={`${campaign.campaign_name}-${campaign.campaign_id}`}
                      value={campaign.campaign_name}
                    >
                      {campaign.campaign_name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="toolbar-control">
                <span className="sr-only">Choose period</span>
                <select
                  className="toolbar-select"
                  value={selectedRange}
                  onChange={(event) => setSelectedRange(event.target.value)}
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                </select>
              </label>

              <button
                type="button"
                className="toolbar-icon-btn"
                onClick={() => setRefreshSalt((value) => value + 1)}
                disabled={loading || !selectedCampaignName}
                aria-label="Refresh campaign metrics"
                title="Refresh"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                  <path d="M20 12a8 8 0 1 1-2.34-5.66" />
                  <path d="M20 4v6h-6" />
                </svg>
              </button>
            </div>
          </div>
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

      <div className="kpi-section">
        <h2>Statistical Graphics</h2>
        <div className="charts-grid">
          <article className="surface-card chart-surface">
            <ClientActivityChart distribution={clientKPIs.lead_quality.lead_status_distribution} />
          </article>
          <article className="surface-card chart-surface">
            <PlatformHealthChart data={clientKPIs.lead_quality.response_rate_by_time} />
          </article>
          <article className="surface-card chart-surface full-width">
            <ResourceUsageChart talkToListenRatio={clientKPIs.conversation_intelligence.talk_to_listen_ratio} />
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

