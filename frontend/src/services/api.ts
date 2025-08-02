import axios from "axios";
import { getHeaders } from "./config";

export type LookupPayload = {
  apn: string;
  street_address?: string | null;
  county: string;
  state: string;
};

// Extended response: new fields are optional so old backends won't break.
export type LookupResponse = {
  apn: string;
  electric_available: boolean;
  electric_provider: string | null;
  water_available: boolean;
  water_provider: string | null;
  sewer_available: boolean;
  sewer_provider: string | null;

  // NEW (optional)
  well_available?: boolean | null;
  well_use?: string | null;
  septic_present?: boolean | null;
};

export async function lookupParcel(payload: LookupPayload) {
  const { baseURL, headers } = getHeaders();
  const url = `${baseURL}/api/v1/parcels/lookup`;
  const res = await axios.post<LookupResponse>(url, payload, { headers });
  return res.data;
}
