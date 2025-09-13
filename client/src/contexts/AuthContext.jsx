import { createContext, useContext, useEffect, useState } from "react";
import { gamesApi } from "../utils/api";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem("authToken"));

  useEffect(() => {
    // Set token in API client
    if (token) {
      gamesApi.setAuthToken(token);
      // Verify token and get user info
      checkAuth();
    } else {
      setLoading(false);
    }
  }, [token]);

  const checkAuth = async () => {
    try {
      const userData = await gamesApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Auth check failed:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (googleToken) => {
    try {
      setLoading(true);
      const response = await gamesApi.googleAuth(googleToken);
      const { access_token, user: userData } = response;

      localStorage.setItem("authToken", access_token);
      setToken(access_token);
      setUser(userData);
      gamesApi.setAuthToken(access_token);

      return userData;
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("authToken");
    setToken(null);
    setUser(null);
    gamesApi.setAuthToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
