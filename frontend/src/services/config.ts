export type ClientConfig = { apiBase?: string; token?: string };
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
  return { baseURL: (cfg.apiBase || "").replace(/\/$/, ""), headers };
}
