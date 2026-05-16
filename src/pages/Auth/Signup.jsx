// src/pages/Auth/Signup.jsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Eye,
  EyeOff,
  Check,
  Shield,
  Lock,
  ShieldCheck,
  BadgeCheck,
  AlertCircle,
} from "lucide-react";
import brandLogo from "../../assets/PicTures/Must_Without_BackGround.jpg";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import "./Signup.css";

function formatSignupErrors(data) {
  if (!data || typeof data !== "object") return null;
  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length) {
    return data.non_field_errors[0];
  }
  for (const [, v] of Object.entries(data)) {
    if (Array.isArray(v) && v.length) return v[0];
    if (v && typeof v === "object" && !Array.isArray(v)) {
      const inner = formatSignupErrors(v);
      if (inner) return inner;
    }
  }
  return null;
}

function Signup() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // Multi-step form: 1, 2, 3
  const [otpSentNotice, setOtpSentNotice] = useState(false);
  const [licenseFile, setLicenseFile] = useState(null);

  const [formData, setFormData] = useState({
    // Step 1: Personal Information
    fullName: "",
    email: "",
    otpCode: "",
    phone: "",
    nationalId: "",

    // Step 2: Vehicle Information
    vehicleType: "",
    vehicleModel: "",
    vehicleColor: "",

    // Step 3: Account Security
    password: "",
    confirmPassword: "",
    agreeToTerms: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [plateCelebration, setPlateCelebration] = useState(null);
  const [signupPlateScan, setSignupPlateScan] = useState(null);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSubmitError("");
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleSendOtp = () => {
    setSubmitError("");
    setOtpSentNotice(true);
  };

  const handleLicenseChange = (e) => {
    setSubmitError("");
    const file = e.target.files?.[0] ?? null;
    setLicenseFile(file);
  };

  const handleNextStep = (e) => {
    e.preventDefault();
    setSubmitError("");
    if (step < 3) {
      setStep(step + 1);
    }
  };

  const handlePrevStep = () => {
    setSubmitError("");
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const goDashboardAfterSignup = () => {
    setPlateCelebration(null);
    setSignupPlateScan(null);
    navigate("/dashboard");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError("");
    if (formData.password !== formData.confirmPassword) {
      setSubmitError(t("signup.passwordMismatch"));
      return;
    }
    setSubmitLoading(true);
    try {
      const fd = new FormData();
      fd.append("fullName", formData.fullName.trim());
      fd.append("email", formData.email.trim());
      fd.append("phone", formData.phone.trim());
      fd.append("nationalId", formData.nationalId.replace(/\D/g, ""));
      fd.append("vehicleType", formData.vehicleType);
      fd.append("vehicleModel", formData.vehicleModel.trim());
      fd.append("vehicleColor", formData.vehicleColor.trim());
      fd.append("password", formData.password);
      fd.append("confirmPassword", formData.confirmPassword);
      fd.append("agreeToTerms", formData.agreeToTerms ? "true" : "false");
      if (!licenseFile) {
        setSubmitError(t("signup.licenseRequired"));
        setSubmitLoading(false);
        return;
      }
      fd.append("licensePhoto", licenseFile);

      const { data, status } = await API.post(ENDPOINTS.SIGNUP, fd);
      if (status === 201 && data?.access) {
        localStorage.setItem("token", data.access);
        localStorage.setItem("authRole", "user");
        if (data.refresh) localStorage.setItem("refresh", data.refresh);
        localStorage.setItem("userName", data.name || "");
        if (data.fleet_id) localStorage.setItem("fleetId", data.fleet_id);
        const plate =
          data.accepted_plate ||
          data.display_plate ||
          data.plate_scan?.detected_plate_text ||
          "";
        setPlateCelebration(plate || t("signup.plateDetectedPending"));
        setSignupPlateScan(data.plate_scan || null);
      }
    } catch (err) {
      const msg =
        formatSignupErrors(err.response?.data) || t("signup.signupError");
      setSubmitError(msg);
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="signup-page">
      <LanguageSwitcher variant="auth" />
      {/* Background decoration */}
      <div className="signup-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      {/* Signup Container */}
      <div className="signup-container">
        {/* Left Side - Branding */}
        <div className="signup-branding">
          <div className="branding-content">
            <div className="auth-brand-lockup">
              <img
                src={brandLogo}
                alt=""
                className="auth-brand-logo-img"
                width={56}
                height={56}
              />
              <span className="auth-brand-wordmark">Misr-Gate</span>
            </div>

            <h1 className="branding-title">{t("signup.joinTitle")}</h1>

            <p className="branding-description">{t("signup.joinDesc")}</p>

            <div className="signup-progress">
              <div className="progress-steps">
                <div
                  className={`progress-step ${step >= 1 ? "active" : ""} ${
                    step > 1 ? "completed" : ""
                  }`}
                >
                  <div className="step-circle" aria-hidden>
                    {step > 1 ? (
                      <Check size={22} strokeWidth={2.25} />
                    ) : (
                      "1"
                    )}
                  </div>
                  <div className="step-label">{t("signup.stepPersonal")}</div>
                </div>
                <div className="progress-line" aria-hidden />
                <div
                  className={`progress-step ${step >= 2 ? "active" : ""} ${
                    step > 2 ? "completed" : ""
                  }`}
                >
                  <div className="step-circle" aria-hidden>
                    {step > 2 ? (
                      <Check size={22} strokeWidth={2.25} />
                    ) : (
                      "2"
                    )}
                  </div>
                  <div className="step-label">{t("signup.stepVehicle")}</div>
                </div>
                <div className="progress-line" aria-hidden />
                <div className={`progress-step ${step >= 3 ? "active" : ""}`}>
                  <div className="step-circle" aria-hidden>
                    3
                  </div>
                  <div className="step-label">{t("signup.stepSecurity")}</div>
                </div>
              </div>
            </div>

            <div className="branding-features">
              <div className="feature-item">
                <span className="feature-icon feature-icon--lucide" aria-hidden>
                  <Check size={18} strokeWidth={2.25} />
                </span>
                <span>{t("signup.feat1")}</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon feature-icon--lucide" aria-hidden>
                  <Check size={18} strokeWidth={2.25} />
                </span>
                <span>{t("signup.feat2")}</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon feature-icon--lucide" aria-hidden>
                  <Check size={18} strokeWidth={2.25} />
                </span>
                <span>{t("signup.feat3")}</span>
              </div>
            </div>

            <div className="branding-badge">{t("signup.badge")}</div>
          </div>
        </div>

        {/* Right Side - Signup Form */}
        <div className="signup-form-section">
          <div className="form-wrapper">
            <div className="auth-form-brand">
              <button type="button" className="auth-form-logo-btn" onClick={() => navigate("/")}>
                <img src={brandLogo} alt="" width={48} height={48} />
              </button>
              <div className="auth-form-brand-text">
                <span className="auth-form-brand-name">Misr-Gate</span>
                <span className="auth-form-brand-tagline">{t("signup.brandTagline")}</span>
              </div>
            </div>

            <div className="form-header">
              <h2 className="form-title">{t("signup.formTitle")}</h2>
              <p className="form-subtitle">
                {t("signup.formSubtitle", {
                  step,
                  label:
                    step === 1
                      ? t("signup.stepLabel1")
                      : step === 2
                        ? t("signup.stepLabel2")
                        : t("signup.stepLabel3"),
                })}
              </p>
            </div>

            {submitError ? (
              <div className="signup-form-error" role="alert">
                <AlertCircle
                  size={18}
                  strokeWidth={1.75}
                  style={{ display: "inline", verticalAlign: "text-bottom", marginRight: 6 }}
                  aria-hidden
                />
                {submitError}
              </div>
            ) : null}

            {/* Multi-Step Form */}
            <form
              className="signup-form"
              onSubmit={step === 3 ? handleSubmit : handleNextStep}
            >
              {/* STEP 1: Personal Information */}
              {step === 1 && (
                <div className="form-step" data-step="1">
                  {/* Full Name */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="fullName">
                      {t("signup.fullName")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="fullName"
                        name="fullName"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phFullName")}
                        autoComplete="name"
                        value={formData.fullName}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  {/* Email + OTP send */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="email">
                      {t("signup.email")}
                    </label>
                    <div className="signup-email-otp-row">
                      <div className="input-wrapper signup-email-field">
                        <input
                          type="email"
                          id="email"
                          name="email"
                          className="form-input form-input--email-otp form-input--solo"
                          placeholder={t("signup.phEmail")}
                          autoComplete="email"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                        />
                      </div>
                      <button
                        type="button"
                        className="signup-otp-trigger"
                        onClick={handleSendOtp}
                      >
                        {t("common.otp")}
                      </button>
                    </div>
                    {otpSentNotice ? (
                      <p className="signup-otp-message" role="status">
                        {t("signup.otpSent")}
                      </p>
                    ) : null}
                  </div>

                  {/* OTP entry */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="otpCode">
                      {t("signup.otpEnter")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="otpCode"
                        name="otpCode"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phOtp")}
                        value={formData.otpCode}
                        onChange={handleInputChange}
                        inputMode="numeric"
                        autoComplete="one-time-code"
                        maxLength={8}
                        required
                      />
                    </div>
                  </div>

                  {/* Phone Number */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="phone">
                      {t("signup.phone")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="tel"
                        id="phone"
                        name="phone"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phPhone")}
                        autoComplete="tel"
                        value={formData.phone}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  {/* National ID */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="nationalId">
                      {t("signup.nationalId")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="nationalId"
                        name="nationalId"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phNationalId")}
                        autoComplete="off"
                        value={formData.nationalId}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: Vehicle Information */}
              {step === 2 && (
                <div className="form-step" data-step="2">
                  <p className="signup-ai-plate-hint">{t("signup.aiPlateHint")}</p>

                  {/* Vehicle license photo */}
                  <div className="form-group">
                    <span className="form-label" id="license-upload-label">
                      {t("signup.licensePhoto")}
                    </span>
                    <div className="signup-license-upload">
                      <input
                        type="file"
                        id="licensePhoto"
                        name="licensePhoto"
                        className="signup-license-input"
                        accept="image/*"
                        onChange={handleLicenseChange}
                        aria-labelledby="license-upload-label"
                        required
                      />
                      <label htmlFor="licensePhoto" className="signup-license-label">
                        <span className="signup-license-label-title">
                          {t("signup.uploadLicense")}
                        </span>
                        <span className="signup-license-label-hint">
                          {t("signup.uploadLicenseHint")}
                        </span>
                      </label>
                      {licenseFile ? (
                        <p className="signup-license-filename">{licenseFile.name}</p>
                      ) : null}
                    </div>
                  </div>

                  {/* Vehicle Type */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="vehicleType">
                      {t("signup.vehicleType")}
                    </label>
                    <div className="input-wrapper">
                      <select
                        id="vehicleType"
                        name="vehicleType"
                        className="form-input form-select form-input--solo"
                        value={formData.vehicleType}
                        onChange={handleInputChange}
                        required
                      >
                        <option value="">{t("signup.selectType")}</option>
                        <option value="sedan">{t("signup.types.sedan")}</option>
                        <option value="bus">{t("signup.types.bus")}</option>
                        <option value="truck">{t("signup.types.truck")}</option>
                        <option value="van">{t("signup.types.van")}</option>
                      </select>
                    </div>
                  </div>

                  {/* Vehicle Model */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="vehicleModel">
                      {t("signup.vehicleModel")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="vehicleModel"
                        name="vehicleModel"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phModel")}
                        value={formData.vehicleModel}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  {/* Vehicle Color */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="vehicleColor">
                      {t("signup.vehicleColor")}
                    </label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        id="vehicleColor"
                        name="vehicleColor"
                        className="form-input form-input--solo"
                        placeholder={t("signup.phColor")}
                        value={formData.vehicleColor}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 3: Account Security */}
              {step === 3 && (
                <div className="form-step" data-step="3">
                  {/* Password */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="password">
                      {t("signup.createPassword")}
                    </label>
                    <div className="input-wrapper input-wrapper--password">
                      <input
                        type={showPassword ? "text" : "password"}
                        id="password"
                        name="password"
                        className="form-input form-input--with-toggle"
                        placeholder={t("signup.phPassword")}
                        value={formData.password}
                        onChange={handleInputChange}
                        autoComplete="new-password"
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label={
                          showPassword ? t("signup.hidePassword") : t("signup.showPassword")
                        }
                      >
                        {showPassword ? (
                          <EyeOff size={20} strokeWidth={1.75} />
                        ) : (
                          <Eye size={20} strokeWidth={1.75} />
                        )}
                      </button>
                    </div>
                    <small className="input-hint">{t("signup.pwdHint")}</small>
                  </div>

                  {/* Confirm Password */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="confirmPassword">
                      {t("signup.confirmPassword")}
                    </label>
                    <div className="input-wrapper input-wrapper--password">
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        id="confirmPassword"
                        name="confirmPassword"
                        className="form-input form-input--with-toggle"
                        placeholder={t("signup.phConfirmPassword")}
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        autoComplete="new-password"
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle"
                        onClick={() =>
                          setShowConfirmPassword(!showConfirmPassword)
                        }
                        aria-label={
                          showConfirmPassword
                            ? t("signup.hidePassword")
                            : t("signup.showPassword")
                        }
                      >
                        {showConfirmPassword ? (
                          <EyeOff size={20} strokeWidth={1.75} />
                        ) : (
                          <Eye size={20} strokeWidth={1.75} />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Terms & Conditions */}
                  <div className="form-group">
                    <label className="checkbox-label terms-checkbox">
                      <input
                        type="checkbox"
                        name="agreeToTerms"
                        checked={formData.agreeToTerms}
                        onChange={handleInputChange}
                        required
                      />
                      <span className="checkbox-text">
                        {t("signup.agreePrefix")}{" "}
                        <a href="/terms" className="link">
                          {t("signup.termsLink")}
                        </a>{" "}
                        {t("signup.and")}{" "}
                        <a href="/privacy" className="link">
                          {t("signup.privacyLink")}
                        </a>
                      </span>
                    </label>
                  </div>

                  {/* Security Notice */}
                  <div className="security-notice">
                    <span className="notice-icon notice-icon--lucide" aria-hidden>
                      <Shield size={22} strokeWidth={1.75} />
                    </span>
                    <p>{t("signup.securityNotice")}</p>
                  </div>
                </div>
              )}

              {/* Form Navigation Buttons */}
              <div className="form-navigation">
                {step > 1 && (
                  <button
                    type="button"
                    className="btn-back"
                    onClick={handlePrevStep}
                  >
                    ← {t("common.back")}
                  </button>
                )}

                <button
                  type="submit"
                  className="submit-button"
                  style={{ flex: step === 1 ? 1 : "initial" }}
                  disabled={submitLoading}
                >
                  {submitLoading
                    ? t("common.processing")
                    : step === 3
                      ? t("signup.createAccount")
                      : t("common.continue")}
                  <span className="button-arrow">→</span>
                </button>
              </div>
            </form>

            {/* Login Link */}
            <div className="login-prompt">
              <p>
                {t("signup.hasAccount")}{" "}
                <button
                  onClick={() => navigate("/login")}
                  className="login-link"
                >
                  {t("signup.signIn")}
                </button>
              </p>
            </div>

            {/* Back to Home Link */}
            <div className="back-home">
              <button onClick={() => navigate("/")} className="home-link">
                ← {t("signup.backHome")}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Trust Badges Footer */}
      {plateCelebration ? (
        <div className="signup-plate-overlay" role="dialog" aria-modal="true" aria-labelledby="signup-plate-title">
          <div className="signup-plate-card">
            <div className="signup-plate-card__glow" aria-hidden>
              <BadgeCheck size={36} strokeWidth={1.75} />
            </div>
            <h2 id="signup-plate-title" className="signup-plate-card__title">
              {t("signup.plateAcceptedTitle")}
            </h2>
            <div className="signup-plate-card__plate">{plateCelebration}</div>
            <p className="signup-plate-card__body">
              {t("signup.plateAcceptedBody", { plate: plateCelebration })}
            </p>
            {signupPlateScan ? (
              <div className="signup-plate-card__ai">
                <p className="signup-plate-card__ai-title">{t("signup.aiScanTitle")}</p>
                {signupPlateScan.annotated_image_url ? (
                  <img
                    src={signupPlateScan.annotated_image_url}
                    alt=""
                    className="signup-plate-card__ai-img"
                  />
                ) : null}
                <div className="signup-plate-card__ai-row">
                  <span>{t("signup.aiDetectedPlate")}</span>
                  <strong>{signupPlateScan.detected_plate_text || "—"}</strong>
                </div>
                <div className="signup-plate-card__ai-row">
                  <span>{t("signup.aiDetectedVehicle")}</span>
                  <strong>{signupPlateScan.detected_vehicle_type || "—"}</strong>
                </div>
                <p
                  className={
                    signupPlateScan.plate_match
                      ? "signup-plate-card__ai-match signup-plate-card__ai-match--ok"
                      : "signup-plate-card__ai-match signup-plate-card__ai-match--no"
                  }
                >
                  {signupPlateScan.plate_match
                    ? t("signup.aiPlateMatch")
                    : t("signup.aiPlateNoMatch")}
                </p>
                {signupPlateScan.error_message ? (
                  <p className="signup-plate-card__ai-err">{signupPlateScan.error_message}</p>
                ) : null}
              </div>
            ) : licenseFile ? (
              <p className="signup-plate-card__ai-pending">{t("signup.aiScanPending")}</p>
            ) : null}
            <button type="button" className="signup-plate-card__cta" onClick={goDashboardAfterSignup}>
              {t("signup.plateAcceptedCta")}
            </button>
          </div>
        </div>
      ) : null}

      <div className="signup-footer">
        <div className="footer-badges">
          <div className="badge-item">
            <span className="badge-icon badge-icon--lucide" aria-hidden>
              <Lock size={16} strokeWidth={1.75} />
            </span>
            <span>{t("common.sslSecured")}</span>
          </div>
          <div className="badge-item">
            <span className="badge-icon badge-icon--lucide" aria-hidden>
              <BadgeCheck size={16} strokeWidth={1.75} />
            </span>
            <span>{t("common.verifiedPlatform")}</span>
          </div>
          <div className="badge-item">
            <span className="badge-icon badge-icon--lucide" aria-hidden>
              <ShieldCheck size={16} strokeWidth={1.75} />
            </span>
            <span>{t("common.dataProtected")}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Signup;
