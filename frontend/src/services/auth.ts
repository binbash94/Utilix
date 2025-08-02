import axios from "axios";
import { getHeaders, saveConfig } from "./config";

export async function login(username: string, password: string) {
  const { baseURL } = getHeaders();
  if (!baseURL) throw new Error("Set API Base URL first.");
  const url = `${baseURL}/api/v1/auth/token`;
  const body = new URLSearchParams({
    grant_type: "password",
    username,
    password,
    scope: ""
  });
  const res = await axios.post(url, body, { headers: { "Content-Type": "application/x-www-form-urlencoded" }});
  const token = res.data?.access_token || res.data?.token || "";
  saveConfig({ token: token ? `Bearer ${token}` : "" });
  return token;
}

export async function registerUser(payload: { email: string; password: string; full_name?: string }) {
  const { baseURL, headers } = getHeaders();
  const url = `${baseURL}/api/v1/auth/register`;
  const res = await axios.post(url, payload, { headers });
  return res.data;
}
