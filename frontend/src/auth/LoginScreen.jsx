import { useEffect, useRef } from "react";
import { useAuth } from "./AuthContext";

function loadGisScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const existing = document.getElementById("google-gis");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", reject);
      return;
    }
    const script = document.createElement("script");
    script.id = "google-gis";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

export default function LoginScreen() {
  const { authConfig, configError, loginWithCredential, error, setError, loading } = useAuth();
  const btnRef = useRef(null);

  useEffect(() => {
    if (!authConfig?.enabled || !authConfig.client_id || !btnRef.current) return;
    let cancelled = false;

    loadGisScript()
      .then(() => {
        if (cancelled || !window.google?.accounts?.id) return;
        window.google.accounts.id.initialize({
          client_id: authConfig.client_id,
          callback: async (response) => {
            try {
              await loginWithCredential(response.credential);
            } catch {
              /* error already in context */
            }
          },
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        btnRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(btnRef.current, {
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "pill",
          width: 320,
        });
      })
      .catch(() => setError("No se pudo cargar el inicio de sesión de Google."));

    return () => {
      cancelled = true;
    };
  }, [authConfig, loginWithCredential, setError]);

  if (loading) {
    return (
      <div className="app-boot">
        <p className="brand-kicker brand-kicker-on-dark">
          GAIA · MapBiomas Colombia
        </p>
        <h1>LULC TEAM</h1>
        <div className="loader" />
      </div>
    );
  }

  const domain =
    (authConfig?.allowed_domains && authConfig.allowed_domains[0]) ||
    "gaiaamazonas.org";

  return (
    <div className="app-boot login-screen">
      <p className="brand-kicker brand-kicker-on-dark">
        GAIA · MapBiomas Colombia
      </p>
      <h1>LULC TEAM</h1>
      <p className="login-copy">
        Inicia sesión con tu correo @{domain}.
      </p>

      {configError ? (
        <p className="warn login-warn">{configError}</p>
      ) : !authConfig?.enabled ? (
        <p className="warn login-warn">
          Falta configurar <code>GOOGLE_OAUTH_CLIENT_ID</code> en{" "}
          <code>backend/.env</code>.
        </p>
      ) : (
        <div ref={btnRef} className="google-btn-slot" />
      )}

      {error ? <p className="warn login-warn">{error}</p> : null}
    </div>
  );
}
