// src/pages/Profile & settings/ProfilePage.jsx

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Mail,
  Phone,
  Edit,
  FileText,
  AlertTriangle,
  DollarSign,
  Car,
} from "lucide-react";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import { formatCount, formatMoney, resolveLocale } from "../../utils/formatNumbers";
import "./ProfilePage.css";

const PROFILE_AVATAR = (name) =>
  `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&size=128&background=007fff&color=fff&bold=true`;

function ProfilePage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [loadError, setLoadError] = useState("");

  const loadMe = useCallback(async () => {
    setLoadError("");
    try {
      const { data } = await API.get(ENDPOINTS.ME);
      setMe(data);
    } catch (e) {
      setLoadError(e.response?.data?.detail || e.message || t("dashboard.loadError"));
    }
  }, [t]);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const userData = useMemo(() => {
    if (!me) {
      return { name: "", email: "", phone: "", fleetId: "" };
    }
    return {
      name: me.name || "",
      email: me.email || "",
      phone: me.phone || "",
      fleetId: me.fleet_id || "",
    };
  }, [me]);

  const vehicles = useMemo(() => {
    const v = me?.vehicles || [];
    return v.map((x) => ({
      id: x.id,
      plate: x.plate,
      model: x.model,
      is_active: x.is_active,
      status: x.status || (x.is_active ? "Active" : "Inactive"),
    }));
  }, [me]);

  const quickStats = useMemo(() => {
    const s = me?.stats || {};
    return {
      totalTrips: Number(s.total_trips ?? 0),
      totalFines: Number(s.unpaid_violations ?? 0),
      totalFare: parseFloat(s.total_fare_paid ?? 0, 10) || 0,
    };
  }, [me]);

  const toggleVehicleStatus = async (vehicleId, currentlyActive) => {
    try {
      await API.patch(ENDPOINTS.VEHICLE(vehicleId), { is_active: !currentlyActive });
      await loadMe();
    } catch (e) {
      window.alert(e.response?.data?.detail || e.message || t("common.error"));
    }
  };

  const handleEditProfile = () => {
    navigate("/dashboard/profile/edit");
  };

  const avatarSrc =
    me?.photo_url && me.photo_url.length > 0 ? me.photo_url : PROFILE_AVATAR(userData.name);

  const loc = resolveLocale(i18n.language);
  const egp = t("common.egp");

  return (
    <main className="wallet-main-content profile-settings-page">
      {loadError ? (
        <p className="signup-form-error" style={{ marginBottom: 16 }} role="alert">
          {loadError}
        </p>
      ) : null}
      <header className="profile-page-header">
        <h1>{t("profile.settingsTitle")}</h1>
      </header>

      <section className="profile-user-card">
        <div className="profile-avatar-section">
          <img
            className="profile-avatar-img"
            src={avatarSrc}
            alt=""
            width={96}
            height={96}
            loading="lazy"
            referrerPolicy="no-referrer"
          />
          <div className="profile-avatar-actions" />
        </div>

        <div className="profile-user-details">
          <h2 className="profile-user-name">{userData.name || "—"}</h2>
          <div className="profile-contact-info">
            <div className="profile-contact-item">
              <Mail size={18} className="profile-contact-icon" />
              <span>{userData.email || "—"}</span>
            </div>
            <div className="profile-contact-item">
              <Phone size={18} className="profile-contact-icon" />
              <span>{userData.phone || "—"}</span>
            </div>
          </div>
        </div>

        <button type="button" className="profile-edit-btn" onClick={handleEditProfile}>
          <Edit size={18} aria-hidden />
          {t("profile.editProfile")}
        </button>
      </section>

      <div className="profile-content-bento">
        <section className="profile-vehicles-card">
          <div className="profile-vehicles-header">
            <h3 className="profile-card-title">{t("profile.linkedVehicles")}</h3>
            <button type="button" className="profile-add-vehicle-btn" onClick={() => navigate("/dashboard/profile/add-vehicle")}>
              + {t("profile.addVehicle")}
            </button>
          </div>
          <div className="profile-vehicles-grid">
            {vehicles.length === 0 ? (
              <p style={{ padding: "8px 4px", opacity: 0.85 }}>{t("profile.noVehicles")}</p>
            ) : (
              vehicles.map((vehicle) => (
                <div key={vehicle.id} className="profile-vehicle-card">
                  <div className="profile-vehicle-card-icon">
                    <Car size={32} strokeWidth={1.75} />
                  </div>
                  <div className="profile-vehicle-card-content">
                    <h4 className="profile-vehicle-card-plate">{vehicle.plate}</h4>
                    <p className="profile-vehicle-card-model">{vehicle.model}</p>
                  </div>
                  <button
                    type="button"
                    className={`profile-vehicle-card-status ${
                      vehicle.status === "Active"
                        ? "profile-vehicle-card-status-active"
                        : "profile-vehicle-card-status-inactive"
                    }`}
                    onClick={() => toggleVehicleStatus(vehicle.id, vehicle.is_active)}
                  >
                    {vehicle.status === "Active" ? t("common.active") : t("common.inactive")}
                  </button>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="profile-stats-card">
          <h3 className="profile-card-title">{t("profile.quickStats")}</h3>
          <div className="profile-stats-grid">
            <div className="profile-stat-item">
              <div className="profile-stat-icon-wrapper profile-stat-icon-blue">
                <FileText size={24} className="profile-stat-icon" />
              </div>
                <h3 className="profile-stat-value numeric-display">{formatCount(quickStats.totalTrips, loc)}</h3>
              <p className="profile-stat-label">{t("profile.totalTrips")}</p>
            </div>

            <div className="profile-stat-item">
              <div className="profile-stat-icon-wrapper profile-stat-icon-red">
                <AlertTriangle size={24} className="profile-stat-icon" />
              </div>
                <h3 className="profile-stat-value numeric-display">{formatCount(quickStats.totalFines, loc)}</h3>
              <p className="profile-stat-label">{t("profile.totalFines")}</p>
            </div>

            <div className="profile-stat-item">
              <div className="profile-stat-icon-wrapper profile-stat-icon-green">
                <DollarSign size={24} className="profile-stat-icon" />
              </div>
                <h3 className="profile-stat-value numeric-display">{formatMoney(quickStats.totalFare, loc, egp)}</h3>
              <p className="profile-stat-label">{t("profile.totalFare")}</p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default ProfilePage;
