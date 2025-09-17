import { Link, useLocation } from "react-router-dom";
import { Home, Upload, List, History, LogIn, LogOut, User } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import ThemeToggle from "./ThemeToggle";
import GoogleLoginButton from "./GoogleLoginButton";

const Navigation = () => {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  const navItems = [
    { path: "/", label: "Home", icon: Home },
    { path: "/games", label: "Games", icon: List },
    { path: "/history", label: "History", icon: History },
  ];

  const handleLogout = () => {
    logout();
  };

  return (
    <>
      <nav className="nav">
        <div className="nav-content">
          <div className="flex items-center">
            <Link
              to="/"
              className="text-xl font-bold text-primary-600 dark:text-primary-400"
            >
              Chess Analysis
            </Link>
          </div>

          <div className="nav-links">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link ${
                  location.pathname === path ? "nav-link-active" : ""
                }`}
              >
                <Icon size={16} className="inline mr-2" />
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center space-x-4">
            <ThemeToggle />

            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {user?.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-8 h-8 rounded-full"
                    />
                  ) : (
                    <User
                      size={20}
                      className="text-gray-600 dark:text-gray-300"
                    />
                  )}
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {user?.name}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="btn btn-secondary text-sm"
                >
                  <LogOut size={14} />
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowLoginModal(true)}
                className="btn btn-primary text-sm"
              >
                <LogIn size={14} />
                Sign In
              </button>
            )}
          </div>
        </div>
      </nav>

      {showLoginModal && (
        <GoogleLoginButton onClose={() => setShowLoginModal(false)} />
      )}
    </>
  );
};

export default Navigation;
