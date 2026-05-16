// src/pages/Home/Homepage.jsx

import React, { useMemo, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AnimatedCounter from "../../components/home/AnimatedCounter";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import {
  clearClientSession,
  dashboardPathFromSession,
  readSessionToken,
} from "../../utils/session";
import "./Homepage.css";
import mustLogo from "../../assets/PicTures/Must_Without_BackGround.jpg";
import heroVideo from "../../assets/videos/Intrance Video.mp4";

function Homepage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [sessionNonce, setSessionNonce] = useState(0);

  const loggedIn = useMemo(() => {
    void sessionNonce;
    void location.pathname;
    return Boolean(readSessionToken());
  }, [sessionNonce, location.pathname]);

  const goDashboard = useCallback(() => {
    navigate(dashboardPathFromSession());
  }, [navigate]);

  const handleLogout = useCallback(() => {
    clearClientSession();
    setSessionNonce((n) => n + 1);
  }, []);

  return (
    <div className="homepage">
      <nav className="navbar">
        <div className="nav-container">
          <div
            className="nav-logo"
            onClick={() => navigate("/")}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                navigate("/");
              }
            }}
          >
            <img
              src={mustLogo}
              alt="Misr-Gate"
              className="nav-logo-img"
              decoding="async"
              fetchPriority="high"
            />
            <span className="logo-text">{t("home.logo")}</span>
          </div>

          <ul className="nav-menu">
            <li>
              <a href="#home">
                {t("home.navHome")}
              </a>
            </li>
            <li>
              <a href="#how-it-works">
                {t("home.navHow")}
              </a>
            </li>
            <li>
              <a href="#faq">
                {t("home.navFaq")}
              </a>
            </li>
            <li>
              <a href="#footer">
                {t("home.navAbout")}
              </a>
            </li>
          </ul>

          <div className="nav-actions">
            <LanguageSwitcher variant="navbar" />
            {loggedIn ? (
              <>
                <button type="button" className="nav-btn btn-signup" onClick={goDashboard}>
                  {t("home.goToDashboard")}
                </button>
                <button type="button" className="nav-btn btn-logout-home" onClick={handleLogout}>
                  {t("sidebar.logout")}
                </button>
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="nav-btn btn-login"
                  onClick={() => navigate("/login")}
                >
                  {t("home.login")}
                </button>
                <button
                  type="button"
                  className="nav-btn btn-signup"
                  onClick={() => navigate("/signup")}
                >
                  {t("home.signUp")}
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      <section className="hero" id="home">
        <video
          className="hero-video"
          autoPlay
          loop
          muted
          playsInline
          preload="metadata"
          aria-hidden
        >
          <source src={heroVideo} type="video/mp4" />
        </video>
        <div className="hero-overlay" aria-hidden />
        <div className="hero-content">
          <div className="hero-badge">
            <span>{t("common.officialBadge")}</span>
          </div>

          <h1 className="hero-title">
            {t("home.heroTitle1")}
            <br />
            <span className="hero-title-accent">{t("home.heroTitle2")}</span>
          </h1>

          <p className="hero-subtitle">{t("home.heroSubtitle")}</p>

          <div className="hero-stats">
            <div className="stat-item stat-item--glass">
              <div className="stat-number">
                <AnimatedCounter end={50000} duration={2000} suffix="+" />
              </div>
              <div className="stat-label">{t("home.statUsers")}</div>
            </div>
            <div className="stat-item stat-item--glass">
              <div className="stat-number">
                <AnimatedCounter end={150} duration={2000} suffix="+" />
              </div>
              <div className="stat-label">{t("home.statGates")}</div>
            </div>
            <div className="stat-item stat-item--glass">
              <div className="stat-number">
                <AnimatedCounter end={99} duration={2000} uptimePercent />
              </div>
              <div className="stat-label">{t("home.statUptime")}</div>
            </div>
          </div>

          <div className="hero-cta">
            {loggedIn ? (
              <button type="button" className="btn-primary btn-large" onClick={goDashboard}>
                {t("home.goToDashboard")}
                <span className="btn-arrow" aria-hidden>
                  →
                </span>
              </button>
            ) : (
              <button
                type="button"
                className="btn-primary btn-large"
                onClick={() => navigate("/signup")}
              >
                {t("home.ctaCreate")}
                <span className="btn-arrow" aria-hidden>
                  →
                </span>
              </button>
            )}
            <button
              type="button"
              className="btn-secondary btn-large"
              onClick={() =>
                document
                  .getElementById("how-it-works")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              {t("home.ctaHow")}
              <span className="btn-arrow" aria-hidden>
                →
              </span>
            </button>
          </div>

          <div className="hero-trust-badges">
            <span className="trust-pill">{t("common.encryptedData")}</span>
            <span className="trust-pill">{t("common.pciPayments")}</span>
            <span className="trust-pill">{t("common.realtimeTrips")}</span>
          </div>
        </div>

        <div className="scroll-indicator">
          <span>{t("common.scroll")}</span>
          <div className="scroll-arrow" aria-hidden>
            ↓
          </div>
        </div>
      </section>

      <section className="home-how-it-works" id="how-it-works">
        <div className="container">
          <div className="section-header home-section-header">
            <p className="home-section-eyebrow">{t("home.sectionProcess")}</p>
            <h2 className="section-title">{t("home.sectionHowTitle")}</h2>
            <p className="section-subtitle">{t("home.sectionHowSubtitle")}</p>
          </div>
          <div className="home-steps-row">
            <article className="home-step-card">
              <span className="home-step-num">01</span>
              <h3 className="home-step-title">{t("home.step1Title")}</h3>
              <p className="home-step-text">{t("home.step1Text")}</p>
            </article>
            <article className="home-step-card">
              <span className="home-step-num">02</span>
              <h3 className="home-step-title">{t("home.step2Title")}</h3>
              <p className="home-step-text">{t("home.step2Text")}</p>
            </article>
            <article className="home-step-card">
              <span className="home-step-num">03</span>
              <h3 className="home-step-title">{t("home.step3Title")}</h3>
              <p className="home-step-text">{t("home.step3Text")}</p>
            </article>
          </div>
        </div>
      </section>

      <section className="faq-section" id="faq">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">{t("home.faqTitle")}</h2>
            <p className="section-subtitle">{t("home.faqSubtitle")}</p>
          </div>

          <div className="faq-grid">
            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq1q")}</h3>
              <p className="faq-answer">{t("home.faq1a")}</p>
            </div>

            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq2q")}</h3>
              <p className="faq-answer">{t("home.faq2a")}</p>
            </div>

            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq3q")}</h3>
              <p className="faq-answer">{t("home.faq3a")}</p>
            </div>

            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq4q")}</h3>
              <p className="faq-answer">{t("home.faq4a")}</p>
            </div>

            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq5q")}</h3>
              <p className="faq-answer">{t("home.faq5a")}</p>
            </div>

            <div className="faq-item">
              <h3 className="faq-question">{t("home.faq6q")}</h3>
              <p className="faq-answer">{t("home.faq6a")}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="final-cta">
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">{t("home.ctaTitle")}</h2>
            <p className="cta-description">{t("home.ctaDesc")}</p>
            <div className="cta-buttons">
              {loggedIn ? (
                <button type="button" className="btn-primary btn-large" onClick={goDashboard}>
                  {t("home.goToDashboard")}
                  <span className="btn-arrow" aria-hidden>
                    →
                  </span>
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-primary btn-large"
                  onClick={() => navigate("/signup")}
                >
                  {t("home.ctaCreate2")}
                  <span className="btn-arrow" aria-hidden>
                    →
                  </span>
                </button>
              )}
              <button
                type="button"
                className="btn-secondary btn-large"
                onClick={() => navigate("/contact")}
              >
                {t("home.ctaContact")}
                <span className="btn-arrow" aria-hidden>
                  →
                </span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer" id="footer">
        <div className="container">
          <div className="footer-main">
            <div className="footer-section">
              <div className="footer-logo">
                <span className="logo-text">{t("home.logo")}</span>
              </div>
              <p className="footer-description">{t("home.footerTagline")}</p>
              <div className="footer-social">
                <a href="#" className="social-link">
                  {t("home.socialFb")}
                </a>
                <a href="#" className="social-link">
                  {t("home.socialTw")}
                </a>
                <a href="#" className="social-link">
                  {t("home.socialLi")}
                </a>
              </div>
            </div>

            <div className="footer-section">
              <h4 className="footer-title">{t("home.quickLinks")}</h4>
              <ul className="footer-links">
                <li>
                  <a href="/about">{t("home.flAbout")}</a>
                </li>
                <li>
                  <a href="/how-it-works">{t("home.flHow")}</a>
                </li>
                <li>
                  <a href="/coverage">{t("home.flCoverage")}</a>
                </li>
                <li>
                  <a href="/faq">{t("home.flFaq")}</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4 className="footer-title">{t("home.support")}</h4>
              <ul className="footer-links">
                <li>
                  <a href="/support">{t("home.fsHelp")}</a>
                </li>
                <li>
                  <a href="/contact">{t("home.fsContact")}</a>
                </li>
                <li>
                  <a href="/refund">{t("home.fsRefund")}</a>
                </li>
                <li>
                  <a href="/dispute">{t("home.fsDispute")}</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4 className="footer-title">{t("home.legal")}</h4>
              <ul className="footer-links">
                <li>
                  <a href="/terms">{t("home.flTerms")}</a>
                </li>
                <li>
                  <a href="/privacy">{t("home.flPrivacy")}</a>
                </li>
                <li>
                  <a href="/cookies">{t("home.flCookies")}</a>
                </li>
                <li>
                  <a href="/compliance">{t("home.flCompliance")}</a>
                </li>
              </ul>
            </div>

            <div className="footer-section">
              <h4 className="footer-title">{t("home.contact")}</h4>
              <div className="footer-contact">
                <p>support@misr-gate.eg</p>
                <p>+20 123 456 7890</p>
                <p>{t("home.fc247")}</p>
                <p>{t("home.fcCity")}</p>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <p>{t("home.copyright")}</p>
            <div className="footer-badges">
              <span className="footer-badge">{t("common.madeInEgypt")}</span>
              <span className="footer-badge">{t("common.secure")}</span>
              <span className="footer-badge">{t("common.certified")}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Homepage;
