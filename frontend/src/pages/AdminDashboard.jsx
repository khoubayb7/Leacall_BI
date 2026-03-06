import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { getClients } from "../services/clientService";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0 });

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
          <h1>Dashboard overview</h1>
        </div>
        <button className="secondary-btn compact" onClick={() => navigate("/admin/create-client")} type="button">
          Create Client
        </button>
      </header>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="stats-grid">
        <article className="stats-card">
          <p>Total clients</p>
          <strong>{loading ? "..." : stats.total}</strong>
        </article>
        <article className="stats-card">
          <p>Active clients</p>
          <strong>{loading ? "..." : stats.active}</strong>
        </article>
        <article className="stats-card">
          <p>Inactive clients</p>
          <strong>{loading ? "..." : stats.inactive}</strong>
        </article>
      </div>

      <article className="surface-card">
        <h2>Quick actions</h2>
        <p>Use the left sidebar to move between admin modules. `Create Clients` opens the full creation form.</p>
      </article>
    </section>
  );
}
