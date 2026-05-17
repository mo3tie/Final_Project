// src/components/Sidebar.jsx

import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LayoutDashboard, Car, Wallet, User, ScanLine } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import { clearClientSession } from "../utils/session";
import "./Sidebar.css";
import mustLogo from "../assets/PicTures/Must_Without_BackGround.jpg";

function Sidebar({ userData, role = "user" }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef(null);

  const defaultUserData = {
    name: role === "admin" ? "System Admin" : "User",
    fleetId: "",
  };

  const currentUserData = userData || defaultUserData;

  const getInitials = (name) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .substring(0, 2);
  };

  const allMenuItems = [
    {
      key: "dashboard",
      icon: LayoutDashboard,
      labelKey: "sidebar.dashboard",
      hintKey: "hintDashboard",
      userPath: "/dashboard",
      adminPath: "/admin/dashboard",
      roles: ["user", "admin"],
    },
    {
      key: "trips",
      icon: Car,
      labelKey: "sidebar.trips",
      hintKey: "hintTrips",
      userPath: "/dashboard/trips",
      adminPath: "/admin/trips",
      roles: ["user", "admin"],
    },
    {
      key: "wallet",
      icon: Wallet,
      labelKey: "sidebar.wallet",
      hintKey: "hintWallet",
      userPath: "/dashboard/wallet",
      adminPath: "/admin/wallet",
      roles: ["user", "admin"],
    },
   
    {
      key: "profile",
      icon: User,
      labelKey: "sidebar.profile",
      hintKey: "hintProfile",
      userPath: "/dashboard/profile",
      adminPath: null,
      roles: ["user"],
    },
  ];

  const menuItems = allMenuItems
    .filter((item) => item.roles.includes(role))
    .map((item) => ({
      ...item,
      label: t(item.labelKey),
      titleHint: t(`sidebar.${item.hintKey}`),
      path:
        role === "admin" && item.adminPath
          ? item.adminPath
          : item.userPath || item.adminPath,
    }));

  const isActive = (path) => {
    if (path === "/dashboard" || path === "/admin/dashboard") {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  useEffect(() => {
    if (!accountMenuOpen) return;
    const onPointerDown = (e) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(e.target)) {
        setAccountMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [accountMenuOpen]);

  const handleLogout = () => {
    setAccountMenuOpen(false);
    clearClientSession();
    navigate("/");
  };

  const handleEditProfile = () => {
    setAccountMenuOpen(false);
    if (role === "admin") {
      navigate("/admin/dashboard");
    } else {
      navigate("/dashboard/profile/edit");
    }
  };

  return (
    <aside className="sidebar sidebar--floating" aria-label="Main navigation">
      <div className="sidebar-floating-inner">
        <div className="sidebar-header sidebar-header--floating">
          <button
            type="button"
            className="sidebar-logo-btn"
            onClick={() => navigate("/")}
            title={t("sidebar.hintHome")}
            aria-label={t("sidebar.homeTitle")}
          >
            <img
              src={mustLogo}
              alt="Misr-Gate"
              className="sidebar-logo-img sidebar-logo-img--floating"
            />
          </button>
          <LanguageSwitcher variant="sidebar" hintTitle={t("sidebar.hintLang")} />
        </div>

        <nav className="sidebar-menu sidebar-menu--floating" aria-label="Primary">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                type="button"
                className={`sidebar-nav-icon ${active ? "active" : ""}`}
                onClick={() => navigate(item.path)}
                title={item.titleHint}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
              >
                <Icon size={22} strokeWidth={1.75} aria-hidden />
              </button>
            );
          })}
        </nav>

        <div
          className="sidebar-footer sidebar-footer--floating sidebar-footer--account"
          ref={accountMenuRef}
        >
          <button
            type="button"
            className="sidebar-user-orb"
            onClick={() => setAccountMenuOpen((o) => !o)}
            title={t("sidebar.hintAccount")}
            aria-label={t("sidebar.account", { name: currentUserData.name })}
            aria-expanded={accountMenuOpen}
            aria-haspopup="menu"
          >
            {getInitials(currentUserData.name)}
          </button>
          {accountMenuOpen ? (
            <div className="sidebar-account-menu" role="menu">
              <button
                type="button"
                role="menuitem"
                className="sidebar-account-menu__item"
                onClick={handleEditProfile}
                title={t("sidebar.hintEdit")}
              >
                {t("sidebar.editProfile")}
              </button>
              <button
                type="button"
                role="menuitem"
                className="sidebar-account-menu__item sidebar-account-menu__item--danger"
                onClick={handleLogout}
                title={t("sidebar.hintLogout")}
              >
                {t("sidebar.logout")}
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
