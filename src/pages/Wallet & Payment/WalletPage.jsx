// src/pages/Wallet & Payment/WalletPage.jsx

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import DeferredMonthlyLineChart from "../../components/charts/DeferredMonthlyLineChart";
import UserPageHeader from "../../components/UserPageHeader";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import { emptyMonthlySeries, walletTransactionsToMonthly } from "../../utils/apiCharts";
import {
  formatAxisMoneyShort,
  formatChartMoney,
  formatMoney,
  resolveLocale,
} from "../../utils/formatNumbers";
import "./WalletPage.css";

/** Shown in the wallet transaction table for every row (after excluding Recharge). */
const WALLET_TX_DISPLAY_AMOUNT_EGP = 10;

function readHeaderUser() {
  try {
    return {
      name: localStorage.getItem("userName") || "",
      fleetId: localStorage.getItem("fleetId") || "",
    };
  } catch {
    return { name: "", fleetId: "" };
  }
}

function WalletPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [dateRange, setDateRange] = useState("");
  const [transactionType, setTransactionType] = useState("All Types");
  const [walletPayload, setWalletPayload] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoadError("");
    try {
      const { data } = await API.get(ENDPOINTS.WALLET);
      setWalletPayload(data);
    } catch (e) {
      setLoadError(e.response?.data?.detail || e.message || i18n.t("wallet.loadError"));
    } finally {
      setLoading(false);
    }
  }, [i18n]);

  useEffect(() => {
    load();
  }, [load]);

  const walletUser = useMemo(() => readHeaderUser(), []);

  const walletBalance = useMemo(() => {
    const raw = walletPayload?.balance ?? "0";
    return parseFloat(String(raw), 10) || 0;
  }, [walletPayload]);

  const summary = useMemo(() => {
    const s = walletPayload?.summary || {};
    const paid = parseFloat(s.total_fares ?? 0, 10) || 0;
    const fines = parseFloat(s.total_fines ?? 0, 10) || 0;
    return {
      totalPaid: Math.abs(paid),
      totalFines: Math.abs(fines),
    };
  }, [walletPayload]);

  const transactions = useMemo(() => walletPayload?.transactions || [], [walletPayload]);

  const transactionsWithoutRecharge = useMemo(
    () => transactions.filter((tx) => tx.type !== "Recharge"),
    [transactions],
  );

  const filteredTransactions = useMemo(() => {
    return transactionsWithoutRecharge.filter((tx) => {
      if (transactionType !== "All Types" && tx.type !== transactionType) return false;
      if (dateRange) {
        const day = (tx.date || "").slice(0, 10);
        if (day && day !== dateRange) return false;
      }
      return true;
    });
  }, [transactionsWithoutRecharge, transactionType, dateRange]);

  const chartData = useMemo(() => {
    if (!transactionsWithoutRecharge.length) return emptyMonthlySeries();
    const normalized = transactionsWithoutRecharge.map((tx) => ({
      ...tx,
      amount: WALLET_TX_DISPLAY_AMOUNT_EGP,
    }));
    return walletTransactionsToMonthly(normalized);
  }, [transactionsWithoutRecharge]);

  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");

  const formatTooltipValue = useCallback((v) => formatChartMoney(v, loc), [loc]);
  const formatYAxis = useCallback((v) => formatAxisMoneyShort(v, loc), [loc]);

  const handleRecharge = () => {
    navigate("/dashboard/wallet/recharge");
  };

  if (loading) {
    return (
      <main className="wallet-main-content">
        <p className="glass-panel" style={{ padding: 24 }}>
          {t("common.processing")}
        </p>
      </main>
    );
  }

  return (
    <main className="wallet-main-content">
      <UserPageHeader
        title={t("wallet.title")}
        subtitle={t("wallet.subtitle")}
        user={walletUser}
        showFleetId={false}
      />

      {loadError ? (
        <p className="signup-form-error" style={{ marginBottom: 16 }} role="alert">
          {loadError}
        </p>
      ) : null}

      <div className="wallet-page-bento">
        <div className="wallet-page-bento__main">
          <section className="wallet-balance-card">
            <div className="wallet-balance-content">
              <h3 className="wallet-balance-title">{t("wallet.balanceTitle")}</h3>
              <p className="wallet-balance-value numeric-display">
                {formatMoney(walletBalance, loc, egp)}
              </p>
              <p className="wallet-balance-subtitle">{t("common.availableBalance")}</p>
            </div>
            <button type="button" className="wallet-recharge-btn" onClick={handleRecharge}>
              {t("wallet.recharge")}
            </button>
          </section>

          <DeferredMonthlyLineChart
            title={t("wallet.chartTitle")}
            data={chartData}
            valueLabel={egp}
            color="#007fff"
            formatTooltipValue={formatTooltipValue}
            formatYAxis={formatYAxis}
          />

          <section className="wallet-transactions-card">
            <h3 className="wallet-card-title">{t("wallet.recentTx")}</h3>
            <div className="wallet-transactions-table-wrap">
              <table className="wallet-transactions-table">
                <thead>
                  <tr>
                    <th>{t("wallet.thDate")}</th>
                    <th>{t("wallet.thType")}</th>
                    <th>{t("wallet.thAmount")}</th>
                    <th>{t("wallet.thSource")}</th>
                    <th>{t("wallet.thStatus")}</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTransactions.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: "center", padding: "20px", opacity: 0.85 }}>
                        {t("wallet.noTx")}
                      </td>
                    </tr>
                  ) : (
                    filteredTransactions.map((tx) => {
                      const d = new Date(tx.date);
                      const dateStr = Number.isNaN(d.getTime())
                        ? tx.date
                        : d.toLocaleDateString(loc, { year: "numeric", month: "short", day: "numeric" });
                      return (
                        <tr key={tx.id}>
                          <td>{dateStr}</td>
                          <td>
                            {tx.type === "Fare"
                              ? t("common.fare")
                              : tx.type === "Fine"
                                ? t("common.fine")
                                : tx.type}
                          </td>
                          <td className="wallet-amount-positive numeric-display">
                            {formatMoney(WALLET_TX_DISPLAY_AMOUNT_EGP, loc, egp)}
                          </td>
                          <td>{tx.source}</td>
                          <td>
                            <span className="wallet-status-badge wallet-status-completed">
                              {t("common.completed")}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside className="wallet-page-bento__rail" aria-label="Filters and summary">
          <div className="wallet-rail-stack">
            <section className="wallet-filters-card">
              <h3 className="wallet-card-title">{t("wallet.filtersTitle")}</h3>
              <div className="wallet-filters-row">
                <div className="wallet-filter-group">
                  <label htmlFor="date-range">{t("wallet.dateRange")}</label>
                  <input
                    id="date-range"
                    type="date"
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="wallet-input wallet-input-date"
                  />
                </div>
                <div className="wallet-filter-group">
                  <label htmlFor="transaction-type">{t("wallet.txType")}</label>
                  <select
                    id="transaction-type"
                    value={transactionType}
                    onChange={(e) => setTransactionType(e.target.value)}
                    className="wallet-select"
                  >
                    <option value="All Types">{t("common.allTypes")}</option>
                    <option value="Fare">{t("common.fare")}</option>
                    <option value="Fine">{t("common.fine")}</option>
                  </select>
                </div>
              </div>
            </section>

            <section className="wallet-summary-card">
              <h3 className="wallet-card-title">{t("wallet.summaryTitle")}</h3>
              <div className="wallet-summary-row">
                <span className="wallet-summary-label">{t("wallet.totalPaid")}</span>
                <span className="wallet-summary-value wallet-summary-paid numeric-display">
                  {formatMoney(summary.totalPaid, loc, egp)}
                </span>
              </div>
              <div className="wallet-summary-row">
                <span className="wallet-summary-label">{t("wallet.totalFines")}</span>
                <span className="wallet-summary-value wallet-summary-fines numeric-display">
                  {formatMoney(summary.totalFines, loc, egp)}
                </span>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </main>
  );
}

export default WalletPage;
