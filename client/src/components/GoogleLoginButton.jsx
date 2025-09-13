import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { LogIn, User, X } from "lucide-react";

const GoogleLoginButton = ({ onClose }) => {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setError(null);

      // In a real app, you would use Google's official SDK
      // For now, we'll simulate this with a prompt for the token
      const mockToken = prompt("Enter Google OAuth token (for demo purposes):");

      if (!mockToken) {
        setLoading(false);
        return;
      }

      await login(mockToken);
      onClose?.();
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-dark-card rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Sign in to Chess Analysis
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={20} />
          </button>
        </div>

        <div className="text-center">
          <div className="mb-6">
            <User size={48} className="mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              Sign in with your Google account to save and manage your chess
              games.
            </p>
          </div>

          {error && <div className="error mb-4">{error}</div>}

          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="btn btn-primary w-full mb-4"
          >
            <LogIn size={16} />
            {loading ? "Signing in..." : "Sign in with Google"}
          </button>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            By signing in, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>
      </div>
    </div>
  );
};

export default GoogleLoginButton;
