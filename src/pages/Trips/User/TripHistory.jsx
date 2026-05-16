// src/pages/Trips/User/TripHistory.jsx

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Calendar, Car, Wallet, AlertTriangle, ChevronLeft, ChevronRight, MapPin } from "lucide-react";
import DeferredMonthlyLineChart from "../../../components/charts/DeferredMonthlyLineChart";
import { EGYPT_GOVERNORATES } from "../../../data/egyptGovernorates";
import UserPageHeader from "../../../components/UserPageHeader";
import API from "../../../APi/axiosConfig";
import { ENDPOINTS } from "../../../APi/endpoints";
import { emptyMonthlySeries, tripsToMonthlyCounts } from "../../../utils/apiCharts";
import {
  formatChartCount,
  formatCount,
  formatMoney,
  resolveLocale,
} from "../../../utils/formatNumbers";
import "./TripHistory.css";
import "../../../components/charts/MonthlyLineChart.css";

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

function TripHistory() {
  const { t, i18n } = useTranslation();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [governorate, setGovernorate] = useState("");
  const [appliedFrom, setAppliedFrom] = useState("");
  const [appliedTo, setAppliedTo] = useState("");
  const [appliedGov, setAppliedGov] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const [tripPayload, setTripPayload] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const params = {};
      if (appliedFrom) params.from = appliedFrom;
      if (appliedTo) params.to = appliedTo;
      if (appliedGov) params.governorate = appliedGov;
      const { data } = await API.get(ENDPOINTS.TRIPS, { params });
      setTripPayload(data);
    } catch (e) {
      setLoadError(e.response?.data?.detail || e.message || i18n.t("trips.loadError"));
    } finally {
      setLoading(false);
    }
  }, [appliedFrom, appliedTo, appliedGov, i18n]);

  useEffect(() => {
    load();
  }, [load]);

  const tripPageUser = useMemo(() => readHeaderUser(), []);

  const stats = useMemo(() => {
    const s = tripPayload?.stats || {};
    return {
      totalTrips: Number(s.totalTrips ?? 0),
      totalFarePaid: Number(s.totalFarePaid ?? 0),
      totalViolations: Number(s.totalViolations ?? 0),
    };
  }, [tripPayload]);

  const allTrips = useMemo(() => tripPayload?.trips || [], [tripPayload]);

  const chartData = useMemo(() => {
    if (!allTrips.length) return emptyMonthlySeries();
    return tripsToMonthlyCounts(allTrips);
  }, [allTrips]);

  const totalPages = Math.max(1, Math.ceil(allTrips.length / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentTrips = allTrips.slice(startIndex, startIndex + itemsPerPage);

  const handleApplyFilters = () => {
    setAppliedFrom(dateFrom);
    setAppliedTo(dateTo);
    setAppliedGov(governorate);
    setCurrentPage(1);
  };

  const handleResetFilters = () => {
    setDateFrom("");
    setDateTo("");
    setGovernorate("");
    setAppliedFrom("");
    setAppliedTo("");
    setAppliedGov("");
    setCurrentPage(1);
  };

  useEffect(() => {
    const tp = Math.max(1, Math.ceil(allTrips.length / itemsPerPage) || 1);
    setCurrentPage((p) => Math.min(p, tp));
  }, [allTrips.length]);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");

  const formatTooltipValue = useCallback((v) => formatChartCount(v, loc), [loc]);
  const formatYAxis = useCallback((v) => formatChartCount(v, loc), [loc]);
  const formatTooltipExtra = useCallback(
    (row) => (row?.topCity ? `${t("trips.chartTooltipTopCity")}: ${row.topCity}` : undefined),
    [t],
  );

  if (loading && !tripPayload && !loadError) {
    return (
      <main className="wallet-main-content trip-history-page">
        <p className="glass-panel" style={{ padding: 24 }}>
          {t("common.processing")}
        </p>
      </main>
    );
  }

  return (
    <main className="wallet-main-content trip-history-page">
      <UserPageHeader
        title={t("Trips")}
        subtitle={t("Trips")}
        user={tripPageUser}
        showFleetId={false}
      />

      {loadError ? (
        <p className="signup-form-error" style={{ marginBottom: 16 }} role="alert">
          {loadError}
        </p>
      ) : null}

      <div className="trip-page-bento">
        <div className="trip-page-bento__main">
          <section className="trip-filter-section">
            <div className="trip-filter-row">
              <div className="trip-filter-group">
                <label htmlFor="date-from" className="trip-filter-label">
                  {t("trips.from")}
                </label>
                <div className="trip-date-input-wrapper">
                  <Calendar className="trip-date-icon" size={18} />
                  <input
                    id="date-from"
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="trip-date-input"
                  />
                </div>
              </div>
              <div className="trip-filter-group">
                <label htmlFor="date-to" className="trip-filter-label">
                  {t("trips.to")}
                </label>
                <div className="trip-date-input-wrapper">
                  <Calendar className="trip-date-icon" size={18} />
                  <input
                    id="date-to"
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="trip-date-input"
                  />
                </div>
              </div>
              <div className="trip-filter-group trip-filter-group--grow">
                <label htmlFor="trip-governorate" className="trip-filter-label">
                  {t("trips.governorate")}
                </label>
                <div className="trip-governorate-wrapper">
                  <MapPin className="trip-governorate-icon" size={18} />
                  <select
                    id="trip-governorate"
                    value={governorate}
                    onChange={(e) => setGovernorate(e.target.value)}
                    className="trip-governorate-select"
                  >
                    <option value="">{t("trips.allGov")}</option>
                    {EGYPT_GOVERNORATES.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="trip-filter-actions">
                <button type="button" className="trip-apply-btn" onClick={handleApplyFilters}>
                  {t("common.apply")}
                </button>
                <button type="button" className="trip-reset-btn" onClick={handleResetFilters}>
                  {t("common.reset")}
                </button>
              </div>
            </div>
          </section>

          <DeferredMonthlyLineChart
            title={t("trips.chartTitle")}
            data={chartData}
            valueLabel={t("common.trips")}
            color="#007fff"
            formatTooltipValue={formatTooltipValue}
            formatYAxis={formatYAxis}
            formatTooltipExtra={formatTooltipExtra}
          />

          <section className="trip-table-section">
            <div className="trip-table-wrapper">
              <table className="trip-table">
                <thead>
                  <tr>
                    <th>{t("trips.thTripId")}</th>
                    <th>{t("trips.thDateTime")}</th>
                    <th>{t("trips.thGov")}</th>
                    <th>{t("trips.thPlate")}</th>
                    <th>{t("trips.thRoute")}</th>
                    <th>{t("trips.thFare")}</th>
                    <th>{t("trips.thStatus")}</th>
                    <th>{t("trips.thViolation")}</th>
                  </tr>
                </thead>
                <tbody>
                  {currentTrips.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="trip-table-empty">
                        {t("trips.empty")}
                      </td>
                    </tr>
                  ) : (
                    currentTrips.map((trip) => (
                      <tr key={trip.id}>
                        <td className="trip-id-cell">{trip.id}</td>
                        <td>{trip.dateTime}</td>
                        <td>{trip.governorate}</td>
                        <td className="trip-vehicle-cell">{trip.vehiclePlate}</td>
                        <td>{trip.gateName}</td>
                        <td className="trip-fare-cell numeric-display">
                          {formatMoney(trip.fareAmount, loc, egp)}
                        </td>
                        <td>
                          <span
                            className={`trip-status-badge ${
                              trip.status === "Paid" ? "trip-status-paid" : "trip-status-not-paid"
                            }`}
                          >
                            {trip.status === "Paid" ? t("common.paid") : t("common.notPaid")}
                          </span>
                        </td>
                        <td className="trip-violation-cell numeric-display">
                          {trip.violationAmount > 0 ? formatMoney(trip.violationAmount, loc, egp) : "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <div className="trip-pagination">
            <button
              type="button"
              className="trip-pagination-btn"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft size={18} />
              {t("common.previous")}
            </button>
            <div className="trip-pagination-numbers">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  type="button"
                  className={`trip-pagination-number ${currentPage === page ? "trip-pagination-active" : ""}`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              ))}
            </div>
            <button
              type="button"
              className="trip-pagination-btn"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              {t("common.next")}
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        <aside className="trip-page-bento__rail" aria-label="Trip summary">
          <section className="trip-stats-section trip-stats-section--rail">
            <div className="trip-stat-card trip-stat-blue">
              <div className="trip-stat-icon-wrapper trip-stat-icon-blue">
                <Car className="trip-stat-icon" size={24} />
              </div>
              <div className="trip-stat-content">
                <p className="trip-stat-label">{t("trips.totalTrips")}</p>
                <h2 className="trip-stat-value numeric-display">{formatCount(stats.totalTrips, loc)}</h2>
              </div>
            </div>

            <div className="trip-stat-card trip-stat-green">
              <div className="trip-stat-icon-wrapper trip-stat-icon-green">
                <Wallet className="trip-stat-icon" size={24} />
              </div>
              <div className="trip-stat-content">
                <p className="trip-stat-label">{t("trips.totalFare")}</p>
                <h2 className="trip-stat-value numeric-display">{formatMoney(stats.totalFarePaid, loc, egp)}</h2>
              </div>
            </div>

            <div className="trip-stat-card trip-stat-red">
              <div className="trip-stat-icon-wrapper trip-stat-icon-red">
                <AlertTriangle className="trip-stat-icon" size={24} />
              </div>
              <div className="trip-stat-content">
                <p className="trip-stat-label">{t("trips.totalViolations")}</p>
                <h2 className="trip-stat-value numeric-display">{formatMoney(stats.totalViolations, loc, egp)}</h2>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}

export default TripHistory;
