import React, { useEffect, useState } from "react";
import "./MonthlyLineChart.css";

/**
 * Loads Recharts only after the main thread is idle (or soon via timeout),
 * so route JS parses and paints before the heavy chart chunk.
 */
export default function DeferredMonthlyLineChart(props) {
  const [Chart, setChart] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      import("./MonthlyLineChart").then((m) => {
        if (!cancelled) setChart(() => m.default);
      });
    };

    if (typeof requestIdleCallback !== "undefined") {
      const id = requestIdleCallback(load, { timeout: 1500 });
      return () => {
        cancelled = true;
        cancelIdleCallback(id);
      };
    }

    const t = setTimeout(load, 0);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, []);

  if (!Chart) {
    return (
      <section className="monthly-line-chart glass-panel" aria-busy="true">
        <h3 className="monthly-line-chart__title">{props.title}</h3>
        <div className="monthly-line-chart__plot" aria-hidden />
      </section>
    );
  }

  return <Chart {...props} />;
}
