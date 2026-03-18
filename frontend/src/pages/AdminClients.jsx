import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import FormInput from "../components/ui/FormInput";
import AlertBox from "../components/ui/AlertBox";
import AppButton from "../components/ui/AppButton";
import DataTable from "../components/ui/DataTable";
import PageHeader from "../components/ui/PageHeader";
import SurfaceCard from "../components/ui/SurfaceCard";
import TableActions from "../components/ui/TableActions";
import { CLIENT_MODULE_OPTIONS, getClientModuleLabel, normalizeEnabledModules } from "../constants/clientModules";
import { logoutUser } from "../services/authService";
import { createClient, deleteClient, getClients, updateClient } from "../services/clientService";

const initialForm = {
  username: "",
  email: "",
  password: "",
  leacall_tenancy_url: "",
  leacall_bi_api_key: "",
  enabled_modules: ["dashboard"],
};

const initialEditForm = {
  username: "",
  email: "",
  leacall_tenancy_url: "",
  leacall_bi_api_key: "",
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
      leacall_bi_api_key: client.leacall_bi_api_key || "",
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
      <PageHeader eyebrow="Admin Module" title="Create and manage clients" />

      <SurfaceCard title="Create client">
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
          <FormInput
            label="BI API Key"
            name="leacall_bi_api_key"
            value={form.leacall_bi_api_key}
            onChange={onCreateChange}
            placeholder="BI API key (X-BI-API-Key)"
            required={false}
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

          {formError ? (
            <AlertBox className="full-row" type="error">
              {formError}
            </AlertBox>
          ) : null}
          {formSuccess ? (
            <AlertBox className="full-row" type="success">
              {formSuccess}
            </AlertBox>
          ) : null}

          <AppButton className="full-row" type="submit" disabled={saving}>
            {saving ? "Creation..." : "Creer client"}
          </AppButton>
        </form>
      </SurfaceCard>

      <SurfaceCard title="Clients">
        {tableError ? <AlertBox type="error">{tableError}</AlertBox> : null}
        {tableSuccess ? <AlertBox type="success">{tableSuccess}</AlertBox> : null}

        {loadingList ? (
          <p>Chargement...</p>
        ) : clients.length === 0 ? (
          <p>Aucun client pour le moment.</p>
        ) : (
          <div className="table-wrap">
            <DataTable
              rows={clients}
              columns={["ID", "Username", "Email", "URL", "Modules", "Actif", "Actions"]}
              getRowKey={(client) => client.id}
              renderRow={(client) => (
                <>
                  <td>{client.id}</td>
                  <td>{client.username}</td>
                  <td>{client.email}</td>
                  <td>{client.leacall_tenancy_url || "-"}</td>
                  <td>{normalizeEnabledModules(client.enabled_modules).map(getClientModuleLabel).join(", ")}</td>
                  <td>{client.is_active ? "Oui" : "Non"}</td>
                  <td>
                    <TableActions>
                      <AppButton variant="secondary" compact type="button" onClick={() => startEditing(client)}>
                        Update
                      </AppButton>
                      <AppButton
                        variant="danger"
                        compact
                        type="button"
                        disabled={deletingClientId === client.id}
                        onClick={() => onDeleteClient(client)}
                      >
                        {deletingClientId === client.id ? "Deleting..." : "Delete"}
                      </AppButton>
                    </TableActions>
                  </td>
                </>
              )}
            />
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
            <FormInput
              label="BI API Key"
              name="leacall_bi_api_key"
              value={editForm.leacall_bi_api_key}
              onChange={onEditChange}
              placeholder="BI API key (X-BI-API-Key)"
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
              <AppButton type="submit" disabled={updating}>
                {updating ? "Updating..." : "Update client"}
              </AppButton>
              <AppButton variant="secondary" compact type="button" onClick={cancelEditing}>
                Cancel
              </AppButton>
            </div>
          </form>
        ) : null}
      </SurfaceCard>
    </section>
  );
}
