import { useState } from "react";
import FormInput from "../components/ui/FormInput";
import { loginUser } from "../services/authService";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
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
      console.log("Login success:", data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Email ou mot de passe invalide.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Connexion</h1>
        <p>Entrez vos identifiants pour continuer.</p>

        <FormInput
          label="Email"
          type="email"
          name="email"
          value={form.email}
          onChange={onChange}
          placeholder="you@email.com"
        />

        <FormInput
          label="Mot de passe"
          type="password"
          name="password"
          value={form.password}
          onChange={onChange}
          placeholder="••••••••"
        />

        {error ? <div className="error-box">{error}</div> : null}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </main>
  );
}
