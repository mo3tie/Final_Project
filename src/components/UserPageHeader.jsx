import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "./UserPageHeader.css";

function avatarUrl(name) {
  const q = encodeURIComponent(name || "User");
  return `https://ui-avatars.com/api/?name=${q}&size=128&background=007fff&color=fff&bold=true`;
}

/**
 * Dashboard-style glass header capsule: title + subtitle left, fleet + avatar right.
 * The fleet/avatar pill opens Profile settings.
 */
function UserPageHeader({
  title,
  subtitle,
  user,
  profilePath = "/dashboard/profile",
  showFleetId = true,
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const u = user ?? { name: "John Driver", fleetId: "FL-2024" };

  const goProfile = () => {
    navigate(profilePath);
  };

  return (
    <header className="user-page-header glass-panel">
      <div className="user-page-header__left">
        <h1 className="user-page-header__title">{title}</h1>
        {subtitle ? <p className="user-page-header__subtitle">{subtitle}</p> : null}
      </div>
      <div className="user-page-header__right">
        <button
          type="button"
          className="user-page-header__pill user-page-header__pill--action"
          onClick={goProfile}
          aria-label={t("profile.settingsTitle")}
        >
          {showFleetId && u.fleetId ? (
            <span className="user-page-header__fleet">
              {t("common.fleetId")}: {u.fleetId}
            </span>
          ) : null}
          <img
            className="user-page-header__avatar"
            src={avatarUrl(u.name)}
            alt=""
            width={40}
            height={40}
            loading="lazy"
            referrerPolicy="no-referrer"
          />
        </button>
      </div>
    </header>
  );
}

export default React.memo(UserPageHeader);
