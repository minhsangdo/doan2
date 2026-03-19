/**
 * API gốc: local dev gọi backend riêng; production (Docker/HF) gọi cùng origin /api.
 */
export const API_URL = import.meta.env.PROD
  ? "/api"
  : (import.meta.env.VITE_API_URL || "http://localhost:8000/api");
