import { useState, useEffect } from "react";

export default function LeacallBiLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setTimeout(() => setVisible(true), 100);
  }, []);

  const handleSubmit = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet" />
      <style>{`
        body { background:#0d1117; font-family:'DM Sans',sans-serif; margin:0; }

        .bg-grid {
          position:fixed; inset:0; z-index:0; pointer-events:none;
          background-image: linear-gradient(rgba(0,229,195,0.03) 1px,transparent 1px), linear-gradient(90deg,rgba(0,229,195,0.03) 1px,transparent 1px);
          background-size:44px 44px; animation:gridMove 25s linear infinite;
        }
        .orb { position:fixed; border-radius:50%; filter:blur(70px); z-index:0; pointer-events:none; }
        .orb-1 { width:450px;height:450px;top:-180px;left:-180px;background:radial-gradient(circle,rgba(0,229,195,0.09),transparent 70%); }
        .orb-2 { width:350px;height:350px;bottom:-120px;right:-120px;background:radial-gradient(circle,rgba(0,184,154,0.07),transparent 70%); }

        .login-card {
          background:#131c26; border:1px solid #1e3045; border-radius:20px;
          box-shadow:0 30px 80px rgba(0,0,0,0.5),0 0 0 1px rgba(0,229,195,0.05);
          opacity:0; transform:translateY(24px) scale(0.97);
          transition:opacity 0.8s cubic-bezier(0.16,1,0.3,1),transform 0.8s cubic-bezier(0.16,1,0.3,1);
          position:relative; overflow:hidden;
        }
        .login-card.visible { opacity:1; transform:translateY(0) scale(1); }
        .login-card::before {
          content:''; position:absolute; top:0; left:0; right:0; height:2px;
          background:linear-gradient(90deg,transparent,#00e5c3,transparent);
          background-size:200% 100%; animation:shimmer 3s linear infinite; opacity:0.7;
        }

        .logo-icon {
          width:42px;height:42px;border-radius:10px;
          background:linear-gradient(135deg,#00e5c3,#00b89a);
          display:flex;align-items:center;justify-content:center;
          font-family:'Syne',sans-serif;font-weight:800;font-size:20px;color:#0d1117;
          box-shadow:0 0 20px rgba(0,229,195,0.3);
        }
        .logo-text {
          font-family:'Syne',sans-serif;font-weight:800;font-size:22px;
          background:linear-gradient(90deg,#e8f4f1,#00e5c3);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        }

        .lbl { font-size:11px;font-weight:500;color:#4a6a7a;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:7px;display:block; }
        .icon-wrap { position:relative; }
        .ico { position:absolute;left:13px;top:50%;transform:translateY(-50%);font-size:14px;color:#4a6a7a;pointer-events:none;transition:color 0.3s; }

        .c-input {
          background:#162030!important; border:1px solid #1e3045!important; border-radius:10px!important;
          color:#e8f4f1!important; font-family:'DM Sans',sans-serif!important; font-size:14px!important;
          padding:11px 14px 11px 38px!important;
          transition:border-color 0.3s,box-shadow 0.3s!important;
        }
        .c-input::placeholder { color:#4a6a7a!important; }
        .c-input:focus {
          border-color:rgba(0,229,195,0.45)!important;
          box-shadow:0 0 0 3px rgba(0,229,195,0.07)!important;
        }
        .icon-wrap:focus-within .ico { color:#00e5c3; }

        .form-check-input { background-color:#162030;border-color:#1e3045;cursor:pointer; }
        .form-check-input:checked { background-color:#00e5c3;border-color:#00e5c3;box-shadow:0 0 8px rgba(0,229,195,0.35); }
        .form-check-label { font-size:13px;color:#4a6a7a;cursor:pointer; }

        .lnk { font-size:13px;color:#00e5c3;text-decoration:none;transition:opacity 0.2s; }
        .lnk:hover { opacity:0.65;color:#00e5c3; }

        .btn-teal {
          background:linear-gradient(135deg,#00e5c3,#00b89a); border:none; color:#0d1117;
          font-family:'Syne',sans-serif;font-weight:700;font-size:15px;
          border-radius:10px;padding:12px;
          box-shadow:0 0 28px rgba(0,229,195,0.3),0 4px 16px rgba(0,0,0,0.3);
          transition:transform 0.2s,box-shadow 0.2s;
        }
        .btn-teal:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 0 40px rgba(0,229,195,0.45),0 8px 20px rgba(0,0,0,0.3);color:#0d1117; }
        .btn-teal:disabled { opacity:0.7;cursor:not-allowed;color:#0d1117; }

        .btn-sso {
          background:#162030;border:1px solid #1e3045;color:#e8f4f1;
          font-family:'DM Sans',sans-serif;font-size:14px;border-radius:10px;padding:11px;
          transition:border-color 0.3s,box-shadow 0.3s;
        }
        .btn-sso:hover { border-color:rgba(0,229,195,0.3);box-shadow:0 0 15px rgba(0,229,195,0.06);color:#e8f4f1; }

        .div-line { flex:1;height:1px;background:#1e3045; }
        .div-txt { font-size:12px;color:#4a6a7a; }
        .foot { font-size:12px;color:#4a6a7a; }

        .spin { width:15px;height:15px;border:2px solid #0d1117;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;display:inline-block; }

        @keyframes gridMove { to { background-position:44px 44px; } }
        @keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
        @keyframes spin { to { transform:rotate(360deg); } }
      `}</style>

      <div className="bg-grid" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      <div className="position-relative d-flex align-items-center justify-content-center vh-100 px-3" style={{ zIndex: 1 }}>
        <div style={{ width: "100%", maxWidth: 400 }}>
          <div className={`login-card p-4 p-md-5 ${visible ? "visible" : ""}`}>

            {/* Logo */}
            <div className="d-flex align-items-center justify-content-center gap-2 mb-4">
              <div className="logo-icon">L</div>
              <span className="logo-text">LeacallBi</span>
            </div>

            <h2 className="text-center mb-1" style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 20, color: "#e8f4f1" }}>Connexion</h2>
            <p className="text-center mb-4" style={{ fontSize: 13, color: "#4a6a7a" }}>Accédez à votre espace</p>

            {/* Email */}
            <div className="mb-3">
              <label className="lbl">Adresse e-mail</label>
              <div className="icon-wrap">
                <span className="ico">✉</span>
                <input type="email" className="form-control c-input" placeholder="vous@entreprise.com" value={email} onChange={e => setEmail(e.target.value)} />
              </div>
            </div>

            {/* Password */}
            <div className="mb-3">
              <label className="lbl">Mot de passe</label>
              <div className="icon-wrap">
                <span className="ico">🔒</span>
                <input type="password" className="form-control c-input" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
              </div>
            </div>

            {/* Remember + Forgot */}
            <div className="d-flex justify-content-between align-items-center mb-4">
              <div className="form-check mb-0">
                <input className="form-check-input" type="checkbox" id="remember" checked={remember} onChange={e => setRemember(e.target.checked)} />
                <label className="form-check-label" htmlFor="remember">Se souvenir de moi</label>
              </div>
              <a className="lnk" href="#">Mot de passe oublié ?</a>
            </div>

            {/* Submit */}
            <button className="btn btn-teal w-100 d-flex align-items-center justify-content-center gap-2 mb-3" onClick={handleSubmit} disabled={loading}>
              {loading ? <><span className="spin" /> Connexion…</> : "Se connecter →"}
            </button>

            {/* Divider */}
            <div className="d-flex align-items-center gap-2 mb-3">
              <div className="div-line" /><span className="div-txt">ou</span><div className="div-line" />
            </div>

            {/* SSO */}
            <button className="btn btn-sso w-100 d-flex align-items-center justify-content-center gap-2 mb-4">
              <span>🏢</span> Connexion SSO entreprise
            </button>

            <p className="text-center foot mb-0">
              Pas de compte ? <a className="lnk" href="#">Contacter l'équipe commerciale</a>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
