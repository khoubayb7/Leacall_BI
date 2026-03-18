import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import AlertBox from "../components/ui/AlertBox";
import AppButton from "../components/ui/AppButton";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import SurfaceCard from "../components/ui/SurfaceCard";
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
      <PageHeader
        eyebrow="Admin Area"
        title="Dashboard overview"
        action={(
          <AppButton variant="secondary" compact onClick={() => navigate("/admin/create-client")} type="button">
            Create Client
          </AppButton>
        )}
      />

      {error ? <AlertBox type="error">{error}</AlertBox> : null}

      <div className="stats-grid">
        <StatCard label="Total clients" value={loading ? "..." : stats.total} />
        <StatCard label="Active clients" value={loading ? "..." : stats.active} />
        <StatCard label="Inactive clients" value={loading ? "..." : stats.inactive} />
      </div>

      <SurfaceCard title="Quick actions">
        <p>Use the left sidebar to move between admin modules. `Create Clients` opens the full creation form.</p>
      </SurfaceCard>
    </section>
  );
}
