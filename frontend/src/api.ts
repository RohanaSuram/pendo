/**
 * Base URL for the backend API.
 * - Local dev: "/api" (Vite proxies it to http://127.0.0.1:8000)
 * - Production: set VITE_API_URL to your backend, e.g. https://<user>-pendo-api.hf.space
 */
export const API_BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/$/, "");

export const apiUrl = (path: string) => `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
