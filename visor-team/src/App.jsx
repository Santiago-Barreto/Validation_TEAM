import React, { useCallback, useEffect, useMemo, useState } from "react";
import MapView from "./components/MapView";
import ControlPanel from "./components/ControlPanel";
import CommentDrawer from "./components/CommentDrawer";
import StatsFloatingPanel from "./components/StatsFloatingPanel";
import LayersFloatingControl from "./components/LayersFloatingControl";
import { useDebounce } from "./hooks/useDebounce";
import { useTeamLayers } from "./hooks/useTeamLayers";
import { API_URL } from "./config/api";
import {
  flushOfflineCommentQueue,
  getQueuedCount,
} from "./services/offlineQueue";
import "./App.css";

export default function App() {
  const [config, setConfig] = useState(null);
  const [bootError, setBootError] = useState(null);

  const [selectedBiomas, setSelectedBiomas] = useState([]);
  const [executedBiomas, setExecutedBiomas] = useState([]);
  const [executed, setExecuted] = useState(false);

  const [tempYear, setTempYear] = useState(2024);
  const year = useDebounce(tempYear, 350);

  const [layersVisible, setLayersVisible] = useState({
    landsat: false,
    col4: true,
    col3: false,
    bordes: false,
  });
  const [opacities, setOpacities] = useState({
    landsat: 1,
    col4: 1,
    col3: 0.85,
  });

  const [showCoberturas, setShowCoberturas] = useState(false);
  const [selectedClasses, setSelectedClasses] = useState([]);

  const [commentMode, setCommentMode] = useState(false);
  const [clickPos, setClickPos] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [identify, setIdentify] = useState(null);
  const [loadingIdentify, setLoadingIdentify] = useState(false);
  const [queuedOfflineCount, setQueuedOfflineCount] = useState(() =>
    getQueuedCount(),
  );
  const [biomeStats, setBiomeStats] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);
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
    });

  useEffect(() => {
    fetch(`${API_URL}/configuracion`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setConfig(data);
        if (data.yearMax) setTempYear(Math.min(2024, data.yearMax));
      })
      .catch((err) => {
        console.error(err);
        setBootError(
          "No se pudo conectar al backend. Arranca uvicorn en el puerto 8000.",
        );
      });
  }, []);

  useEffect(() => {
    if (!navigator.onLine) return undefined;
    let cancelled = false;
    flushOfflineCommentQueue().then((sent) => {
      if (cancelled) return;
      setQueuedOfflineCount(getQueuedCount());
      if (sent > 0) refetchComentarios();
    });
    return () => {
      cancelled = true;
    };
  }, [refetchComentarios]);

  useEffect(() => {
    const onOnline = () => {
      flushOfflineCommentQueue().then((sent) => {
        setQueuedOfflineCount(getQueuedCount());
        if (sent > 0) refetchComentarios();
      });
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [refetchComentarios]);

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
    setStatsOpen(true);
  };

  const onToggleLayer = useCallback((key) => {
    setLayersVisible((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const onOpacityChange = useCallback((key, value) => {
    setOpacities((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleMapClick = useCallback(
    async (latlng) => {
      if (!executed) return;
      setClickPos(latlng);
      setLoadingIdentify(true);
      setIdentify(null);
      if (commentMode) setDrawerOpen(true);

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

  if (bootError) {
    return (
      <div className="app-boot">
        <h1>Validation TEAM</h1>
        <p>{bootError}</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="app-boot">
        <h1>Validation TEAM</h1>
        <p>Cargando configuración MapBiomas…</p>
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="app-shell">
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
        showCoberturas={showCoberturas}
        onToggleCoberturasPanel={() => setShowCoberturas((v) => !v)}
        selectedClasses={selectedClasses}
        onToggleClass={(id) =>
          setSelectedClasses((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
          )
        }
        onClearClasses={() => setSelectedClasses([])}
        commentMode={commentMode}
        onToggleCommentMode={() => setCommentMode((v) => !v)}
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
          opacities={opacities}
          comentarios={comentarios}
          clickPos={clickPos}
          clickEnabled={executed}
          onMapClick={handleMapClick}
          year={tempYear}
          mapFocus={mapFocus}
        />
        {loadingTiles && <div className="map-loading">Actualizando capas…</div>}

        <LayersFloatingControl
          executed={executed}
          layersVisible={layersVisible}
          onToggleLayer={onToggleLayer}
          opacities={opacities}
          onOpacityChange={onOpacityChange}
        />

        {executed && !statsOpen && (
          <button
            type="button"
            className="stats-reopen-btn"
            onClick={() => setStatsOpen(true)}
          >
            Estadísticas bioma
          </button>
        )}

        <StatsFloatingPanel
          open={executed && statsOpen}
          onClose={() => setStatsOpen(false)}
          biomeStats={biomeStats}
          loadingStats={loadingStats}
          executedBiomas={executedBiomas}
          onMapFocus={setMapFocus}
        />
      </main>

      {drawerOpen && (
        <CommentDrawer
          clickPos={clickPos}
          identify={identify}
          loadingIdentify={loadingIdentify}
          year={year}
          biomas={executedBiomas}
          onClose={() => setDrawerOpen(false)}
          onSaved={() => {
            refetchComentarios();
            setQueuedOfflineCount(getQueuedCount());
          }}
          onQueueChanged={setQueuedOfflineCount}
        />
      )}
    </div>
  );
}
