const DEFAULT_API_BASE_URL = "http://127.0.0.1:8765";

export const API_BASE_URL =
  import.meta.env.VITE_AUDITX_API_BASE_URL ?? DEFAULT_API_BASE_URL;