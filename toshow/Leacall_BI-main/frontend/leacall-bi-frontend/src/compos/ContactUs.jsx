import { useState, useEffect } from "react";

export default function ContactUs() {
  const [form, setForm] = useState({ name: "", email: "", company: "", subject: "", message: "" });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setTimeout(() => setVisible(true), 100);
  }, []);

  const update = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }));

  const handleSubmit = () => {
    if (!form.name || !form.email || !form.message) return;
    setLoading(true);
    setTimeout(() => { setLoading(false); setSent(true); }, 2000);
  };

  const isValid = form.name && form.email && form.message;

  return (
    <>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet" />
      <style>{`
        body { background:#0d1117; font-family:'DM Sans',sans-serif; margin:0; }

        .bg-grid {
          position:fixed; inset:0; z-index:0; pointer-events:none;
          background-image:linear-gradient(rgba(0,229,195,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,229,195,0.03) 1px,transparent 1px);
          background-size:44px 44px; animation:gridMove 25s linear infinite;
        }
        .orb { position:fixed; border-radius:50%; filter:blur(70px); z-index:0; pointer-events:none; }
        .orb-1 { width:450px;height:450px;top:-180px;left:-180px;background:radial-gradient(circle,rgba(0,229,195,0.09),transparent 70%); }
        .orb-2 { width:350px;height:350px;bottom:-120px;right:-120px;background:radial-gradient(circle,rgba(0,184,154,0.07),transparent 70%); }

        /* Card */
        .contact-card {
          background:#131c26; border:1px solid #1e3045; border-radius:20px;
          box-shadow:0 30px 80px rgba(0,0,0,0.5),0 0 0 1px rgba(0,229,195,0.05);
          opacity:0; transform:translateY(24px) scale(0.97);
          transition:opacity 0.8s cubic-bezier(0.16,1,0.3,1),transform 0.8s cubic-bezier(0.16,1,0.3,1);
          position:relative; overflow:hidden;
        }
        .contact-card.visible { opacity:1; transform:translateY(0) scale(1); }
        .contact-card::before {
          content:''; position:absolute; top:0; left:0; right:0; height:2px;
          background:linear-gradient(90deg,transparent,#00e5c3,transparent);
          background-size:200% 100%; animation:shimmer 3s linear infinite; opacity:0.7;
        }

        /* Info panel */
        .info-panel {
          opacity:0; transform:translateX(-30px);
          transition:opacity 0.7s ease,transform 0.7s ease;
        }
        .info-panel.visible { opacity:1; transform:translateX(0); }

        .logo-icon {
          width:38px;height:38px;border-radius:9px;
          background:linear-gradient(135deg,#00e5c3,#00b89a);
          display:flex;align-items:center;justify-content:center;
          font-family:'Syne',sans-serif;font-weight:800;font-size:18px;color:#0d1117;
          box-shadow:0 0 18px rgba(0,229,195,0.28); flex-shrink:0;
        }
        .logo-text {
          font-family:'Syne',sans-serif;font-weight:800;font-size:20px;
          background:linear-gradient(90deg,#e8f4f1,#00e5c3);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        }

        /* Info cards */
        .info-card {
          background:#162030; border:1px solid #1e3045; border-radius:14px;
          padding:14px 16px; display:flex; align-items:center; gap:12px;
          transition:border-color 0.3s,box-shadow 0.3s; cursor:default;
          opacity:0; transform:translateX(-20px);
          animation:none;
        }
        .info-card.show { animation:slideIn 0.5s ease forwards; }
        .info-card:hover { border-color:rgba(0,229,195,0.3);box-shadow:0 0 18px rgba(0,229,195,0.06); }
        .info-icon {
          width:38px;height:38px;border-radius:9px;flex-shrink:0;
          background:rgba(0,229,195,0.08);border:1px solid rgba(0,229,195,0.15);
          display:flex;align-items:center;justify-content:center;font-size:16px;
        }
        .info-label { font-size:11px;color:#4a6a7a;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px; }
        .info-value { font-size:14px;color:#e8f4f1;font-weight:500; }

        /* Form elements */
        .lbl { font-size:11px;font-weight:500;color:#4a6a7a;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:7px;display:block; }
        .icon-wrap { position:relative; }
        .ico { position:absolute;left:13px;top:50%;transform:translateY(-50%);font-size:14px;color:#4a6a7a;pointer-events:none;transition:color 0.3s; }
        .icon-wrap:focus-within .ico { color:#00e5c3; }

        .c-input, .c-select, .c-textarea {
          background:#162030!important; border:1px solid #1e3045!important; border-radius:10px!important;
          color:#e8f4f1!important; font-family:'DM Sans',sans-serif!important; font-size:14px!important;
          transition:border-color 0.3s,box-shadow 0.3s!important;
        }
        .c-input { padding:11px 14px 11px 38px!important; }
        .c-select, .c-textarea { padding:11px 14px!important; }
        .c-select { appearance:none!important; cursor:pointer!important; }
        .c-textarea { resize:vertical!important; }
        .c-input::placeholder,.c-textarea::placeholder { color:#4a6a7a!important; }
        .c-input:focus,.c-select:focus,.c-textarea:focus {
          border-color:rgba(0,229,195,0.45)!important;
          box-shadow:0 0 0 3px rgba(0,229,195,0.07)!important;
        }
        .c-select option { background:#162030; }
        .select-wrap { position:relative; }
        .select-arrow { position:absolute;right:13px;top:50%;transform:translateY(-50%);color:#4a6a7a;pointer-events:none;font-size:12px; }

        /* Buttons */
        .btn-teal {
          background:linear-gradient(135deg,#00e5c3,#00b89a); border:none; color:#0d1117;
          font-family:'Syne',sans-serif;font-weight:700;font-size:15px;
          border-radius:10px; padding:12px;
          box-shadow:0 0 28px rgba(0,229,195,0.3),0 4px 16px rgba(0,0,0,0.3);
          transition:transform 0.2s,box-shadow 0.2s;
        }
        .btn-teal:hover:not(:disabled) { transform:translateY(-1px);box-shadow:0 0 40px rgba(0,229,195,0.45),0 8px 20px rgba(0,0,0,0.3);color:#0d1117; }
        .btn-teal:disabled { opacity:0.45;cursor:not-allowed;color:#0d1117;box-shadow:none; }

        .btn-outline-reset {
          background:#162030;border:1px solid #1e3045;color:#00e5c3;
          font-family:'DM Sans',sans-serif;font-size:14px;border-radius:9px;padding:9px 22px;
          transition:border-color 0.3s;
        }
        .btn-outline-reset:hover { border-color:rgba(0,229,195,0.4);color:#00e5c3; }

        /* Status dot */
        .live-dot { width:7px;height:7px;border-radius:50%;background:#00e5c3;box-shadow:0 0 6px #00e5c3;display:inline-block;animation:blink 2s ease-in-out infinite; }

        /* Success */
        .success-icon {
          width:64px;height:64px;border-radius:50%;
          background:rgba(0,229,195,0.1);border:1px solid rgba(0,229,195,0.3);
          display:flex;align-items:center;justify-content:center;
          margin:0 auto 20px;font-size:28px;
          animation:checkPop 0.5s cubic-bezier(0.16,1,0.3,1) forwards;
        }

        .spin { width:15px;height:15px;border:2px solid #0d1117;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;display:inline-block; }

        @keyframes gridMove { to { background-position:44px 44px; } }
        @keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
        @keyframes spin { to { transform:rotate(360deg); } }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
        @keyframes checkPop { 0% { transform:scale(0);opacity:0; } 70% { transform:scale(1.2); } 100% { transform:scale(1);opacity:1; } }
        @keyframes slideIn { from { opacity:0;transform:translateX(-20px); } to { opacity:1;transform:translateX(0); } }

        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-track { background:#0d1117; }
        ::-webkit-scrollbar-thumb { background:#1e3045;border-radius:3px; }
      `}</style>

      <div className="bg-grid" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />

      <div className="position-relative py-5 px-3 d-flex align-items-center justify-content-center" style={{ zIndex: 1, minHeight: "100vh" }}>
        <div style={{ width: "100%", maxWidth: 900 }}>
          <div className="row g-4 align-items-start">

            {/* ── LEFT: Info ── */}
            <div className="col-12 col-lg-4">
              <div className={`info-panel ${visible ? "visible" : ""}`}>

                {/* Brand */}
                <div className="d-flex align-items-center gap-2 mb-4">
                  <div className="logo-icon">L</div>
                  <span className="logo-text">LeacallBi</span>
                </div>

                <h1 style={{ fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: 32, lineHeight: 1.15, letterSpacing: "-0.8px", color: "#e8f4f1", marginBottom: 12 }}>
                  Contactez-<br />
                  <span style={{ background: "linear-gradient(90deg,#00e5c3,#00c4ff)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>nous</span>
                </h1>
                <p className="mb-4" style={{ fontSize: 14, color: "#4a6a7a", lineHeight: 1.8 }}>
                  Notre équipe est disponible pour répondre à vos questions, démonstrations et demandes commerciales.
                </p>

                {/* Info cards */}
                <div className="d-flex flex-column gap-3 mb-4">
                  {[
                    { icon: "✉️", label: "Email", value: "contact@leacallbi.com", delay: "0.3s" },
                    { icon: "📞", label: "Téléphone", value: "+216 70 123 456", delay: "0.45s" },
                    { icon: "📍", label: "Adresse", value: "Tunis, Tunisie", delay: "0.6s" },
                    { icon: "🕐", label: "Disponibilité", value: "Lun–Ven, 09h–18h", delay: "0.75s" },
                  ].map(({ icon, label, value, delay }) => (
                    <div key={label} className={`info-card ${visible ? "show" : ""}`} style={{ animationDelay: delay }}>
                      <div className="info-icon">{icon}</div>
                      <div>
                        <div className="info-label">{label}</div>
                        <div className="info-value">{value}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Live indicator */}
                <div className="d-flex align-items-center gap-2" style={{ fontSize: 12, color: "#4a6a7a" }}>
                  <span className="live-dot" />
                  Temps de réponse moyen : &lt; 2h
                </div>
              </div>
            </div>

            {/* ── RIGHT: Form ── */}
            <div className="col-12 col-lg-8">
              <div className={`contact-card p-4 p-md-5 ${visible ? "visible" : ""}`}>

                {sent ? (
                  /* Success */
                  <div className="text-center py-4">
                    <div className="success-icon">✓</div>
                    <h3 style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 20, color: "#e8f4f1", marginBottom: 10 }}>
                      Message envoyé !
                    </h3>
                    <p style={{ fontSize: 14, color: "#4a6a7a", lineHeight: 1.7, marginBottom: 24 }}>
                      Merci pour votre message. Notre équipe vous répondra dans les plus brefs délais.
                    </p>
                    <button className="btn btn-outline-reset" onClick={() => { setSent(false); setForm({ name: "", email: "", company: "", subject: "", message: "" }); }}>
                      Nouveau message
                    </button>
                  </div>
                ) : (
                  <>
                    <h2 style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 18, color: "#e8f4f1", marginBottom: 6 }}>
                      Envoyez-nous un message
                    </h2>
                    <p className="mb-4" style={{ fontSize: 13, color: "#4a6a7a" }}>
                      Les champs marqués d'un * sont requis.
                    </p>

                    {/* Row 1 */}
                    <div className="row g-3 mb-0">
                      <div className="col-12 col-sm-6">
                        <label className="lbl">Nom complet *</label>
                        <div className="icon-wrap">
                          <span className="ico">👤</span>
                          <input type="text" className="form-control c-input" placeholder="Votre nom" value={form.name} onChange={update("name")} />
                        </div>
                      </div>
                      <div className="col-12 col-sm-6">
                        <label className="lbl">Email *</label>
                        <div className="icon-wrap">
                          <span className="ico">✉</span>
                          <input type="email" className="form-control c-input" placeholder="vous@email.com" value={form.email} onChange={update("email")} />
                        </div>
                      </div>
                    </div>

                    {/* Row 2 */}
                    <div className="row g-3 mt-0 mb-0">
                      <div className="col-12 col-sm-6">
                        <label className="lbl">Entreprise</label>
                        <div className="icon-wrap">
                          <span className="ico">🏢</span>
                          <input type="text" className="form-control c-input" placeholder="Votre société" value={form.company} onChange={update("company")} />
                        </div>
                      </div>
                      <div className="col-12 col-sm-6">
                        <label className="lbl">Sujet</label>
                        <div className="select-wrap">
                          <span className="select-arrow">▾</span>
                          <select className="form-select c-select" value={form.subject} onChange={update("subject")}>
                            <option value="">Choisir un sujet…</option>
                            <option value="demo">Demande de démo</option>
                            <option value="commercial">Question commerciale</option>
                            <option value="support">Support technique</option>
                            <option value="partnership">Partenariat</option>
                            <option value="other">Autre</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Message */}
                    <div className="mt-3 mb-4">
                      <label className="lbl">Message *</label>
                      <textarea className="form-control c-textarea" rows={5} placeholder="Décrivez votre besoin…" value={form.message} onChange={update("message")} />
                    </div>

                    {/* Submit */}
                    <button
                      className="btn btn-teal w-100 d-flex align-items-center justify-content-center gap-2"
                      onClick={handleSubmit}
                      disabled={!isValid || loading}
                    >
                      {loading ? <><span className="spin" /> Envoi en cours…</> : "Envoyer le message →"}
                    </button>
                  </>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </>
  );
}
