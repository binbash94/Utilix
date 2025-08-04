import { useState } from "react";
import * as XLSX from "xlsx";
import { lookupParcel, LookupResponse } from "../services/api";

type RowIn = { apn: string; address?: string; county: string; state: string };

export default function BulkUpload() {
  const [rows, setRows] = useState<RowIn[]>([]);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [results, setResults] = useState<(LookupResponse & { __row?: number })[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onFile = async (file: File) => {
    setError(null); setRows([]); setResults([]);
    try {
      const buf = await file.arrayBuffer();
      const wb = XLSX.read(buf, { type: "array" });
      const first = wb.Sheets[wb.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json<Record<string, any>>(first, { raw: false });
      const normalized = json.map((row) => {
        const out: any = {};
        for (const [k, v] of Object.entries(row)) {
          const key = k.trim().toLowerCase().replace(/\s+/g, "_");
          if (key === "apn" || key === "pan") out.apn = String(v);
          else if (key === "address") out.address = String(v);
          else if (key === "county") out.county = String(v);
          else if (key === "state") out.state = String(v);
        }
        return out as RowIn;
      });
      setRows(normalized);
    } catch (e: any) { setError(e.message || "Failed to parse file."); }
  };

  const run = async () => {
    setProgress({ done: 0, total: rows.length });
    const out: (LookupResponse & { __row?: number })[] = [];
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      const apn = r.apn.replace(/[-.]/g, "");
      try {
        const res = await lookupParcel({
          apn: apn,
          street_address: r.address ?? null,
          county: r.county,
          state: (r.state || "FL").toUpperCase()
        });
        out.push({ ...res, __row: i + 1 });
      } catch {
        out.push({ apn: apn, electric_available: false, electric_provider: null,
                   water_available: false, water_provider: null,
                   sewer_available: false, sewer_provider: null } as any);
      }
      setProgress({ done: i + 1, total: rows.length });
      await new Promise(res => setTimeout(res, 10));
    }
    setResults(out);
  };

  const download = () => {
    const ws = XLSX.utils.json_to_sheet(results);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "UTILIX Results");
    XLSX.writeFile(wb, "utilix_results.xlsx");
  };

  return (
    <div className="space-y-3">
      <input
        type="file"
        accept=".csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        onChange={e => e.target.files && onFile(e.target.files[0])}
        className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-ui-primary file:text-white hover:file:bg-ui-accent"
      />
      {error && <div className="text-ui-danger text-sm">{error}</div>}

      {rows.length > 0 && (
        <div className="text-sm text-ui-subtext">
          Loaded <b>{rows.length}</b> rows.
        </div>
      )}

      <div className="flex items-center gap-3">
        <button className="bg-ui-primary hover:bg-ui-accent text-white px-4 py-2 rounded-xl disabled:opacity-50"
                onClick={run} disabled={rows.length === 0}>Process</button>
        <button className="bg-ui-card border border-ui-border text-ui-text px-4 py-2 rounded-xl disabled:opacity-50"
                onClick={download} disabled={results.length === 0}>Download Results</button>
      </div>

      {(progress.total > 0) && (
        <div className="text-xs text-ui-subtext">{progress.done} / {progress.total} processed</div>
      )}
    </div>
  );
}
