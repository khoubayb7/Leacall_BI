import { useState, useEffect, useRef } from "react";

const TEAL = "#00e5c3";
const BG = "#0d1117";
const PANEL = "#131c26";
const CARD = "#162030";
const BORDER = "#1e3045";
const MUTED = "#4a6a7a";

function Particles() {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);
    const resize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
    window.addEventListener("resize", resize);
    const pts = Array.from({ length: 40 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.2 + 0.3, a: Math.random() * 0.5 + 0.1,
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,229,195,${p.a})`; ctx.fill();
      });
      for (let i = 0; i < pts.length; i++)
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 120) {
            ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(0,229,195,${0.06 * (1 - d / 120)})`; ctx.lineWidth = 0.5; ctx.stroke();
          }
        }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={canvasRef} style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }} />;
}

function Input({ label, type = "text", placeholder, icon, value, onChange }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: MUTED, marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.8px" }}>
        {label}
      </label>
      <div style={{ position: "relative" }}>
        <span style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", fontSize: 14, color: focused ? TEAL : MUTED, transition: "color 0.3s", pointerEvents: "none" }}>
          {icon}
        </span>
        <input
          type={type} placeholder={placeholder} value={value} onChange={onChange}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{
            width: "100%", background: CARD, border: `1px solid ${focused ? "rgba(0,229,195,0.45)" : BORDER}`,
            borderRadius: 10, color: "#e8f4f1", fontFamily: "'DM Sans', sans-serif", fontSize: 14,
            padding: "11px 14px 11px 40px", outline: "none",
            boxShadow: focused ? "0 0 0 3px rgba(0,229,195,0.07)" : "none",
            transition: "border-color 0.3s, box-shadow 0.3s",
          }}
        />
      </div>
    </div>
  );
}

function Textarea({ label, placeholder, value, onChange }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: MUTED, marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.8px" }}>
        {label}
      </label>
      <textarea
        placeholder={placeholder} value={value} onChange={onChange}
        onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
        rows={5}
        style={{
          width: "100%", background: CARD, border: `1px solid ${focused ? "rgba(0,229,195,0.45)" : BORDER}`,
          borderRadius: 10, color: "#e8f4f1", fontFamily: "'DM Sans', sans-serif", fontSize: 14,
          padding: "12px 14px", outline: "none", resize: "vertical",
          boxShadow: focused ? "0 0 0 3px rgba(0,229,195,0.07)" : "none",
          transition: "border-color 0.3s, box-shadow 0.3s",
        }}
      />
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: MUTED, marginBottom: 7, textTransform: "uppercase", letterSpacing: "0.8px" }}>
        {label}
      </label>
      <div style={{ position: "relative" }}>
        <span style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", color: MUTED, pointerEvents: "none", fontSize: 12 }}>▾</span>
        <select
          value={value} onChange={onChange}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{
            width: "100%", background: CARD, border: `1px solid ${focused ? "rgba(0,229,195,0.45)" : BORDER}`,
            borderRadius: 10, color: value ? "#e8f4f1" : MUTED, fontFamily: "'DM Sans', sans-serif", fontSize: 14,
            padding: "11px 14px", outline: "none", appearance: "none", cursor: "pointer",
            boxShadow: focused ? "0 0 0 3px rgba(0,229,195,0.07)" : "none",
            transition: "border-color 0.3s, box-shadow 0.3s",
          }}
        >
          {options.map(o => <option key={o.value} value={o.value} style={{ background: CARD }}>{o.label}</option>)}
        </select>
      </div>
    </div>
  );
}

