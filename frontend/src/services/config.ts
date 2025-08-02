export type ClientConfig = { token?: string };
const KEY = "utilix_cfg_v1";

export function getStoredConfig(): ClientConfig {
  try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
  catch { return {}; }
}
export function saveConfig(cfg: ClientConfig) {
  localStorage.setItem(KEY, JSON.stringify(cfg));
}
export function getHeaders() {
  const cfg = getStoredConfig();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (cfg.token) headers.Authorization = cfg.token.startsWith("Bearer") ? cfg.token : `Bearer ${cfg.token}`;
  const baseURL = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000";
  return { baseURL: baseURL.replace(/\/$/, ""), headers };
}
