import { useNavigate } from "react-router-dom";
import { useState } from "react";

import FormInput from "../components/ui/FormInput";
import { getDefaultRouteForRole, loginUser } from "../services/authService";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await loginUser(form);
      const role = data?.user?.role;
      navigate(getDefaultRouteForRole(role), { replace: true });
    } catch (err) {
      const apiError = err?.response?.data;
      const message = apiError?.detail || apiError?.non_field_errors?.[0] || "Identifiants invalides.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Connexion</h1>
        <p>Entrez votre username et mot de passe.</p>

        <FormInput
          label="Username"
          type="text"
          name="username"
          value={form.username}
          onChange={onChange}
          placeholder="username"
        />

        <FormInput
          label="Mot de passe"
          type="password"
          name="password"
          value={form.password}
          onChange={onChange}
          placeholder="********"
        />

        {error ? <div className="error-box">{error}</div> : null}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </main>
  );
}
