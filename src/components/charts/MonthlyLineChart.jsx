import React from "react";
import "./MonthlyLineChart.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/**
 * @param {{ title: string, data: Array<Record<string, unknown>>, xDataKey?: string, valueLabel?: string, color?: string, formatTooltipValue?: (n: number) => string, formatYAxis?: (n: number) => string, formatTooltipExtra?: (payload: Record<string, unknown>) => string | undefined }} props
 */
function MonthlyLineChart({
  title,
  data,
  xDataKey = "month",
  valueLabel = "Amount",
  color = "#007fff",
  formatTooltipValue,
  formatYAxis,
  formatTooltipExtra,
}) {
  const fmtTip = formatTooltipValue ?? ((v) => Number(v).toLocaleString());
  const fmtAxis = formatYAxis ?? ((v) => (Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(Math.round(v))));
  const bottomMargin = xDataKey === "city" ? 28 : 0;
  return (
    <section className="monthly-line-chart glass-panel">
      <h3 className="monthly-line-chart__title">{title}</h3>
      <div className="monthly-line-chart__plot">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: bottomMargin }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
            <XAxis
              dataKey={xDataKey}
              tick={{ fontSize: xDataKey === "city" ? 10 : 11, fill: "#64748b" }}
              axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
              interval={0}
              angle={xDataKey === "city" ? -28 : 0}
              textAnchor={xDataKey === "city" ? "end" : "middle"}
              height={xDataKey === "city" ? 56 : undefined}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b" }}
              axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
              tickFormatter={(v) => fmtAxis(Number(v))}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid rgba(148, 163, 184, 0.35)",
                boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
              }}
              formatter={(value, _name, item) => {
                const row = item?.payload;
                const extra = formatTooltipExtra && row ? formatTooltipExtra(row) : undefined;
                const label = extra ? `${valueLabel} · ${extra}` : valueLabel;
                return [fmtTip(Number(value)), label];
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2.5}
              dot={{ fill: color, strokeWidth: 2, r: 4, stroke: "#fff" }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export default React.memo(MonthlyLineChart);
