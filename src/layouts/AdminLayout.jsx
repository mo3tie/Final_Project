import React, { useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { readAuthRole, readSessionToken } from "../utils/session";
import "../components/Sidebar.css";
import "../styles/user-theme.css";
import "../styles/admin-pages-glass.css";

const ADMIN_USER = {
  name: "System Admin",
  fleetId: "",
};

function AdminLayout() {
  const navigate = useNavigate();
  const role = readAuthRole();

  useEffect(() => {
    if (!readSessionToken()) {
      navigate("/login", { replace: true });
      return;
    }
    if (role !== "admin") {
      navigate("/dashboard", { replace: true });
    }
  }, [role, navigate]);

  if (role !== "admin") {
    return null;
  }

  return (
    <div className="user-app-shell">
      <Sidebar role="admin" userData={ADMIN_USER} />
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

export default AdminLayout;
