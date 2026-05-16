// src/pages/Auth/Login.jsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff, Shield, Zap, AlertCircle } from "lucide-react";
import API from "../../APi/axiosConfig";
import { ENDPOINTS } from "../../APi/endpoints";
import brandLogo from "../../assets/PicTures/Must_Without_BackGround.jpg";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import "./Login.css";

function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("user");
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false); 
  const [error, setError] = useState(""); 

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(""); 

    try {
      const response = await API.post(ENDPOINTS.LOGIN, {
        email: formData.email,
        password: formData.password,
      });

      if (response.status === 200) {
        localStorage.setItem("token", response.data.access);
        localStorage.setItem("userName", response.data.name);
        const isAdmin = activeTab === "admin";
        localStorage.setItem("authRole", isAdmin ? "admin" : "user");

        if (!isAdmin) {
          try {
            const me = await API.get(ENDPOINTS.ME);
            if (me.data?.fleet_id) localStorage.setItem("fleetId", me.data.fleet_id);
            if (me.data?.name) localStorage.setItem("userName", me.data.name);
          } catch {
            /* sidebar falls back to login name */
          }
          navigate("/dashboard");
        } else {
          navigate("/admin/dashboard");
        }
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.detail ||
        t("login.invalidCreds");
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <LanguageSwitcher variant="auth" />
      <div className="login-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      <div className="login-container">
        <div className="login-branding">
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
            <h1 className="branding-title">{t("login.brandingTitle")}</h1>
            <p className="branding-description">{t("login.brandingDesc")}</p>

            <div className="branding-features">
              <div className="feature-item">
                <span className="feature-icon feature-icon--lucide" aria-hidden>
                  <Shield size={20} strokeWidth={1.75} />
                </span>
                <span>{t("login.feature1")}</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon feature-icon--lucide" aria-hidden>
                  <Zap size={20} strokeWidth={1.75} />
                </span>
                <span>{t("login.feature2")}</span>
              </div>
            </div>
            <div className="branding-badge">{t("login.badge")}</div>
          </div>
        </div>

        <div className="login-form-section">
          <div className="form-wrapper">
            <div className="auth-form-brand">
              <button type="button" className="auth-form-logo-btn" onClick={() => navigate("/")}>
                <img src={brandLogo} alt="" width={48} height={48} />
              </button>
              <div className="auth-form-brand-text">
                <span className="auth-form-brand-name">Misr-Gate</span>
                <span className="auth-form-brand-tagline">{t("login.tagline")}</span>
              </div>
            </div>

            <div className="login-tabs">
              <button
                type="button"
                className={`tab-button ${activeTab === "user" ? "active" : ""}`}
                onClick={() => setActiveTab("user")}
              >
                <span className="tab-label">{t("login.tabUser")}</span>
              </button>
              <button
                type="button"
                className={`tab-button ${activeTab === "admin" ? "active" : ""}`}
                onClick={() => setActiveTab("admin")}
              >
                <span className="tab-label">{t("login.tabAdmin")}</span>
              </button>
            </div>

            <div className="form-header">
              <h2 className="form-title">
                {activeTab === "user" ? t("login.welcomeUser") : t("login.welcomeAdmin")}
              </h2>
              <p className="form-subtitle">{t("login.formSubtitle")}</p>
            </div>

            {/* Error Message UI */}
            {error && (
              <div className="error-message-ui" role="alert">
                <AlertCircle className="error-icon-svg" size={20} strokeWidth={1.75} aria-hidden />
                {error}
              </div>
            )}

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="login-email">
                  {t("login.email")}
                </label>
                <div className="input-wrapper">
                  <input
                    id="login-email"
                    type="email"
                    name="email"
                    className="form-input form-input--solo"
                    placeholder={t("login.emailPlaceholder")}
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    autoComplete="email"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="login-password">
                  {t("login.password")}
                </label>
                <div className="input-wrapper input-wrapper--password">
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-input form-input--with-toggle"
                    placeholder={t("login.passwordPlaceholder")}
                    required
                    value={formData.password}
                    onChange={handleInputChange}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? t("login.hidePassword") : t("login.showPassword")}
                  >
                    {showPassword ? (
                      <EyeOff size={20} strokeWidth={1.75} />
                    ) : (
                      <Eye size={20} strokeWidth={1.75} />
                    )}
                  </button>
                </div>
              </div>

              <div className="form-options">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleInputChange}
                  />
                  <span className="checkbox-text">{t("login.remember")}</span>
                </label>
                
                <a href="#" className="forgot-link" onClick={(e) => e.preventDefault()}>
                  {t("login.forgot")}
                </a>
              </div>

              <button type="submit" className="submit-button" disabled={loading}>
                <span>
                  {loading
                    ? t("common.processing")
                    : activeTab === "user"
                      ? t("login.signIn")
                      : t("login.adminLogin")}
                </span>
                {!loading && <span className="button-arrow">→</span>}
              </button>

              <div className="form-divider">
                <span>{t("common.or")}</span>
              </div>
              <div className="auth-dev-skip-wrap">
                <button
                  type="button"
                  className="auth-dev-skip"
                  onClick={() => navigate("/dashboard")}
                >
                  {t("common.devSkip")}
                </button>
              </div>

              {activeTab === "user" && (
                <div className="signup-prompt">
                  <p>
                    {t("login.noAccount")}{" "}
                    <button
                      type="button"
                      className="signup-link"
                      onClick={() => navigate("/signup")}
                    >
                      {t("login.createAccount")}
                    </button>
                  </p>
                </div>
              )}
            </form>

            <div className="back-home">
              <button onClick={() => navigate("/")} className="home-link">
                ← {t("login.backHome")}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
