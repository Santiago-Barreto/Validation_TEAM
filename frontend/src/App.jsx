import React, { useCallback, useEffect, useMemo, useState } from "react";
import MapView from "./components/MapView";
import ControlPanel from "./components/ControlPanel";
import CommentDrawer from "./components/CommentDrawer";
import StatsFloatingPanel from "./components/StatsFloatingPanel";
import LayersFloatingControl from "./components/LayersFloatingControl";
import LegendFloatingPanel from "./components/LegendFloatingPanel";
import LoginScreen from "./auth/LoginScreen";
import { useAuth } from "./auth/AuthContext";
import { useDebounce } from "./hooks/useDebounce";
import { useTeamLayers } from "./hooks/useTeamLayers";
import { API_URL } from "./config/api";
import {
  flushOfflineCommentQueue,
  getQueuedCount,
} from "./services/offlineQueue";
import "./App.css";

function UserAvatar({ name, picture }) {
  const [failed, setFailed] = useState(false);
  const initial = (name || "?").trim().charAt(0).toUpperCase() || "?";

  if (!picture || failed) {
    return (
      <span className="user-avatar fallback" aria-hidden="true">
        {initial}
      </span>
    );
  }

  return (
    <img
      src={picture}
      alt=""
      className="user-avatar"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}

export default function App() {
  const { isAuthenticated, user, logout, loading: authLoading } = useAuth();
  const [config, setConfig] = useState(null);
  const [bootError, setBootError] = useState(null);

  const [selectedBiomas, setSelectedBiomas] = useState([]);
  const [executedBiomas, setExecutedBiomas] = useState([]);
  const [executed, setExecuted] = useState(false);

  const [tempYear, setTempYear] = useState(2025);
  const year = useDebounce(tempYear, 350);

  const [layersVisible, setLayersVisible] = useState({
    landsat: false,
    col4: true,
    col3: false,
    bordes: false,
    solar: true,
  });

  const [selectedClasses, setSelectedClasses] = useState([]);

  const [commentMode, setCommentMode] = useState(false);
  const [landsatStyle, setLandsatStyle] = useState("green");
  const [swipeMode, setSwipeMode] = useState(false);
  const [swipeRatio, setSwipeRatio] = useState(0.5);
  const [commentsVisible, setCommentsVisible] = useState(true);
  const [draftPoints, setDraftPoints] = useState([]);
  const [clickPos, setClickPos] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingComment, setEditingComment] = useState(null);
  const [identify, setIdentify] = useState(null);
  const [loadingIdentify, setLoadingIdentify] = useState(false);
  const [queuedOfflineCount, setQueuedOfflineCount] = useState(() =>
    getQueuedCount(),
  );
  const [solarPlants, setSolarPlants] = useState([]);
  const [biomeStats, setBiomeStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [mapFocus, setMapFocus] = useState(null);

  const classIdsKey = useMemo(
    () => [...selectedClasses].sort((a, b) => a - b).join(","),
    [selectedClasses],
  );
  const classIds = useMemo(
    () => (classIdsKey ? classIdsKey.split(",").map(Number) : []),
    [classIdsKey],
  );

  const { tiles, inventario, loadingTiles, comentarios, refetchComentarios } =
    useTeamLayers({
      biomas: executedBiomas,
      year,
      classIds,
      layersVisible,
      executed,
      landsatStyle,
    });

  const comentariosEnBioma = useMemo(() => {
    if (!executed || !executedBiomas.length) return [];
    const visibles = new Set(executedBiomas);
    return (comentarios || []).filter((c) => {
      const b = (c.bioma || "").trim();
      if (!b) return true;
      if (visibles.has(b)) return true;
      if (
        (b === "Pacifico" || b === "Pacifico insular") &&
        visibles.has("Pacífico")
      ) {
        return true;
      }
      if (b === "Caribe Insular" && visibles.has("Caribe")) return true;
      return false;
    });
  }, [comentarios, executed, executedBiomas]);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetch(`${API_URL}/configuracion`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setConfig(data);
        if (data.yearMax) setTempYear(Math.min(2025, data.yearMax));
        setBootError(null);
      })
      .catch((err) => {
        console.error(err);
        setBootError(
          "No se pudo conectar al backend. Arranca uvicorn en el puerto 8000.",
        );
      });
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated || !navigator.onLine) return undefined;
    let cancelled = false;
    flushOfflineCommentQueue().then((sent) => {
      if (cancelled) return;
      setQueuedOfflineCount(getQueuedCount());
      if (sent > 0) refetchComentarios();
    });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, refetchComentarios]);

  useEffect(() => {
    if (!isAuthenticated) return undefined;
    const onOnline = () => {
      flushOfflineCommentQueue().then((sent) => {
        setQueuedOfflineCount(getQueuedCount());
        if (sent > 0) refetchComentarios();
      });
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [isAuthenticated, refetchComentarios]);

  useEffect(() => {
    if (!executed || !executedBiomas.length) {
      setBiomeStats(null);
      return undefined;
    }
    let cancelled = false;
    setLoadingStats(true);
    const bq = executedBiomas
      .map((b) => `biomas=${encodeURIComponent(b)}`)
      .join("&");
    fetch(`${API_URL}/stats/bioma?${bq}`)
      .then(async (r) => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((data) => {
        if (!cancelled) setBiomeStats(data);
      })
      .catch((err) => {
        console.error("Error stats bioma:", err);
        if (!cancelled) {
          setBiomeStats({
            disponible: false,
            mensaje: err.message || "No se pudieron cargar estadísticas",
            biomas: executedBiomas,
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingStats(false);
      });
    return () => {
      cancelled = true;
    };
  }, [executed, executedBiomas]);

  useEffect(() => {
    if (!executed || !executedBiomas.length || !layersVisible.solar) {
      setSolarPlants([]);
      return undefined;
    }
    let cancelled = false;
    const bq = executedBiomas
      .map((b) => `biomas=${encodeURIComponent(b)}`)
      .join("&");
    fetch(`${API_URL}/solar?${bq}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (!cancelled) setSolarPlants(data.points || []);
      })
      .catch((err) => {
        console.error("Error plantas solares:", err);
        if (!cancelled) setSolarPlants([]);
      });
    return () => {
      cancelled = true;
    };
  }, [executed, executedBiomas, layersVisible.solar]);

  const toggleBioma = (b) => {
    setSelectedBiomas((prev) =>
      prev.includes(b) ? prev.filter((x) => x !== b) : [...prev, b],
    );
  };

  const onEjecutar = () => {
    if (!selectedBiomas.length) {
      window.alert("Selecciona al menos un bioma.");
      return;
    }
    setExecutedBiomas([...selectedBiomas]);
    setExecuted(true);
  };

  const onToggleLayer = useCallback((key) => {
    setLayersVisible((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const onToggleSwipe = useCallback(() => {
    setSwipeMode((on) => {
      const next = !on;
      if (next) {
        // Al entrar a swipe, carga ambas capas (opacas); se pueden apagar después.
        setLayersVisible((prev) => ({ ...prev, landsat: true, col4: true }));
      }
      return next;
    });
  }, []);

  const handleMapClick = useCallback(
    async (latlng) => {
      // Modo comentario: solo basemap. Cada clic agrega un marcador borrador.
      if (commentMode) {
        if (!executed) return;
        const lat = latlng.lat;
        const lon = latlng.lng;
        if (lat < -5 || lat > 13.6 || lon < -82 || lon > -66) {
          window.alert(
            "Solo se pueden crear comentarios dentro de Colombia.",
          );
          return;
        }
        const point = {
          id: `draft-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          lat,
          lng: lon,
        };
        setDraftPoints((prev) => [...prev, point]);
        setClickPos(latlng);
        setEditingComment(null);
        setDrawerOpen(true);
        return;
      }

      if (!executed) return;
      setClickPos(latlng);
      setLoadingIdentify(true);
      setIdentify(null);

      try {
        const bq = executedBiomas
          .map((b) => `biomas=${encodeURIComponent(b)}`)
          .join("&");
        const res = await fetch(
          `${API_URL}/identificar-clase?lat=${latlng.lat}&lon=${latlng.lng}&year=${year}&${bq}`,
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setIdentify(data);
      } catch (err) {
        console.error(err);
        setIdentify({ error: true, message: "No se pudo consultar el punto" });
      } finally {
        setLoadingIdentify(false);
      }
    },
    [commentMode, executed, executedBiomas, year],
  );

  if (authLoading) {
    return (
      <div className="app-boot">
        <h1>LULC TEAM</h1>
        <div className="loader" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  if (bootError) {
    return (
      <div className="app-boot">
        <h1>LULC TEAM</h1>
        <p>{bootError}</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="app-boot">
        <p className="brand-kicker brand-kicker-on-dark">GAIA · MapBiomas Colombia</p>
        <h1>LULC TEAM</h1>
        <p>Cargando configuración…</p>
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="user-chip" title={user?.email}>
        <UserAvatar name={user?.name} picture={user?.picture} />
        <span className="user-chip-text">
          <strong>{user?.name}</strong>
          <small>{user?.email}</small>
        </span>
        <button type="button" className="btn-ghost user-logout" onClick={logout}>
          Salir
        </button>
      </div>

      <ControlPanel
        config={config}
        selectedBiomas={selectedBiomas}
        onToggleBioma={toggleBioma}
        onEjecutar={onEjecutar}
        executed={executed}
        inventario={inventario}
        loadingTiles={loadingTiles}
        year={tempYear}
        onYearChange={setTempYear}
        yearMin={config.yearMin}
        yearMax={config.yearMax}
        commentMode={commentMode}
        onToggleCommentMode={() => {
          setCommentMode((active) => {
            if (active) {
              setDrawerOpen(false);
              setDraftPoints([]);
            }
            return !active;
          });
        }}
        commentsVisible={commentsVisible}
        onToggleCommentsVisible={() => setCommentsVisible((v) => !v)}
        queuedOfflineCount={queuedOfflineCount}
        clickPos={clickPos}
        identify={identify}
        loadingIdentify={loadingIdentify}
        identifyYear={year}
      />

      <main className="map-pane">
        <MapView
          activeBasemap="satelite"
          tiles={tiles}
          layersVisible={layersVisible}
          comentarios={commentsVisible ? comentariosEnBioma : []}
          draftPoints={draftPoints}
          onDraftPointClick={(id) => {
            setDraftPoints((prev) => {
              const next = prev.filter((p) => p.id !== id);
              if (!next.length) setDrawerOpen(false);
              return next;
            });
          }}
          clickPos={clickPos}
          clickEnabled={executed}
          onMapClick={handleMapClick}
          year={tempYear}
          mapFocus={mapFocus}
          onCommentResolved={() => refetchComentarios()}
          solarPlants={layersVisible.solar ? solarPlants : []}
          onCommentEdit={(punto) => {
            setDraftPoints([]);
            setDrawerOpen(false);
            setEditingComment(punto);
          }}
          landsatStyle={landsatStyle}
          swipeMode={swipeMode}
          swipeRatio={swipeRatio}
          onSwipeRatioChange={setSwipeRatio}
        />
        {loadingTiles && <div className="map-loading">Actualizando capas…</div>}
        {commentMode && draftPoints.length > 0 && (
          <div className="repeat-comment-banner">
            <span>
              {draftPoints.length} marcador
              {draftPoints.length === 1 ? "" : "es"} — escribe el comentario y
              envía
            </span>
          </div>
        )}

        <LayersFloatingControl
          executed={executed}
          layersVisible={layersVisible}
          onToggleLayer={onToggleLayer}
          landsatStyle={landsatStyle}
          landsatStyles={config.landsatStyles || []}
          onLandsatStyleChange={setLandsatStyle}
          swipeMode={swipeMode}
          onToggleSwipe={onToggleSwipe}
        />

        <LegendFloatingPanel
          executed={executed}
          leyenda={config.leyenda || []}
          selectedClasses={selectedClasses}
          onToggleClass={(id) =>
            setSelectedClasses((prev) =>
              prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
            )
          }
          onClearClasses={() => setSelectedClasses([])}
        />


        <StatsFloatingPanel
          open={executed}
          biomeStats={biomeStats}
          loadingStats={loadingStats}
          executedBiomas={executedBiomas}
          onMapFocus={setMapFocus}
        />
      </main>

      {(editingComment || (drawerOpen && draftPoints.length > 0)) && (
        <CommentDrawer
          draftPoints={draftPoints}
          year={year}
          biomas={executedBiomas}
          editingComment={editingComment}
          onClose={() => {
            setDrawerOpen(false);
            setEditingComment(null);
          }}
          onSaved={() => {
            refetchComentarios();
            setQueuedOfflineCount(getQueuedCount());
          }}
          onQueueChanged={setQueuedOfflineCount}
          onClearDrafts={() => {
            setDraftPoints([]);
            setDrawerOpen(false);
          }}
        />
      )}
    </div>
  );
}
