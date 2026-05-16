// src/pages/Dashboard/AdminDashboard.jsx

import React, { useState, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Wallet,
  Car,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./AdminDashboard.css";
import { formatMoney, resolveLocale } from "../../utils/formatNumbers";

const MONTH_META = Array.from({ length: 12 }, (_, i) => ({ index: i + 1 }));

const ALL_MONTH_INDICES = MONTH_META.map((m) => m.index);

const MONTH_PRESETS = [
  { id: "all", months: ALL_MONTH_INDICES },
  { id: "h1", months: [1, 2, 3, 4, 5, 6] },
  { id: "h2", months: [7, 8, 9, 10, 11, 12] },
  { id: "q1", months: [1, 2, 3] },
  { id: "q2", months: [4, 5, 6] },
  { id: "q3", months: [7, 8, 9] },
  { id: "q4", months: [10, 11, 12] },
];

/** Mock monthly trips count + wallet activity (EGP) — same months, shared filter */
const MOCK_TRIPS_WALLET_BY_MONTH = [
  { monthIndex: 1, trips: 118, wallet: 98200 },
  { monthIndex: 2, trips: 105, wallet: 87600 },
  { monthIndex: 3, trips: 132, wallet: 104500 },
  { monthIndex: 4, trips: 128, wallet: 101200 },
  { monthIndex: 5, trips: 141, wallet: 112800 },
  { monthIndex: 6, trips: 156, wallet: 118400 },
  { monthIndex: 7, trips: 162, wallet: 121900 },
  { monthIndex: 8, trips: 149, wallet: 115600 },
  { monthIndex: 9, trips: 138, wallet: 108300 },
  { monthIndex: 10, trips: 151, wallet: 119700 },
  { monthIndex: 11, trips: 144, wallet: 114200 },
  { monthIndex: 12, trips: 168, wallet: 128500 },
];

const ALERT_KEYS = ["al1", "al2"];

function selectionRecordFromMonths(activeMonths) {
  const set = new Set(activeMonths);
  return Object.fromEntries(ALL_MONTH_INDICES.map((i) => [i, set.has(i)]));
}

function countSelected(record) {
  return ALL_MONTH_INDICES.filter((i) => record[i]).length;
}

function AdminDashboard() {
  const { t, i18n } = useTranslation();
  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");
  const fmtMoney = (n) => formatMoney(n, loc, egp);
  const [monthSelection, setMonthSelection] = useState(() =>
    selectionRecordFromMonths(ALL_MONTH_INDICES),
  );
  const [activePresetId, setActivePresetId] = useState("all");

  const filteredTrendData = useMemo(() => {
    return MOCK_TRIPS_WALLET_BY_MONTH.filter((d) => monthSelection[d.monthIndex])
      .sort((a, b) => a.monthIndex - b.monthIndex)
      .map((d) => ({
        ...d,
        month: t(`adminDashboard.monthShort.${d.monthIndex}`),
      }));
  }, [monthSelection, t]);

  const toggleMonth = useCallback((monthIndex) => {
    setActivePresetId(null);
    setMonthSelection((prev) => {
      if (prev[monthIndex] && countSelected(prev) <= 1) {
        return prev;
      }
      return { ...prev, [monthIndex]: !prev[monthIndex] };
    });
  }, []);

  const applyPreset = useCallback((preset) => {
    setActivePresetId(preset.id);
    setMonthSelection(selectionRecordFromMonths(preset.months));
  }, []);
  // Mock dashboard stats
  const stats = {
    walletBalance: 1247.5,
    totalTrips: 142,
    activeViolations: 3,
    violationsFines: 450,
    monthlyRevenue: 2847,
  };

  // Mock recent trips
  const recentTrips = [
    {
      id: "rt-1",
      vehicle: "NYC-4521",
      timeKey: "rt1",
      fare: 24.5,
      status: "Completed",
    },
    {
      id: "rt-2",
      vehicle: "NYC-4521",
      timeKey: "rt2",
      fare: 18.75,
      status: "Violation",
    },
    {
      id: "rt-3",
      vehicle: "NYC-7834",
      timeKey: "rt3",
      fare: 31.2,
      status: "Completed",
    },
    {
      id: "rt-4",
      vehicle: "NYC-2201",
      timeKey: "rt4",
      fare: 19.0,
      status: "Completed",
    },
  ];

  return (
      <main className="admin-main-content">
        <header className="admin-page-header">
          <div className="admin-page-title-card">
            <h1>{t("adminDashboard.title")}</h1>
            <p>{t("adminDashboard.welcome")}</p>
          </div>
        </header>

        {/* Stats Cards */}
        <section className="admin-stats-section">
          <div className="admin-stat-card green">
            <div className="stat-header">
              <div>
                <p className="stat-label">{t("adminDashboard.walletBalance")}</p>
                <h2 className="stat-value">{fmtMoney(stats.walletBalance)}</h2>
              </div>
              <div className="stat-icon stat-icon--lucide green-bg" aria-hidden>
                <Wallet size={22} strokeWidth={1.75} />
              </div>
            </div>
          </div>

          <div className="admin-stat-card blue">
            <div className="stat-header">
              <div>
                <p className="stat-label">{t("adminDashboard.totalTrips")}</p>
                <h2 className="stat-value">{stats.totalTrips}</h2>
              </div>
              <div className="stat-icon stat-icon--lucide blue-bg" aria-hidden>
                <Car size={22} strokeWidth={1.75} />
              </div>
            </div>
            <div className="stat-footer">
              <span className="stat-trend positive">{t("adminDashboard.tripsChange")}</span>
            </div>
          </div>

          <div className="admin-stat-card red">
            <div className="stat-header">
              <div>
                <p className="stat-label">{t("adminDashboard.activeViolations")}</p>
                <h2 className="stat-value">{stats.activeViolations}</h2>
              </div>
              <div className="stat-icon stat-icon--lucide red-bg" aria-hidden>
                <AlertTriangle size={22} strokeWidth={1.75} />
              </div>
            </div>
            <div className="stat-footer">
              <span className="violations-fine">
                {t("adminDashboard.payFines", { amount: stats.violationsFines })}
              </span>
            </div>
          </div>

          <div className="admin-stat-card yellow">
            <div className="stat-header">
              <div>
                <p className="stat-label">{t("adminDashboard.thisMonth")}</p>
                <h2 className="stat-value">{fmtMoney(stats.monthlyRevenue)}</h2>
              </div>
              <div className="stat-icon stat-icon--lucide yellow-bg" aria-hidden>
                <TrendingUp size={22} strokeWidth={1.75} />
              </div>
            </div>
            <div className="stat-footer">
              <span className="stat-note">{t("adminDashboard.revenueNote")}</span>
            </div>
          </div>
        </section>

        {/* Trips & wallet — shared month filter, two line charts */}
        <section className="admin-trends-section" aria-labelledby="admin-trends-heading">
          <div className="admin-trends-filter-card admin-card">
            <div className="admin-trends-filter-head">
              <div>
                <h2 id="admin-trends-heading" className="admin-trends-title">
                  {t("adminDashboard.trendsTitle")}
                </h2>
                <p className="admin-trends-subtitle">{t("adminDashboard.trendsSubtitle")}</p>
              </div>
            </div>
            <div
              className="admin-trends-presets"
              role="toolbar"
              aria-label={t("adminWallet.monthPresetsToolbar")}
            >
              {MONTH_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className={`admin-trends-preset ${activePresetId === preset.id ? "admin-trends-preset--active" : ""}`}
                  onClick={() => applyPreset(preset)}
                >
                  {t(`adminDashboard.monthPreset.${preset.id}`)}
                </button>
              ))}
            </div>
            <div className="admin-trends-month-block">
              <span className="admin-trends-month-label">{t("common.months")}</span>
              <div className="admin-trends-month-chips" role="group" aria-label={t("adminWallet.toggleMonths")}>
                {MONTH_META.map(({ index }) => {
                  const on = monthSelection[index];
                  return (
                    <button
                      key={index}
                      type="button"
                      className={`admin-trends-chip ${on ? "admin-trends-chip--on" : ""}`}
                      onClick={() => toggleMonth(index)}
                      aria-pressed={on}
                    >
                      {t(`adminDashboard.monthShort.${index}`)}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="admin-trends-charts-grid">
            <div className="admin-card admin-trend-chart-card">
              <h3 className="admin-trend-chart-title">{t("adminDashboard.chartTripsTitle")}</h3>
              <p className="admin-trend-chart-desc">{t("adminDashboard.chartTripsDesc")}</p>
              <div className="admin-trend-chart-plot">
                {filteredTrendData.length === 0 ? (
                  <p className="admin-trend-chart-empty">{t("common.selectMonth")}</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={filteredTrendData} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 11, fill: "#64748b" }}
                        axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: "#64748b" }}
                        axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                        allowDecimals={false}
                      />
                      <Tooltip
                        formatter={(v) => [Number(v).toLocaleString(loc), t("common.trips")]}
                        contentStyle={{
                          borderRadius: "12px",
                          border: "1px solid rgba(148, 163, 184, 0.35)",
                          boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="trips"
                        stroke="#007fff"
                        strokeWidth={2.5}
                        dot={{ fill: "#007fff", strokeWidth: 2, r: 4, stroke: "#fff" }}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="admin-card admin-trend-chart-card">
              <h3 className="admin-trend-chart-title">{t("adminDashboard.chartWalletTitle")}</h3>
              <p className="admin-trend-chart-desc">{t("adminDashboard.chartWalletDesc")}</p>
              <div className="admin-trend-chart-plot">
                {filteredTrendData.length === 0 ? (
                  <p className="admin-trend-chart-empty">{t("common.selectMonth")}</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={filteredTrendData} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 11, fill: "#64748b" }}
                        axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                      />
                      <YAxis
                        tick={{ fontSize: 11, fill: "#64748b" }}
                        axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                        tickFormatter={(v) =>
                          t("adminDashboard.chartAxisThousands", { n: (v / 1000).toFixed(0) })
                        }
                      />
                      <Tooltip
                        formatter={(v) => [
                          `${Number(v).toLocaleString(loc)} ${t("common.egp")}`,
                          t("adminDashboard.chartRevenueSeries"),
                        ]}
                        contentStyle={{
                          borderRadius: "12px",
                          border: "1px solid rgba(148, 163, 184, 0.35)",
                          boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="wallet"
                        stroke="#059669"
                        strokeWidth={2.5}
                        dot={{ fill: "#059669", strokeWidth: 2, r: 4, stroke: "#fff" }}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Content Grid */}
        <section className="admin-content-section">
          {/* Recent Trips */}
          <div className="admin-card">
            <h3 className="card-title">{t("adminDashboard.recentTrips")}</h3>
            <div className="admin-trips-list">
              {recentTrips.map((trip) => (
                <div key={trip.id} className="admin-trip-item">
                  <div className="trip-icon trip-icon--lucide" aria-hidden>
                    <Car size={20} strokeWidth={1.75} />
                  </div>
                  <div className="trip-details">
                    <h4>{trip.vehicle}</h4>
                    <p>{t(`adminDashboard.tripTimes.${trip.timeKey}`)}</p>
                  </div>
                  <div className="trip-fare">{fmtMoney(trip.fare)}</div>
                  <span className={`trip-status ${trip.status.toLowerCase()}`}>
                    {trip.status === "Completed"
                      ? t("common.completed")
                      : trip.status === "Violation"
                        ? t("common.violation")
                        : trip.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="admin-card">
            <h3 className="card-title">{t("adminDashboard.activeAlerts")}</h3>
            <div className="admin-alerts-list">
              {ALERT_KEYS.map((alertKey) => (
                <div key={alertKey} className="admin-alert-item alert-error">
                  <div className="alert-icon alert-icon--lucide" aria-hidden>
                    <AlertTriangle size={20} strokeWidth={1.75} />
                  </div>
                  <div className="alert-content">
                    <h4>{t(`adminDashboard.alertsMock.${alertKey}.title`)}</h4>
                    <p>{t(`adminDashboard.alertsMock.${alertKey}.message`)}</p>
                    <span className="alert-time">
                      {t(`adminDashboard.alertsMock.${alertKey}.time`)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
  );
}

export default AdminDashboard;
