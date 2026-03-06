import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logoutUser } from "../services/authService";
import { getClientPlatformData } from "../services/platformService";

export default function ClientPlatform() {
  const navigate = useNavigate();
  const [clientData, setClientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError("");

      try {
        const data = await getClientPlatformData();
        setClientData(data);
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
          <h1>Client dashboard</h1>
        </div>
      </header>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="stats-grid">
        <article className="stats-card">
          <p>Username</p>
          <strong>{loading ? "..." : clientData?.username || "-"}</strong>
        </article>
        <article className="stats-card">
          <p>Status</p>
          <strong>{loading ? "..." : clientData?.is_active ? "Active" : "Inactive"}</strong>
        </article>
        <article className="stats-card">
          <p>Role</p>
          <strong>{loading ? "..." : clientData?.role || "-"}</strong>
        </article>
      </div>

      <article className="surface-card">
        <h2>Platform details</h2>
        <div className="table-wrap">
          <table>
            <tbody>
              <tr>
                <th>Email</th>
                <td>{loading ? "..." : clientData?.email || "-"}</td>
              </tr>
              <tr>
                <th>Leacall URL</th>
                <td>{loading ? "..." : clientData?.leacall_tenancy_url || "-"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
