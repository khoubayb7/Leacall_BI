import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { getStoredUser, logoutUser } from "../../services/authService";

function SidebarIcon({ icon }) {
  if (icon === "grid") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    );
  }

  if (icon === "users") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <circle cx="8" cy="8" r="3" />
        <path d="M2.8 19.5c.5-3 2.5-4.8 5.2-4.8s4.7 1.8 5.2 4.8" fill="none" strokeWidth="2" strokeLinecap="round" />
        <circle cx="17" cy="7" r="2.5" />
        <path d="M14.2 15.8c1.1-.9 2-1.3 3-1.3 2.1 0 3.6 1.3 4 3.5" fill="none" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (icon === "file") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <path d="M7 3.5h7.5L19 8v12.5H7z" fill="none" strokeWidth="2" />
        <path d="M14.5 3.5V8H19" fill="none" strokeWidth="2" />
        <path d="M9.5 12h7M9.5 15.5h7" fill="none" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (icon === "settings") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <circle cx="12" cy="12" r="3.2" />
        <path d="M12 3.8v2.1M12 18.1v2.1M20.2 12h-2.1M5.9 12H3.8M18 6l-1.5 1.5M7.5 16.5L6 18M18 18l-1.5-1.5M7.5 7.5L6 6" fill="none" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (icon === "bell") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <path d="M6.5 17.5h11l-1.6-2.8V10a3.9 3.9 0 0 0-7.8 0v4.7z" fill="none" strokeWidth="2" strokeLinejoin="round" />
        <path d="M10 19.2c.4 1.1 1 1.5 2 1.5s1.6-.4 2-1.5" fill="none" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (icon === "phone") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <path d="M7.6 4.5l2.5 3.2-1.6 1.6c.8 2.1 2.2 3.5 4.3 4.3l1.6-1.6 3.2 2.5-1.1 3.1c-.2.7-.9 1.1-1.7 1-6-.9-10.7-5.6-11.6-11.6-.1-.8.3-1.5 1-1.7z" fill="none" strokeWidth="2" strokeLinejoin="round" />
      </svg>
    );
  }

  if (icon === "chart") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
        <path d="M4 19.5h16" fill="none" strokeWidth="2" strokeLinecap="round" />
        <rect x="6" y="11" width="3.5" height="6" rx="1" />
        <rect x="10.8" y="8" width="3.5" height="9" rx="1" />
        <rect x="15.6" y="5" width="3.5" height="12" rx="1" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="sidebar-icon-svg">
      <path d="M4.5 7h15M4.5 12h15M4.5 17h15" fill="none" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function AppShell({ brandName, brandInitial, menuItems, version = "v1.0.0" }) {
  const navigate = useNavigate();
  const user = getStoredUser();

  const onLogout = async () => {
    await logoutUser();
    navigate("/login", { replace: true });
  };

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <div>
          <header className="sidebar-header">
            <div className="brand-badge">{brandInitial}</div>
            <div className="brand-name">{brandName}</div>
          </header>

          <nav className="sidebar-nav" aria-label="Role navigation">
            {menuItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
              >
                <SidebarIcon icon={item.icon} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <footer className="sidebar-footer">
          <p className="sidebar-user">@{user?.username || "unknown"}</p>
          <button className="sidebar-logout" onClick={onLogout} type="button">Logout</button>
          <span className="sidebar-version">{version}</span>
        </footer>
      </aside>

      <main className="workspace-main">
        <Outlet />
      </main>
    </div>
  );
}
