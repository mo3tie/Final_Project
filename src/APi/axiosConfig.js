// src/APi/axiosConfig.js
import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: never send a stale JWT to login/signup — SimpleJWT returns 401 for invalid
// Bearer tokens before AllowAny is applied, which blocks registration.
API.interceptors.request.use((config) => {
  const url = config.url || "";
  const isPublicAuth =
    url.includes("/auth/login") || url.includes("/auth/signup");

  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }

  if (isPublicAuth) {
    delete config.headers.Authorization;
  } else {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default API;