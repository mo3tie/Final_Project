import React, { useEffect, useMemo } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { readAuthRole, readSessionToken } from "../utils/session";
import "../components/Sidebar.css";
import "../styles/user-theme.css";
import "../styles/user-pages-glass.css";
import "./UserLayout.css";

const DEFAULT_USER = {
  name: "John Driver",
  fleetId: "",
};

function readShellUser() {
  try {
    return {
      name: localStorage.getItem("userName") || DEFAULT_USER.name,
      fleetId: localStorage.getItem("fleetId") || DEFAULT_USER.fleetId,
    };
  } catch {
    return { ...DEFAULT_USER };
  }
}

function UserLayout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const role = useMemo(() => readAuthRole(), [pathname]);
  const user = useMemo(() => readShellUser(), [pathname]);

  useEffect(() => {
    if (!readSessionToken()) {
      navigate("/login", { replace: true });
      return;
    }
    if (role === "admin") {
      navigate("/admin/dashboard", { replace: true });
    }
  }, [role, navigate]);

  if (role === "admin") {
    return null;
  }

  return (
    <div className="user-app-shell">
      <Sidebar userData={user} role="user" />
      <div className="user-app-shell__main">
        <div className="user-app-shell__content">
          <div className="user-app-shell__outlet">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserLayout;
