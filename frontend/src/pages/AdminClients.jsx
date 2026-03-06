import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import FormInput from "../components/ui/FormInput";
import { CLIENT_MODULE_OPTIONS, getClientModuleLabel, normalizeEnabledModules } from "../constants/clientModules";
import { logoutUser } from "../services/authService";
import { createClient, deleteClient, getClients, updateClient } from "../services/clientService";

const initialForm = {
  username: "",
  email: "",
  password: "",
  leacall_tenancy_url: "",
  enabled_modules: ["dashboard"],
};

const initialEditForm = {
  username: "",
  email: "",
  leacall_tenancy_url: "",
  is_active: true,
  enabled_modules: ["dashboard"],
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

function toggleModule(modules, moduleKey) {
  if (modules.includes(moduleKey)) {
    if (modules.length === 1) {
      return modules;
    }
    return modules.filter((module) => module !== moduleKey);
  }

  return [...modules, moduleKey];
}

export default function AdminClients() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [clients, setClients] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");

  const [editingClientId, setEditingClientId] = useState(null);
  const [editForm, setEditForm] = useState(initialEditForm);
  const [updating, setUpdating] = useState(false);
  const [deletingClientId, setDeletingClientId] = useState(null);
  const [tableError, setTableError] = useState("");
  const [tableSuccess, setTableSuccess] = useState("");

  useEffect(() => {
    const loadClients = async () => {
      setLoadingList(true);
      setTableError("");

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
        setTableError("Impossible de charger les clients.");
      } finally {
        setLoadingList(false);
      }
    };

    loadClients();
  }, [navigate]);

  const onCreateChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onCreateToggleModule = (moduleKey) => {
    setForm((prev) => ({
      ...prev,
      enabled_modules: toggleModule(prev.enabled_modules, moduleKey),
    }));
  };

  const onCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError("");
    setFormSuccess("");
    setSaving(true);

    try {
      const created = await createClient(form);
      setClients((prev) => [created, ...prev]);
      setForm(initialForm);
      setFormSuccess(`Client ${created.username} created successfully.`);
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        await logoutUser();
        navigate("/login", { replace: true });
        return;
      }

      setFormError(extractApiError(err, "Echec de creation du client."));
    } finally {
      setSaving(false);
    }
  };

  const startEditing = (client) => {
    setEditingClientId(client.id);
    setEditForm({
      username: client.username || "",
      email: client.email || "",
      leacall_tenancy_url: client.leacall_tenancy_url || "",
      is_active: Boolean(client.is_active),
      enabled_modules: normalizeEnabledModules(client.enabled_modules),
    });
    setTableError("");
    setTableSuccess("");
  };

  const cancelEditing = () => {
    setEditingClientId(null);
    setEditForm(initialEditForm);
  };

  const onEditChange = (e) => {
    const { name, value } = e.target;
    if (name === "is_active") {
      setEditForm((prev) => ({ ...prev, is_active: value === "active" }));
      return;
    }

    setEditForm((prev) => ({ ...prev, [name]: value }));
  };

  const onEditToggleModule = (moduleKey) => {
    setEditForm((prev) => ({
      ...prev,
      enabled_modules: toggleModule(prev.enabled_modules, moduleKey),
    }));
  };

  const onUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!editingClientId) return;

    setTableError("");
    setTableSuccess("");
    setUpdating(true);

    try {
      const updatedClient = await updateClient(editingClientId, editForm);
      setClients((prev) => prev.map((client) => (client.id === updatedClient.id ? updatedClient : client)));
      setTableSuccess(`Client ${updatedClient.username} updated successfully.`);
      cancelEditing();
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        await logoutUser();
        navigate("/login", { replace: true });
        return;
      }

      setTableError(extractApiError(err, "Echec de la mise a jour."));
    } finally {
      setUpdating(false);
    }
  };

  const onDeleteClient = async (client) => {
    const confirmed = window.confirm(`Delete client ${client.username}?`);
    if (!confirmed) return;

    setTableError("");
    setTableSuccess("");
    setDeletingClientId(client.id);

    try {
      await deleteClient(client.id);
      setClients((prev) => prev.filter((row) => row.id !== client.id));
      setTableSuccess(`Client ${client.username} deleted successfully.`);

      if (editingClientId === client.id) {
        cancelEditing();
      }
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        await logoutUser();
        navigate("/login", { replace: true });
        return;
      }

      setTableError(extractApiError(err, "Echec de la suppression du client."));
    } finally {
      setDeletingClientId(null);
    }
  };

  return (
    <section className="workspace-content">
      <header className="content-header">
        <div>
          <p className="eyebrow">Admin Module</p>
          <h1>Create and manage clients</h1>
        </div>
      </header>

      <article className="surface-card">
        <h2>Create client</h2>
        <form className="grid-form" onSubmit={onCreateSubmit}>
          <FormInput label="Username" name="username" value={form.username} onChange={onCreateChange} placeholder="client1" />
          <FormInput label="Email" type="email" name="email" value={form.email} onChange={onCreateChange} placeholder="client@mail.com" />
          <FormInput label="Password" type="password" name="password" value={form.password} onChange={onCreateChange} placeholder="******" />
          <FormInput
            label="Leacall URL"
            type="url"
            name="leacall_tenancy_url"
            value={form.leacall_tenancy_url}
            onChange={onCreateChange}
            placeholder="https://tenant.leacall.com"
          />

          <div className="full-row">
            <p className="module-pick-title">Enabled modules</p>
            <div className="module-pick-grid">
              {CLIENT_MODULE_OPTIONS.map((module) => (
                <label key={module.key} className="module-option">
                  <input
                    type="checkbox"
                    checked={form.enabled_modules.includes(module.key)}
                    onChange={() => onCreateToggleModule(module.key)}
                  />
                  <span>{module.label}</span>
                </label>
              ))}
            </div>
          </div>

          {formError ? <div className="error-box full-row">{formError}</div> : null}
          {formSuccess ? <div className="success-box full-row">{formSuccess}</div> : null}

          <button className="primary-btn full-row" type="submit" disabled={saving}>
            {saving ? "Creation..." : "Creer client"}
          </button>
        </form>
      </article>

      <article className="surface-card">
        <h2>Clients</h2>
        {tableError ? <div className="error-box">{tableError}</div> : null}
        {tableSuccess ? <div className="success-box">{tableSuccess}</div> : null}

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
                  <th>Modules</th>
                  <th>Actif</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client.id}>
                    <td>{client.id}</td>
                    <td>{client.username}</td>
                    <td>{client.email}</td>
                    <td>{client.leacall_tenancy_url || "-"}</td>
                    <td>{normalizeEnabledModules(client.enabled_modules).map(getClientModuleLabel).join(", ")}</td>
                    <td>{client.is_active ? "Oui" : "Non"}</td>
                    <td>
                      <div className="table-actions">
                        <button className="secondary-btn compact" type="button" onClick={() => startEditing(client)}>
                          Update
                        </button>
                        <button
                          className="danger-btn compact"
                          type="button"
                          disabled={deletingClientId === client.id}
                          onClick={() => onDeleteClient(client)}
                        >
                          {deletingClientId === client.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {editingClientId ? (
          <form className="grid-form edit-form" onSubmit={onUpdateSubmit}>
            <h3 className="full-row">Update client #{editingClientId}</h3>
            <FormInput label="Username" name="username" value={editForm.username} onChange={onEditChange} placeholder="client1" />
            <FormInput label="Email" type="email" name="email" value={editForm.email} onChange={onEditChange} placeholder="client@mail.com" />
            <FormInput
              label="Leacall URL"
              type="url"
              name="leacall_tenancy_url"
              value={editForm.leacall_tenancy_url}
              onChange={onEditChange}
              placeholder="https://tenant.leacall.com"
              required={false}
            />

            <label className="form-label">
              <span>Status</span>
              <select className="form-input" name="is_active" value={editForm.is_active ? "active" : "inactive"} onChange={onEditChange}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </label>

            <div className="full-row">
              <p className="module-pick-title">Enabled modules</p>
              <div className="module-pick-grid">
                {CLIENT_MODULE_OPTIONS.map((module) => (
                  <label key={module.key} className="module-option">
                    <input
                      type="checkbox"
                      checked={editForm.enabled_modules.includes(module.key)}
                      onChange={() => onEditToggleModule(module.key)}
                    />
                    <span>{module.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="full-row edit-form-actions">
              <button className="primary-btn" type="submit" disabled={updating}>
                {updating ? "Updating..." : "Update client"}
              </button>
              <button className="secondary-btn compact" type="button" onClick={cancelEditing}>
                Cancel
              </button>
            </div>
          </form>
        ) : null}
      </article>
    </section>
  );
}