function InfoCard({ icon, title, value, delay, visible }) {
  return (
    <div style={{
      background: CARD, border: `1px solid ${BORDER}`, borderRadius: 14,
      padding: "18px 20px", display: "flex", alignItems: "center", gap: 14,
      opacity: visible ? 1 : 0, transform: visible ? "translateX(0)" : "translateX(30px)",
      transition: `opacity 0.6s ${delay}s ease, transform 0.6s ${delay}s ease`,
      cursor: "default",
    }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(0,229,195,0.3)"; e.currentTarget.style.boxShadow = "0 0 18px rgba(0,229,195,0.06)"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = BORDER; e.currentTarget.style.boxShadow = "none"; }}
    >
      <div style={{
        width: 40, height: 40, borderRadius: 10, flexShrink: 0,
        background: "rgba(0,229,195,0.08)", border: `1px solid rgba(0,229,195,0.15)`,
        display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
      }}>{icon}</div>
      <div>
        <div style={{ fontSize: 11, color: MUTED, textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 3 }}>{title}</div>
        <div style={{ fontSize: 14, color: "#e8f4f1", fontWeight: 500 }}>{value}</div>
      </div>
    </div>
  );
}

export default function ContactUs({ onBackClick }) {
  const [form, setForm] = useState({ name: "", email: "", company: "", subject: "", message: "" });
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [visible, setVisible] = useState(false);
  const [rightVisible, setRightVisible] = useState(false);

  useEffect(() => {
    setTimeout(() => setVisible(true), 100);
    setTimeout(() => setRightVisible(true), 300);
  }, []);

  const update = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }));

  const handleSubmit = () => {
    if (!form.name || !form.email || !form.message) return;
    setLoading(true);
    setTimeout(() => { setLoading(false); setSent(true); }, 2000);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background:${BG}; }
        input::placeholder, textarea::placeholder { color:${MUTED}; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes gridMove { to { background-position: 44px 44px; } }
        @keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
        @keyframes checkPop { 0% { transform:scale(0); opacity:0; } 70% { transform:scale(1.2); } 100% { transform:scale(1); opacity:1; } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: ${BG}; } ::-webkit-scrollbar-thumb { background: ${BORDER}; border-radius: 3px; }
      `}</style>

      {/* Grid bg */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0,
        backgroundImage: `linear-gradient(rgba(0,229,195,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,195,0.03) 1px, transparent 1px)`,
        backgroundSize: "44px 44px", animation: "gridMove 25s linear infinite",
      }} />

      {/* Orbs */}
      <div style={{ position: "fixed", top: -200, left: -200, width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,229,195,0.08), transparent 70%)", filter: "blur(70px)", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: -150, right: -150, width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,184,154,0.06), transparent 70%)", filter: "blur(70px)", zIndex: 0 }} />

      <Particles />

      {/* Page */}
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif", padding: "40px 20px" }}>
        <div style={{ width: "100%", maxWidth: 900, display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 28, alignItems: "start" }}>

          {/* ── LEFT — Info ── */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24, paddingTop: 8 }}>

            {/* Brand */}
            <div style={{
              opacity: visible ? 1 : 0, transform: visible ? "translateX(0)" : "translateX(-30px)",
              transition: "opacity 0.7s ease, transform 0.7s ease",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 9, background: `linear-gradient(135deg, ${TEAL}, #00b89a)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 17, color: BG,
                  boxShadow: `0 0 18px rgba(0,229,195,0.28)`,
                }}>L</div>
                <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 20, background: `linear-gradient(90deg, #e8f4f1, ${TEAL})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  LeacallBi
                </span>
              </div>
              <button
                type="button"
                onClick={onBackClick}
                style={{
                  marginBottom: 16,
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: `1px solid ${BORDER}`,
                  background: CARD,
                  color: TEAL,
                  fontFamily: "'DM Sans', sans-serif",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                ← Retour à la connexion
              </button>

              <h1 style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 32, lineHeight: 1.15, letterSpacing: "-0.8px", color: "#e8f4f1", marginBottom: 12 }}>
                Contactez-<br />
                <span style={{ background: `linear-gradient(90deg, ${TEAL}, #00c4ff)`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  nous
                </span>
              </h1>
              <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.8, maxWidth: 300 }}>
                Notre équipe est disponible pour répondre à vos questions, démonstrations et demandes commerciales.
              </p>
            </div>

            {/* Contact info cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <InfoCard icon="✉️" title="Email" value="contact@leacallbi.com" delay={0.4} visible={rightVisible} />
              <InfoCard icon="📞" title="Téléphone" value="+216 70 123 456" delay={0.5} visible={rightVisible} />
              <InfoCard icon="📍" title="Adresse" value="Tunis, Tunisie" delay={0.6} visible={rightVisible} />
              <InfoCard icon="🕐" title="Disponibilité" value="Lun–Ven, 09h–18h" delay={0.7} visible={rightVisible} />
            </div>

            {/* Status */}
            <div style={{
              opacity: rightVisible ? 1 : 0, transform: rightVisible ? "translateX(0)" : "translateX(30px)",
              transition: "opacity 0.6s 0.8s ease, transform 0.6s 0.8s ease",
              display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: MUTED,
            }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: TEAL, boxShadow: `0 0 6px ${TEAL}`, animation: "shimmer 2s ease-in-out infinite" }} />
              Temps de réponse moyen : &lt; 2h
            </div>
          </div>

          {/* ── RIGHT — Form ── */}
          <div style={{
            background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 20,
            padding: "36px 32px", position: "relative", overflow: "hidden",
            opacity: visible ? 1 : 0, transform: visible ? "translateY(0) scale(1)" : "translateY(24px) scale(0.97)",
            transition: "opacity 0.8s 0.2s cubic-bezier(0.16,1,0.3,1), transform 0.8s 0.2s cubic-bezier(0.16,1,0.3,1)",
            boxShadow: "0 30px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,229,195,0.05)",
          }}>
            {/* Shimmer top border */}
            <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${TEAL}, transparent)`, backgroundSize: "200% 100%", animation: "shimmer 3s linear infinite", opacity: 0.7 }} />
            {/* Corner glow */}
            <div style={{ position: "absolute", top: -50, right: -50, width: 140, height: 140, background: `radial-gradient(circle, rgba(0,229,195,0.07), transparent 70%)`, borderRadius: "50%", pointerEvents: "none" }} />

            {sent ? (
              /* Success state */
              <div style={{ textAlign: "center", padding: "40px 20px", animation: "fadeUp 0.6s ease forwards" }}>
                <div style={{
                  width: 64, height: 64, borderRadius: "50%",
                  background: "rgba(0,229,195,0.1)", border: `1px solid rgba(0,229,195,0.3)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  margin: "0 auto 20px", fontSize: 28,
                  animation: "checkPop 0.5s cubic-bezier(0.16,1,0.3,1) forwards",
                }}>✓</div>
                <h3 style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 20, color: "#e8f4f1", marginBottom: 10 }}>
                  Message envoyé !
                </h3>
                <p style={{ fontSize: 14, color: MUTED, lineHeight: 1.7 }}>
                  Merci pour votre message. Notre équipe vous répondra dans les plus brefs délais.
                </p>
                <button onClick={() => { setSent(false); setForm({ name: "", email: "", company: "", subject: "", message: "" }); }} style={{
                  marginTop: 24, padding: "10px 24px", borderRadius: 9, border: `1px solid ${BORDER}`,
                  background: CARD, color: TEAL, fontFamily: "'DM Sans', sans-serif", fontSize: 14,
                  cursor: "pointer", transition: "border-color 0.3s",
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(0,229,195,0.4)"}
                  onMouseLeave={e => e.currentTarget.style.borderColor = BORDER}
                >
                  Nouveau message
                </button>
              </div>
            ) : (
              <>
                <h2 style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 18, color: "#e8f4f1", marginBottom: 6 }}>
                  Envoyez-nous un message
                </h2>
                <p style={{ fontSize: 13, color: MUTED, marginBottom: 24 }}>Tous les champs marqués sont requis.</p>

                {/* Two-col row */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Input label="Nom complet *" placeholder="Votre nom" icon="👤" value={form.name} onChange={update("name")} />
                  <Input label="Email *" type="email" placeholder="vous@email.com" icon="✉" value={form.email} onChange={update("email")} />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <Input label="Entreprise" placeholder="Votre société" icon="🏢" value={form.company} onChange={update("company")} />
                  <Select
                    label="Sujet"
                    value={form.subject}
                    onChange={update("subject")}
                    options={[
                      { value: "", label: "Choisir un sujet…" },
                      { value: "demo", label: "Demande de démo" },
                      { value: "commercial", label: "Question commerciale" },
                      { value: "support", label: "Support technique" },
                      { value: "partnership", label: "Partenariat" },
                      { value: "other", label: "Autre" },
                    ]}
                  />
                </div>

                <Textarea label="Message *" placeholder="Décrivez votre besoin…" value={form.message} onChange={update("message")} />

                <button onClick={handleSubmit} disabled={loading || !form.name || !form.email || !form.message} style={{
                  width: "100%", padding: "12px", borderRadius: 10, border: "none",
                  background: (!form.name || !form.email || !form.message)
                    ? `rgba(0,229,195,0.25)`
                    : `linear-gradient(135deg, ${TEAL}, #00b89a)`,
                  color: (!form.name || !form.email || !form.message) ? "rgba(0,229,195,0.5)" : BG,
                  fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 15,
                  cursor: (!form.name || !form.email || !form.message || loading) ? "not-allowed" : "pointer",
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
                  boxShadow: (!form.name || !form.email || !form.message) ? "none" : `0 0 28px rgba(0,229,195,0.28), 0 4px 16px rgba(0,0,0,0.3)`,
                  transition: "all 0.3s",
                }}
                  onMouseEnter={e => { if (form.name && form.email && form.message && !loading) { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = `0 0 40px rgba(0,229,195,0.4), 0 8px 20px rgba(0,0,0,0.3)`; } }}
                  onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
                >
                  {loading
                    ? <><div style={{ width: 15, height: 15, border: `2px solid ${BG}`, borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} /> Envoi en cours…</>
                    : "Envoyer le message →"
                  }
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
