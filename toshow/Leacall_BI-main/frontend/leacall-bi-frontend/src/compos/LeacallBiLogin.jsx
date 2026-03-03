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
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,229,195,${p.a})`;
        ctx.fill();
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

export default function LeacallBiLogin({ onContactClick }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => { setTimeout(() => setVisible(true), 100); }, []);

  const handleSubmit = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background:${BG}; }
        input::placeholder { color:${MUTED}; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes gridMove { to { background-position: 44px 44px; } }
        @keyframes shimmer { 0% { background-position:-200% 0; } 100% { background-position:200% 0; } }
      `}</style>

      {/* Grid bg */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0,
        backgroundImage: `linear-gradient(rgba(0,229,195,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,195,0.03) 1px, transparent 1px)`,
        backgroundSize: "44px 44px", animation: "gridMove 25s linear infinite",
      }} />

      {/* Glow orbs */}
      <div style={{ position: "fixed", top: -200, left: -200, width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,229,195,0.08), transparent 70%)", filter: "blur(60px)", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: -150, right: -150, width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,184,154,0.06), transparent 70%)", filter: "blur(60px)", zIndex: 0 }} />

      <Particles />

      {/* Center */}
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif", padding: 20 }}>
        <div style={{
          width: "100%", maxWidth: 400,
          background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 20,
          padding: "40px 36px", position: "relative", overflow: "hidden",
          opacity: visible ? 1 : 0, transform: visible ? "translateY(0) scale(1)" : "translateY(24px) scale(0.97)",
          transition: "opacity 0.8s cubic-bezier(0.16,1,0.3,1), transform 0.8s cubic-bezier(0.16,1,0.3,1)",
          boxShadow: "0 30px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,229,195,0.05)",
        }}>

          {/* Top shimmer line */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, height: 2,
            background: `linear-gradient(90deg, transparent, ${TEAL}, transparent)`,
            backgroundSize: "200% 100%", animation: "shimmer 3s linear infinite", opacity: 0.7,
          }} />

          {/* Logo */}
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 6 }}>
              <div style={{
                width: 38, height: 38, borderRadius: 10,
                background: `linear-gradient(135deg, ${TEAL}, #00b89a)`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 18, color: BG,
                boxShadow: `0 0 20px rgba(0,229,195,0.3)`,
              }}>L</div>
              <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 22, background: `linear-gradient(90deg, #e8f4f1, ${TEAL})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                LeacallBi
              </span>
            </div>
            <p style={{ fontSize: 13, color: MUTED, marginTop: 8 }}>Connectez-vous à votre espace</p>
          </div>

          {/* Form */}
          <Input label="Adresse e-mail" type="email" placeholder="vous@entreprise.com" icon="✉" value={email} onChange={e => setEmail(e.target.value)} />
          <Input label="Mot de passe" type="password" placeholder="••••••••" icon="🔒" value={password} onChange={e => setPassword(e.target.value)} />

          {/* Remember + Forgot */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22, marginTop: 4 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: MUTED, cursor: "pointer" }}>
              <div onClick={() => setRemember(!remember)} style={{
                width: 16, height: 16, borderRadius: 4, border: `1px solid ${remember ? TEAL : BORDER}`,
                background: remember ? TEAL : CARD, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s", boxShadow: remember ? `0 0 8px rgba(0,229,195,0.35)` : "none",
              }}>
                {remember && <span style={{ color: BG, fontSize: 10, fontWeight: 700 }}>✓</span>}
              </div>
              Se souvenir de moi
            </label>
            <span style={{ fontSize: 13, color: TEAL, cursor: "pointer", transition: "opacity 0.2s" }}
              onMouseEnter={e => e.target.style.opacity = "0.6"}
              onMouseLeave={e => e.target.style.opacity = "1"}>
              Mot de passe oublié ?
            </span>
          </div>

          {/* Submit */}
          <button onClick={handleSubmit} disabled={loading} style={{
            width: "100%", padding: "12px", borderRadius: 10, border: "none",
            background: `linear-gradient(135deg, ${TEAL}, #00b89a)`,
            color: BG, fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 15,
            cursor: loading ? "not-allowed" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            opacity: loading ? 0.7 : 1,
            boxShadow: `0 0 28px rgba(0,229,195,0.3), 0 4px 16px rgba(0,0,0,0.3)`,
            transition: "transform 0.2s, box-shadow 0.2s",
          }}
            onMouseEnter={e => { if (!loading) { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = `0 0 40px rgba(0,229,195,0.45), 0 8px 20px rgba(0,0,0,0.3)`; } }}
            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = `0 0 28px rgba(0,229,195,0.3), 0 4px 16px rgba(0,0,0,0.3)`; }}
          >
            {loading
              ? <><div style={{ width: 15, height: 15, border: `2px solid ${BG}`, borderTopColor: "transparent", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} /> Connexion…</>
              : "Se connecter →"
            }
          </button>

          <p style={{ textAlign: "center", fontSize: 12, color: MUTED, marginTop: 20 }}>
            Pas de compte ?{" "}
            <span style={{ color: TEAL, cursor: "pointer" }}
              onClick={onContactClick}
              onMouseEnter={e => e.target.style.opacity = "0.6"}
              onMouseLeave={e => e.target.style.opacity = "1"}>
              Contacter l'équipe commerciale
            </span>
          </p>
        </div>
      </div>
    </>
  );
}


