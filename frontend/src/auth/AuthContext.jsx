import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { API_URL } from "../config/api";
import {
  clearSession,
  getStoredToken,
  getStoredUser,
  storeSession,
} from "../services/authStorage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [token, setToken] = useState(() => getStoredToken());
  const [authConfig, setAuthConfig] = useState(null);
  const [configError, setConfigError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/auth/config`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((cfg) => {
        if (!cancelled) {
          setAuthConfig(cfg);
          setConfigError("");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAuthConfig({ enabled: false, client_id: "", allowed_domains: [] });
          setConfigError(
            "No se pudo conectar al backend. Arranca uvicorn en el puerto 8000 y recarga la página.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (r) => {
        if (!r.ok) throw new Error("expired");
        return r.json();
      })
      .then((u) => {
        if (!cancelled) {
          setUser(u);
          storeSession(token, u);
        }
      })
      .catch(() => {
        if (!cancelled) {
          clearSession();
          setUser(null);
          setToken("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const loginWithCredential = useCallback(async (credential) => {
    setError("");
    const res = await fetch(`${API_URL}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential }),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = body.detail || "No se pudo iniciar sesión.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      throw new Error(msg);
    }
    storeSession(credential, body);
    setToken(credential);
    setUser(body);
    return body;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setToken("");
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      authConfig,
      configError,
      loading,
      error,
      setError,
      loginWithCredential,
      logout,
      isAuthenticated: Boolean(user && token),
    }),
    [user, token, authConfig, configError, loading, error, loginWithCredential, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
