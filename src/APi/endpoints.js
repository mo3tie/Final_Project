// src/APi/endpoints.js

export const ENDPOINTS = {
  LOGIN: "/users/auth/login/",
  SIGNUP: "/users/auth/signup/",
  SEND_OTP: "/users/auth/send-otp/",
  ME: "/users/me/",
  VERIFY_PASSWORD: "/users/me/verify-password/",
  TRIPS: "/users/trips/",
  WALLET: "/payment/wallet/",
  WALLET_RECHARGE: "/payment/wallet/recharge/",
  VEHICLE: (id) => `/vehicles/${id}/`,
  PLATE_SCANS: "/ai/plate-scans/",
  PLATE_SCAN: (id) => `/ai/plate-scans/${id}/`,
  ADMIN_PLATE_SCANS: "/ai/admin/plate-scans/",
  ADMIN_ACCOUNTS: "/users/admin/accounts/",
};