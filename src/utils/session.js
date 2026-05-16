/**
 * Clears client-side auth (JWT in localStorage and common cookie names).
 * Language preference (misr-gate-lang) is kept.
 */
export function clearClientSession() {
  try {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh");
    localStorage.removeItem("userName");
    localStorage.removeItem("fleetId");
    localStorage.removeItem("authRole");
  } catch {
    /* ignore */
  }
  const expires = "expires=Thu, 01 Jan 1970 00:00:00 GMT";
  const names = ["token", "access", "refresh", "sessionid", "csrftoken"];
  for (const name of names) {
    document.cookie = `${name}=;${expires};path=/`;
  }
}

export function readAuthRole() {
  try {
    return localStorage.getItem("authRole") === "admin" ? "admin" : "user";
  } catch {
    return "user";
  }
}

/** Where to send authenticated users when they tap “Dashboard”. */
export function dashboardPathFromSession() {
  return readAuthRole() === "admin" ? "/admin/dashboard" : "/dashboard";
}

export function readSessionToken() {
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

/** Keep sidebar/header in sync after profile or vehicle changes. */
export function syncSessionFromMe(me) {
  if (!me || typeof me !== "object") return;
  try {
    if (me.name) localStorage.setItem("userName", me.name);
    if (me.fleet_id) localStorage.setItem("fleetId", me.fleet_id);
    localStorage.setItem("authRole", "user");
  } catch {
    /* ignore */
  }
}
