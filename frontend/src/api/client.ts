import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

const TOKEN_KEY = "esg_access_token";
const REFRESH_KEY = "esg_refresh_token";

export function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string) {
  sessionStorage.setItem(TOKEN_KEY, access);
  sessionStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }
    const refresh = sessionStorage.getItem(REFRESH_KEY);
    if (!refresh) {
      clearTokens();
      return Promise.reject(error);
    }
    original._retry = true;
    if (!refreshing) {
      refreshing = axios
        .post(`${baseURL}/api/auth/token/refresh/`, { refresh })
        .then((r) => {
          setTokens(r.data.access, refresh);
          return r.data.access as string;
        })
        .finally(() => {
          refreshing = null;
        });
    }
    try {
      const access = await refreshing;
      original.headers.Authorization = `Bearer ${access}`;
      return api(original);
    } catch {
      clearTokens();
      window.location.href = "/login";
      return Promise.reject(error);
    }
  }
);
