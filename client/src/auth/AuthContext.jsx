import { createContext, useCallback, useContext, useMemo, useState } from "react";
import * as authApi from "../api/auth";
import { getToken, setToken } from "../api/client";

const USER_KEY = "linkfolio_user";

function readStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => (getToken() ? readStoredUser() : null));

  const applyAuthResponse = useCallback((auth) => {
    setToken(auth.token);
    const nextUser = { userId: auth.user_id, name: auth.name, email: auth.email, username: auth.username };
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
  }, []);

  const login = useCallback(
    async (email, password) => {
      const auth = await authApi.login(email, password);
      applyAuthResponse(auth);
    },
    [applyAuthResponse]
  );

  const register = useCallback(
    async (name, email, username, password) => {
      const auth = await authApi.register(name, email, username, password);
      applyAuthResponse(auth);
    },
    [applyAuthResponse]
  );

  const updateProfile = useCallback((updates) => {
    setUser((current) => {
      const next = { ...current, ...updates };
      localStorage.setItem(USER_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isAuthenticated: user !== null, login, register, logout, updateProfile }),
    [user, login, register, logout, updateProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
