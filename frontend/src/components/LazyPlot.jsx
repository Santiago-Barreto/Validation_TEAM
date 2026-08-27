/**
 * Plotly bajo demanda. Si el chunk falla, no tumba el resto de la app.
 */
import React, { Component, Suspense, lazy } from "react";

const LazyPlotInner = lazy(() =>
  Promise.all([
    import("plotly.js-cartesian-dist"),
    import("react-plotly.js/factory"),
  ]).then(([plotlyMod, factoryMod]) => {
    const Plotly = plotlyMod.default || plotlyMod;
    const createPlotlyComponent = factoryMod.default || factoryMod;
    if (typeof createPlotlyComponent !== "function") {
      throw new Error("react-plotly factory no disponible");
    }
    return { default: createPlotlyComponent(Plotly) };
  }),
);

class PlotErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="stats-plot-skeleton">
          No se pudo cargar el gráfico. Recarga la página.
        </div>
      );
    }
    return this.props.children;
  }
}

export default function LazyPlot(props) {
  return (
    <PlotErrorBoundary>
      <Suspense
        fallback={<div className="stats-plot-skeleton">Cargando gráfico…</div>}
      >
        <LazyPlotInner {...props} />
      </Suspense>
    </PlotErrorBoundary>
  );
}
