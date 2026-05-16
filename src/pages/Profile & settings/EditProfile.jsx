// src/pages/Profile & settings/EditProfile.jsx

import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Mail,
  Phone,
  Eye,
  EyeOff,
  Car,
  Edit2,
  Trash2,
  Lock,
} from "lucide-react";
import UserPageHeader from "../../components/UserPageHeader";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import { syncSessionFromMe } from "../../utils/session";
import "./EditProfile.css";

/** Short badge label so the row fits without overlapping the model text */
function vehicleTypeShortLabel(type) {
  const map = {
    "Private Car": "Pri",
    Minibus: "Mi",
    Van: "Van",
    Truck: "Trk",
  };
  if (map[type]) return map[type];
  return type.length <= 4 ? type : `${type.slice(0, 3)}…`;
}

function avatarFromName(name) {
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name || "User")}&size=256&background=007fff&color=fff&bold=true`;
}

function formatProfileSaveError(data, fallback) {
  if (!data || typeof data !== "object") return fallback;
  if (typeof data.detail === "string" && data.detail) return data.detail;
  const nfe = data.non_field_errors;
  if (Array.isArray(nfe) && nfe[0]) return nfe[0];
  const keys = ["currentPassword", "email", "phone", "newPassword", "fullName"];
  for (const key of keys) {
    const v = data[key];
    if (Array.isArray(v) && v[0]) return v[0];
    if (typeof v === "string" && v) return v;
  }
  return fallback;
}

/** Egyptian local numbers often start with 0 after stripping +20; normalize to +20XXXXXXXXXX */
function buildPhonePayload(phone) {
  let digits = phone.replace(/\D/g, "");
  if (digits.length >= 11 && digits.startsWith("0")) {
    digits = digits.slice(1);
  }
  if (digits.length >= 10) return `+20${digits}`;
  return phone.trim();
}

function EditProfile() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [me, setMe] = useState(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [phone, setPhone] = useState("");

  const [vehicles, setVehicles] = useState([]);

  // Password verification
  const [verificationPassword, setVerificationPassword] = useState("");
  const [verificationStatus, setVerificationStatus] = useState(null); // 'success' | 'error' | null
  const [verificationMessage, setVerificationMessage] = useState("");
  const [passwordVerified, setPasswordVerified] = useState(false);

  const photoInputRef = useRef(null);
  const [photoObjectUrl, setPhotoObjectUrl] = useState(null);

  useEffect(() => {
    return () => {
      if (photoObjectUrl) URL.revokeObjectURL(photoObjectUrl);
    };
  }, [photoObjectUrl]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await API.get(ENDPOINTS.ME);
        if (cancelled) return;
        setMe(data);
        setFullName(data.name || "");
        setEmail(data.email || "");
        const p = (data.phone || "").replace(/^\s*\+?20\s*/i, "").trim();
        setPhone(p);
        setVehicles(
          (data.vehicles || []).map((v) => ({
            id: v.id,
            plate: v.plate,
            model: v.model,
            type: v.type || "Car",
          })),
        );
      } catch {
        if (!cancelled) navigate("/dashboard/profile");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  const displayPhoto =
    photoObjectUrl || (me?.photo_url && me.photo_url.length > 0 ? me.photo_url : avatarFromName(fullName));

  const handlePhotoChange = (event) => {
    const file = event.target.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;
    setPhotoObjectUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
  };

  const handleRemovePhoto = () => {
    setPhotoObjectUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    if (photoInputRef.current) photoInputRef.current.value = "";
  };

  const handleSaveChanges = async (event) => {
    event.preventDefault();
    if (!verificationPassword) {
      setVerificationStatus("error");
      setVerificationMessage(t("editProfile.needCurrentToSave"));
      return;
    }
    if (!passwordVerified) {
      setVerificationStatus("error");
      setVerificationMessage(t("editProfile.verifyBeforeSave"));
      return;
    }
    try {
      const phonePayload = buildPhonePayload(phone);
      const payload = {
        fullName: fullName.trim(),
        email: email.trim(),
        phone: phonePayload,
        currentPassword: verificationPassword,
      };
      if (password.trim()) payload.newPassword = password.trim();
      const { data } = await API.patch(ENDPOINTS.ME, payload);
      setMe(data);
      try {
        localStorage.setItem("userName", (data.name || fullName).trim());
        if (data.fleet_id != null && data.fleet_id !== undefined) {
          localStorage.setItem("fleetId", String(data.fleet_id));
        }
      } catch {
        /* ignore quota / private mode */
      }
      setPassword("");
      setVerificationPassword("");
      setPasswordVerified(false);
      setVerificationStatus("success");
      setVerificationMessage(t("editProfile.saveSuccess"));
    } catch (err) {
      const msg = formatProfileSaveError(err.response?.data, t("editProfile.saveFailed"));
      setVerificationStatus("error");
      setVerificationMessage(msg);
      setPasswordVerified(false);
    }
  };

  const handleCancel = () => {
    navigate("/dashboard/profile");
  };

  const handleEditVehicle = (_id) => {
    navigate("/dashboard/profile/add-vehicle");
  };

  const handleDeleteVehicle = async (id) => {
    if (!window.confirm(t("editProfile.confirmDeleteVehicle"))) return;
    try {
      await API.delete(ENDPOINTS.VEHICLE(id));
      const { data } = await API.get(ENDPOINTS.ME);
      syncSessionFromMe(data);
      setMe(data);
      setVehicles(
        (data.vehicles || []).map((v) => ({
          id: v.id,
          plate: v.plate,
          model: v.model,
          type: v.type || "Car",
        })),
      );
    } catch (e) {
      window.alert(e.response?.data?.detail || e.message || t("common.error"));
    }
  };

  const handleVerifyPassword = async () => {
    if (!verificationPassword) {
      setVerificationStatus("error");
      setVerificationMessage(t("editProfile.wrongPassword"));
      setPasswordVerified(false);
      return;
    }
    try {
      const { data } = await API.post(ENDPOINTS.VERIFY_PASSWORD, {
        password: verificationPassword,
      });
      if (data?.valid) {
        setVerificationStatus("success");
        setVerificationMessage(t("editProfile.correctPassword"));
        setPasswordVerified(true);
      } else {
        setVerificationStatus("error");
        setVerificationMessage(t("editProfile.wrongPassword"));
        setPasswordVerified(false);
      }
    } catch {
      setVerificationStatus("error");
      setVerificationMessage(t("editProfile.wrongPassword"));
      setPasswordVerified(false);
    }
  };

  return (
    <main className="wallet-main-content edit-profile-main">
      <UserPageHeader
        title={t("editProfile.title")}
        subtitle={t("editProfile.subtitle")}
        user={{ name: fullName, fleetId: me?.fleet_id || "" }}
      />

      <div className="edit-profile-grid">
        <section className="edit-profile-card edit-profile-card--primary-form">
          <h2 className="edit-profile-card-title">{t("editProfile.profileInfo")}</h2>
          <div className="edit-profile-photo-block">
            <div className="edit-profile-photo-preview">
              <img src={displayPhoto} alt="" width={112} height={112} loading="lazy" />
            </div>
            <div className="edit-profile-photo-actions">
              <button
                type="button"
                className="edit-profile-photo-btn edit-profile-photo-btn--primary"
                onClick={() => photoInputRef.current?.click()}
              >
                {t("editProfile.uploadPhoto")}
              </button>
              {photoObjectUrl ? (
                <button type="button" className="edit-profile-photo-btn" onClick={handleRemovePhoto}>
                  {t("editProfile.remove")}
                </button>
              ) : null}
            </div>
            <input
              ref={photoInputRef}
              type="file"
              accept="image/*"
              className="edit-profile-photo-input"
              onChange={handlePhotoChange}
              aria-label={t("editProfile.profilePicture")}
            />
          </div>
          <form className="edit-profile-form" onSubmit={handleSaveChanges}>
              <div className="edit-profile-field-group">
                <label htmlFor="full-name" className="edit-profile-label">
                  {t("editProfile.fullName")}
                </label>
                <div className="edit-profile-input-wrapper">
                  <input
                    id="full-name"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="edit-profile-input"
                    placeholder={t("editProfile.placeholders.fullName")}
                  />
                </div>
              </div>

              <div className="edit-profile-field-group">
                <label htmlFor="email" className="edit-profile-label">
                  {t("editProfile.email")}
                </label>
                <div className="edit-profile-input-wrapper">
                  <Mail className="edit-profile-input-icon" size={18} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="edit-profile-input edit-profile-input-with-icon"
                    placeholder={t("editProfile.placeholders.email")}
                  />
                </div>
              </div>

              <div className="edit-profile-field-group">
                <label htmlFor="new-password" className="edit-profile-label">
                  {t("editProfile.newPassword")}
                </label>
                <div className="edit-profile-input-wrapper">
                  <Lock className="edit-profile-input-icon" size={18} />
                  <input
                    id="new-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="edit-profile-input edit-profile-input-with-icon edit-profile-input-with-toggle"
                    placeholder={t("editProfile.placeholders.password")}
                  />
                  <button
                    type="button"
                    className="edit-profile-toggle-btn"
                    onClick={() => setShowPassword((prev) => !prev)}
                    aria-label={showPassword ? t("signup.hidePassword") : t("signup.showPassword")}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="edit-profile-field-group">
                <label htmlFor="phone" className="edit-profile-label">
                  {t("editProfile.phone")}
                </label>
                <div className="edit-profile-input-row">
                  <span className="edit-profile-prefix">+20</span>
                  <input
                    id="phone"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="edit-profile-input edit-profile-input-flex"
                    placeholder="10 XXXX XXXX"
                  />
                </div>
              </div>

              <div className="edit-profile-actions">
                <button type="button" className="edit-profile-cancel-btn" onClick={handleCancel}>
                  {t("common.cancel")}
                </button>
                <button type="submit" className="edit-profile-save-btn">
                  {t("editProfile.saveChanges")}
                </button>
              </div>
          </form>
        </section>

        <div className="edit-profile-right-column">
            {/* My Vehicles Card */}
            <section className="edit-profile-card edit-profile-vehicles-card">
              <div className="edit-profile-vehicles-header">
                <h2 className="edit-profile-card-title">{t("editProfile.myVehicles")}</h2>
                <p className="edit-profile-add-vehicle-note">{t("profile.vehiclesAdminOnly")}</p>
              </div>
              <div className="edit-profile-vehicle-list">
                {vehicles.map((vehicle) => (
                  <div key={vehicle.id} className="edit-profile-vehicle-item">
                    <div className="edit-profile-vehicle-icon" aria-hidden>
                      <Car size={19} strokeWidth={1.85} />
                    </div>
                    <div className="edit-profile-vehicle-info">
                      <span className="edit-profile-vehicle-plate">{vehicle.plate}</span>
                      <span className="edit-profile-vehicle-model">{vehicle.model}</span>
                    </div>
                    <span className="edit-profile-vehicle-type-badge">
                      {vehicleTypeShortLabel(vehicle.type)}
                    </span>
                    <div className="edit-profile-vehicle-actions">
                      <button
                        type="button"
                        className="edit-profile-icon-btn"
                        onClick={() => handleEditVehicle(vehicle.id)}
                        aria-label={t("editProfile.editVehicle")}
                      >
                        <Edit2 size={17} strokeWidth={1.75} />
                      </button>
                      <button
                        type="button"
                        className="edit-profile-icon-btn edit-profile-icon-btn--delete edit-profile-icon-danger"
                        onClick={() => handleDeleteVehicle(vehicle.id)}
                        aria-label={t("editProfile.deleteVehicle")}
                      >
                        <Trash2 size={17} strokeWidth={1.75} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Password Verification Card */}
            <section className="edit-profile-card edit-profile-verification-card">
              <h2 className="edit-profile-card-title">{t("editProfile.passwordVerification")}</h2>
              <p className="edit-profile-verification-text">{t("editProfile.verificationIntro")}</p>
              <div className="edit-profile-field-group">
                <label htmlFor="verify-password" className="edit-profile-label">
                  {t("editProfile.currentPassword")}
                </label>
                <input
                  id="verify-password"
                  type="password"
                  value={verificationPassword}
                  onChange={(e) => {
                    setVerificationPassword(e.target.value);
                    setPasswordVerified(false);
                  }}
                  className={`edit-profile-input ${
                    verificationStatus === "success"
                      ? "edit-profile-input-success"
                      : verificationStatus === "error"
                      ? "edit-profile-input-error"
                      : ""
                  }`}
                  placeholder={t("editProfile.verificationPlaceholder")}
                />
              </div>
              <button
                type="button"
                className="edit-profile-verify-btn"
                onClick={handleVerifyPassword}
              >
                {t("editProfile.verify")}
              </button>
              {verificationMessage && (
                <p
                  className={`edit-profile-verification-message ${
                    verificationStatus === "success"
                      ? "edit-profile-verification-success"
                      : verificationStatus === "error"
                      ? "edit-profile-verification-error"
                      : ""
                  }`}
                >
                  {verificationMessage}
                </p>
              )}
            </section>
        </div>
      </div>
    </main>
  );
}

export default EditProfile;

