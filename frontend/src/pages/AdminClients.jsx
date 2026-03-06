import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import FormInput from "../components/ui/FormInput";
import { logoutUser } from "../services/authService";
import { createClient, getClients } from "../services/clientService";

const initialForm = {
  username: "",
  email: "",
  password: "",
  leacall_tenancy_url: "",
};

export default function AdminClients() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [clients, setClients] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const loadClients = async () => {
      setLoadingList(true);
      setError("");

      try {
        const data = await getClients();
        setClients(data);
      } catch (err) {
        const status = err?.response?.status;
        if (status === 401 || status === 403) {
          await logoutUser();
          navigate("/login", { replace: true });
          return;
        }
        setError("Impossible de charger les clients.");
      } finally {
        setLoadingList(false);
      }
    };

    loadClients();
  }, [navigate]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const created = await createClient(form);
      setClients((prev) => [created, ...prev]);
      setForm(initialForm);
      setSuccess(`Client ${created.username} created successfully.`);
    } catch (err) {
      const apiError = err?.response?.data;
      const firstFieldError = apiError && typeof apiError === "object" ? Object.values(apiError)?.[0]?.[0] : null;
      setError(firstFieldError || "Echec de creation du client.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="workspace-content">
      <header className="content-header">
        <div>
          <p className="eyebrow">Admin Module</p>
          <h1>Create client</h1>
        </div>
      </header>

      <article className="surface-card">
        <form className="grid-form" onSubmit={onSubmit}>
          <FormInput label="Username" name="username" value={form.username} onChange={onChange} placeholder="client1" />
          <FormInput label="Email" type="email" name="email" value={form.email} onChange={onChange} placeholder="client@mail.com" />
          <FormInput label="Password" type="password" name="password" value={form.password} onChange={onChange} placeholder="******" />
          <FormInput
            label="Leacall URL"
            type="url"
            name="leacall_tenancy_url"
            value={form.leacall_tenancy_url}
            onChange={onChange}
            placeholder="https://tenant.leacall.com"
          />

          {error ? <div className="error-box full-row">{error}</div> : null}
          {success ? <div className="success-box full-row">{success}</div> : null}

          <button className="primary-btn full-row" type="submit" disabled={saving}>
            {saving ? "Creation..." : "Creer client"}
          </button>
        </form>
      </article>

      <article className="surface-card">
        <h2>Recent clients</h2>
        {loadingList ? (
          <p>Chargement...</p>
        ) : clients.length === 0 ? (
          <p>Aucun client pour le moment.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>URL</th>
                  <th>Actif</th>
                </tr>
              </thead>
              <tbody>
                {clients.slice(0, 7).map((client) => (
                  <tr key={client.id}>
                    <td>{client.id}</td>
                    <td>{client.username}</td>
                    <td>{client.email}</td>
                    <td>{client.leacall_tenancy_url || "-"}</td>
                    <td>{client.is_active ? "Oui" : "Non"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
