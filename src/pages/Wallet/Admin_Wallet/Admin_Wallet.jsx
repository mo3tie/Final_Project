// src/pages/Wallet/Admin_Wallet/Admin_Wallet.jsx

import React, { useState, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  Search,
  Landmark,
  Wallet,
  AlertTriangle,
  CreditCard,
  LineChart as LineChartIcon,
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
import "../../Wallet & Payment/WalletPage.css";
import "./Admin_Wallet.css";
import UserPageHeader from "../../../components/UserPageHeader";
import { formatMoney, resolveLocale } from "../../../utils/formatNumbers";

const ADMIN_HEADER_USER = { name: "System Admin", fleetId: "" };

const MONTH_META = [
  { index: 1, short: "Jan" },
  { index: 2, short: "Feb" },
  { index: 3, short: "Mar" },
  { index: 4, short: "Apr" },
  { index: 5, short: "May" },
  { index: 6, short: "Jun" },
  { index: 7, short: "Jul" },
  { index: 8, short: "Aug" },
  { index: 9, short: "Sep" },
  { index: 10, short: "Oct" },
  { index: 11, short: "Nov" },
  { index: 12, short: "Dec" },
];

/** Mock monthly revenue (EGP) for the current reporting year */
const MOCK_MONTHLY_REVENUE = [
  { monthIndex: 1, month: "Jan", revenue: 72400 },
  { monthIndex: 2, month: "Feb", revenue: 68900 },
  { monthIndex: 3, month: "Mar", revenue: 91800 },
  { monthIndex: 4, month: "Apr", revenue: 87200 },
  { monthIndex: 5, month: "May", revenue: 95100 },
  { monthIndex: 6, month: "Jun", revenue: 102400 },
  { monthIndex: 7, month: "Jul", revenue: 108800 },
  { monthIndex: 8, month: "Aug", revenue: 104200 },
  { monthIndex: 9, month: "Sep", revenue: 99100 },
  { monthIndex: 10, month: "Oct", revenue: 113500 },
  { monthIndex: 11, month: "Nov", revenue: 106700 },
  { monthIndex: 12, month: "Dec", revenue: 124200 },
];

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

function selectionRecordFromMonths(activeMonths) {
  const set = new Set(activeMonths);
  return Object.fromEntries(ALL_MONTH_INDICES.map((i) => [i, set.has(i)]));
}

function countSelected(record) {
  return ALL_MONTH_INDICES.filter((i) => record[i]).length;
}

function Admin_Wallet() {
  const { t, i18n } = useTranslation();
  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");
  const fmtMoney = (n) => formatMoney(n, loc, egp);
  const [searchQuery, setSearchQuery] = useState("");
  const [transactionFilter, setTransactionFilter] = useState("all");
  const [monthSelection, setMonthSelection] = useState(() =>
    selectionRecordFromMonths(ALL_MONTH_INDICES),
  );
  const [activePresetId, setActivePresetId] = useState("all");

  const lineChartData = useMemo(() => {
    return MOCK_MONTHLY_REVENUE.filter((d) => monthSelection[d.monthIndex]).sort(
      (a, b) => a.monthIndex - b.monthIndex,
    );
  }, [monthSelection]);

  const filteredRevenueTotal = useMemo(
    () => lineChartData.reduce((sum, d) => sum + d.revenue, 0),
    [lineChartData],
  );

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

  const stats = {
    totalLiquidity: 158450,
    totalRevenue: 1250000,
    revenueChange: "+12.5%",
    totalUnpaidFines: 32450,
  };

  const transactions = [
    {
      id: 1,
      date: "Oct 25, 2024",
      userId: "USR-10001",
      userName: "Administrator",
      plate: "ABC-123",
      type: "Toll Fee",
      amount: 25.5,
      method: "Wallet",
      status: "Paid",
    },
    {
      id: 3,
      date: "Oct 24, 2024",
      userId: "USR-10442",
      userName: "Ahmed Hassan",
      plate: "DEF-456",
      type: "Fine",
      amount: 150,
      method: "Wallet",
      status: "Paid",
    },
    {
      id: 4,
      date: "Oct 24, 2024",
      userId: "SYS-900",
      userName: "Fleet Pool",
      plate: "—",
      type: "Toll Fee",
      amount: 875,
      method: "Wallet",
      status: "Paid",
    },
    {
      id: 5,
      date: "Oct 23, 2024",
      userId: "USR-10888",
      userName: "Omar Ali",
      plate: "JKL-012",
      type: "Fine",
      amount: 220,
      method: "Visa *5678",
      status: "Paid",
    },
    {
      id: 6,
      date: "Oct 23, 2024",
      userId: "USR-10210",
      userName: "Mary Ali",
      plate: "XYZ-789",
      type: "Toll Fee",
      amount: 20,
      method: "Wallet",
      status: "Paid",
    },
  ];

  const filteredTransactions = transactions.filter((tx) => {
    const q = searchQuery.trim().toLowerCase();
    const matchesSearch =
      !q ||
      tx.userId.toLowerCase().includes(q) ||
      tx.plate.toLowerCase().includes(q) ||
      tx.userName.toLowerCase().includes(q);
    const matchesType =
      transactionFilter === "all"
        ? true
        : transactionFilter === "fines"
        ? tx.type.toLowerCase() === "fine"
        : transactionFilter === "tolls"
        ? tx.type.toLowerCase() === "toll fee"
        : true;
    return matchesSearch && matchesType;
  });

  return (
      <main className="wallet-main-content admin-wallet-main">
        <div className="admin-wallet-header">
          <UserPageHeader
            title={t("adminWallet.title")}
            subtitle={t("adminWallet.subtitle")}
            user={ADMIN_HEADER_USER}
            showFleetId={false}
            profilePath="/admin/dashboard"
          />
        </div>

        {/* Top Stats */}
        <section className="admin-wallet-stats">
          {/* Blue main banner */}
          <div className="admin-wallet-card admin-wallet-card-primary">
            <div>
              <p className="admin-wallet-card-label">{t("adminWallet.liquidity")}</p>
              <h2 className="admin-wallet-card-value">{fmtMoney(stats.totalLiquidity)}</h2>
              <p className="admin-wallet-card-sub">{t("adminWallet.liquiditySub")}</p>
            </div>
            <div className="admin-wallet-card-icon" aria-hidden>
              <Landmark size={30} strokeWidth={1.65} />
            </div>
          </div>

          {/* Total Revenue */}
          <div className="admin-wallet-card admin-wallet-card-green">
            <div className="admin-wallet-stat-icon admin-wallet-stat-icon-green" aria-hidden>
              <Wallet size={24} strokeWidth={1.75} />
            </div>
            <div>
              <p className="admin-wallet-card-label">{t("adminWallet.revenue")}</p>
              <h3 className="admin-wallet-card-value-sm">{fmtMoney(stats.totalRevenue)}</h3>
              <p className="admin-wallet-card-sub positive">
                {stats.revenueChange} vs last period
              </p>
            </div>
          </div>

          {/* Total Unpaid Fines */}
          <div className="admin-wallet-card admin-wallet-card-red">
            <div className="admin-wallet-stat-icon admin-wallet-stat-icon-red" aria-hidden>
              <AlertTriangle size={24} strokeWidth={1.75} />
            </div>
            <div>
              <p className="admin-wallet-card-label">{t("adminWallet.unpaidFines")}</p>
              <h3 className="admin-wallet-card-value-sm">{fmtMoney(stats.totalUnpaidFines)}</h3>
              <p className="admin-wallet-card-sub">{t("adminWallet.unpaidFinesSub")}</p>
            </div>
          </div>
        </section>

        {/* Monthly revenue — line chart + month filter */}
        <section className="admin-wallet-revenue-section" aria-labelledby="admin-wallet-revenue-heading">
          <div className="admin-wallet-revenue-head">
            <div className="admin-wallet-revenue-head-text">
              <div className="admin-wallet-revenue-title-row">
                <span className="admin-wallet-revenue-icon" aria-hidden>
                  <LineChartIcon size={22} strokeWidth={1.75} />
                </span>
                <h2 id="admin-wallet-revenue-heading">{t("adminWallet.monthlyRevenue")}</h2>
              </div>
              <p className="admin-wallet-revenue-desc">{t("adminWallet.monthlyRevenueDesc")}</p>
            </div>
            <div className="admin-wallet-revenue-summary">
              <span className="admin-wallet-revenue-summary-label">{t("adminWallet.selectedTotal")}</span>
              <strong className="admin-wallet-revenue-summary-value">
                {fmtMoney(filteredRevenueTotal)}
              </strong>
              <span className="admin-wallet-revenue-summary-meta">
                {t("adminWallet.monthsOnChart", { count: lineChartData.length })}
              </span>
            </div>
          </div>

          <div
            className="admin-wallet-month-presets"
            role="toolbar"
            aria-label={t("adminWallet.monthPresetsToolbar")}
          >
            {MONTH_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className={`admin-wallet-preset-btn ${activePresetId === preset.id ? "admin-wallet-preset-btn--active" : ""}`}
                onClick={() => applyPreset(preset)}
              >
                {t(`adminWallet.monthPreset.${preset.id}`)}
              </button>
            ))}
          </div>

          <div className="admin-wallet-month-filter-block">
            <span className="admin-wallet-month-filter-label">{t("adminWallet.monthsInChart")}</span>
            <div className="admin-wallet-month-chips" role="group" aria-label={t("adminWallet.toggleMonths")}>
              {MONTH_META.map(({ index, short }) => {
                const on = monthSelection[index];
                return (
                  <button
                    key={index}
                    type="button"
                    className={`admin-wallet-month-chip ${on ? "admin-wallet-month-chip--on" : ""}`}
                    onClick={() => toggleMonth(index)}
                    aria-pressed={on}
                  >
                    {short}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="admin-wallet-line-chart-wrap">
            {lineChartData.length === 0 ? (
              <p className="admin-wallet-line-chart-empty">{t("adminWallet.chartEmpty")}</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={lineChartData}
                  margin={{ top: 12, right: 16, left: 4, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={{ stroke: "rgba(148, 163, 184, 0.5)" }}
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(value) => [
                      `${Number(value).toLocaleString()} ${t("common.egp")}`,
                      t("adminWallet.tooltipRevenue"),
                    ]}
                    labelFormatter={(label) => t("adminWallet.monthTooltip", { label })}
                    contentStyle={{
                      borderRadius: "12px",
                      border: "1px solid rgba(148, 163, 184, 0.35)",
                      boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name={t("adminWallet.tooltipRevenue")}
                    stroke="#007fff"
                    strokeWidth={2.75}
                    dot={{ fill: "#007fff", strokeWidth: 2, r: 5, stroke: "#fff" }}
                    activeDot={{ r: 7, strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        {/* Filters & Search */}
        <section className="admin-wallet-filters">
          <div className="admin-wallet-search-group">
            <label htmlFor="admin-wallet-search" className="admin-wallet-filter-label">
              {t("adminWallet.searchLabel")}
            </label>
            <div className="admin-wallet-search-wrapper">
              <Search className="admin-wallet-search-icon" size={18} strokeWidth={1.75} />
              <input
                id="admin-wallet-search"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t("adminWallet.searchPlaceholder")}
                className="admin-wallet-search-input"
              />
            </div>
          </div>

          <div className="admin-wallet-filter-group">
            <label
              htmlFor="admin-wallet-transaction-type"
              className="admin-wallet-filter-label"
            >
              {t("adminWallet.txTypeLabel")}
            </label>
            <select
              id="admin-wallet-transaction-type"
              value={transactionFilter}
              onChange={(e) => setTransactionFilter(e.target.value)}
              className="admin-wallet-select"
            >
              <option value="all">{t("adminWallet.filterAll")}</option>
              <option value="tolls">{t("adminWallet.filterTolls")}</option>
              <option value="fines">{t("adminWallet.filterFines")}</option>
            </select>
          </div>
        </section>

        {/* Transactions Table */}
        <section className="admin-wallet-table-section">
          <div className="admin-wallet-table-wrapper">
            <table className="admin-wallet-table">
              <thead>
                <tr>
                  <th>{t("adminWallet.thDate")}</th>
                  <th>{t("adminWallet.thUser")}</th>
                  <th>{t("adminWallet.thPlate")}</th>
                  <th>{t("adminWallet.thAmount")}</th>
                  <th>{t("adminWallet.thMethod")}</th>
                  <th>{t("adminWallet.thStatus")}</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((tx) => (
                  <tr key={tx.id}>
                    <td>{tx.date}</td>
                    <td className="admin-wallet-user-cell">
                      <span className="admin-wallet-user-name">{tx.userName}</span>
                      <span className="admin-wallet-user-id">{tx.userId}</span>
                    </td>
                    <td className="admin-wallet-plate-cell">{tx.plate}</td>
                    <td className="admin-wallet-amount-cell">{fmtMoney(tx.amount)}</td>
                    <td>
                      <span className="admin-wallet-method">
                        {tx.method.includes("Visa") ? (
                          <>
                            <CreditCard size={16} strokeWidth={1.75} aria-hidden /> {tx.method}
                          </>
                        ) : (
                          <>
                            <Wallet size={16} strokeWidth={1.75} aria-hidden /> {tx.method}
                          </>
                        )}
                      </span>
                    </td>
                    <td>
                      <span className="admin-wallet-status-badge admin-wallet-status-paid">
                        {tx.status === "Paid" ? t("common.paid") : tx.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
  );
}

export default Admin_Wallet;

