import { Link, useNavigate, useLocation } from "react-router-dom";
import { LogOut, Link2, BarChart3 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

export function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="topnav">
      <Link to="/dashboard" className="topnav-brand">
        <span className="brand-mark">LF</span>
        LinkFolio
      </Link>
      {user && (
        <nav className="topnav-links">
          <Link to="/dashboard" className={location.pathname === "/dashboard" ? "active" : ""}>
            <Link2 size={16} /> Links
          </Link>
          <Link to="/analytics" className={location.pathname === "/analytics" ? "active" : ""}>
            <BarChart3 size={16} /> Analytics
          </Link>
        </nav>
      )}
      {user && (
        <div className="topnav-actions">
          <a href={`/u/${user.username}`} target="_blank" rel="noopener noreferrer" className="topnav-preview">
            View my page
          </a>
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            <LogOut size={16} />
            Log out
          </button>
        </div>
      )}
    </header>
  );
}
