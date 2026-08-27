/**
 * Carga tiles Landsat / Col3 / Col4 / bordes y comentarios.
 * Landsat se recorta al bioma ejecutado.
 */

import { useState, useEffect, useCallback } from "react";
import { API_URL } from "../config/api";
import { normalizeCommentRow } from "../utils/normalizeComment";

function biomasQuery(biomas) {
  return biomas.map((b) => `biomas=${encodeURIComponent(b)}`).join("&");
}

export function useTeamLayers({ biomas, year, classIds, layersVisible, executed }) {
  const [tiles, setTiles] = useState({
    landsat: null,
    col3: null,
    col4: null,
    bordes: null,
  });
  const [inventario, setInventario] = useState(null);
  const [loadingTiles, setLoadingTiles] = useState(false);
  const [comentarios, setComentarios] = useState([]);
  const [comentariosNonce, setComentariosNonce] = useState(0);

  const refetchComentarios = useCallback(() => {
    setComentariosNonce((n) => n + 1);
  }, []);

  // Landsat — recortado a biomas ejecutados (misma máscara que Col3/Col4)
  useEffect(() => {
    let cancelled = false;

    if (!layersVisible.landsat || !executed || !biomas?.length) {
      setTiles((prev) => ({ ...prev, landsat: null }));
      return undefined;
    }

    const landsatYear = Math.min(Math.max(year, 1985), 2024);
    const bq = biomasQuery(biomas);

    fetch(`${API_URL}/landsat?year=${landsatYear}&${bq}`)
      .then(async (r) => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((d) => {
        if (!cancelled) {
          setTiles((prev) => ({ ...prev, landsat: d?.url || null }));
        }
      })
      .catch((err) => {
        console.error("Error Landsat:", err);
        if (!cancelled) setTiles((prev) => ({ ...prev, landsat: null }));
      });

    return () => {
      cancelled = true;
    };
  }, [year, layersVisible.landsat, executed, biomas]);

  // Col3 / Col4 / bordes — requieren Ejecutar + biomas
  useEffect(() => {
    if (!executed || !biomas?.length) return;

    let cancelled = false;
    setLoadingTiles(true);

    const classParam =
      classIds?.length > 0 ? `&class_id=${classIds.join(",")}` : "";
    const bq = biomasQuery(biomas);

    const jobs = [];

    if (layersVisible.col4) {
      jobs.push(
        fetch(`${API_URL}/tiles/col4?year=${year}&${bq}${classParam}`)
          .then((r) => r.json())
          .then((d) => ({ key: "col4", url: d.url || null })),
      );
    } else {
      jobs.push(Promise.resolve({ key: "col4", url: null }));
    }

    if (layersVisible.col3) {
      jobs.push(
        fetch(`${API_URL}/tiles/col3?year=${year}&${bq}${classParam}`)
          .then((r) => r.json())
          .then((d) => ({ key: "col3", url: d.url || null })),
      );
    } else {
      jobs.push(Promise.resolve({ key: "col3", url: null }));
    }

    if (layersVisible.bordes) {
      jobs.push(
        fetch(`${API_URL}/tiles/bordes?${bq}`)
          .then((r) => r.json())
          .then((d) => ({ key: "bordes", url: d.url || null })),
      );
    } else {
      jobs.push(Promise.resolve({ key: "bordes", url: null }));
    }

    Promise.all(jobs)
      .then((results) => {
        if (cancelled) return;
        setTiles((prev) => {
          const next = { ...prev };
          results.forEach((r) => {
            next[r.key] = r.url;
          });
          return next;
        });
      })
      .catch((err) => console.error("Error tiles TEAM:", err))
      .finally(() => {
        if (!cancelled) setLoadingTiles(false);
      });

    return () => {
      cancelled = true;
    };
  }, [
    executed,
    biomas,
    year,
    classIds,
    layersVisible.col3,
    layersVisible.col4,
    layersVisible.bordes,
  ]);

  useEffect(() => {
    if (!executed || !biomas?.length) return;
    let cancelled = false;
    fetch(`${API_URL}/inventario?${biomasQuery(biomas)}`)
      .then((r) => r.json())
      .then((d) => {
        if (!cancelled) setInventario(d);
      })
      .catch((err) => console.error("Error inventario:", err));
    return () => {
      cancelled = true;
    };
  }, [executed, biomas]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/puntos`)
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        setComentarios(
          Array.isArray(data) ? data.map(normalizeCommentRow).filter(Boolean) : [],
        );
      })
      .catch((err) => console.error("Error comentarios:", err));
    return () => {
      cancelled = true;
    };
  }, [comentariosNonce]);

  return {
    tiles,
    inventario,
    loadingTiles,
    comentarios,
    refetchComentarios,
  };
}
