export type ParcelResult = {
  apn: string;
  electric_available: boolean;
  electric_provider: string | null;
  water_available: boolean;
  water_provider: string | null;
  water_phone?: string | null;
  sewer_available: boolean;
  sewer_provider: string | null;
  sewer_phone?: string | null;
} | null;

function Row({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between py-2 border-b border-ui-border/50 last:border-none">
      <span className="text-ui-subtext">{label}</span>
      <span className="font-medium">{value ?? "—"}</span>
    </div>
  );
}

export default function ResultsCard({ result }: { result: ParcelResult }) {
  return (
    <div className="bg-ui-card rounded-2xl border border-ui-border p-5 shadow-soft">
      <h3 className="text-lg font-semibold mb-4 text-ui-primary2">Results</h3>
      {!result ? (
        <p className="text-sm text-ui-subtext">No results yet. Run a lookup to see details.</p>
      ) : (
        <div className="space-y-4">
          <Row label="APN / STRAP" value={result.apn} />
          <div className="pt-2">
            <div className="text-sm uppercase tracking-wide text-ui-subtext mb-2">Electric</div>
            <Row label="Available" value={result.electric_available ? "Yes" : "No"} />
            <Row label="Provider" value={result.electric_provider} />
          </div>
          <div>
            <div className="text-sm uppercase tracking-wide text-ui-subtext mb-2">Water</div>
            <Row label="Available" value={result.water_available ? "Yes" : "No"} />
            <Row label="Provider" value={result.water_provider} />
            <Row label="Phone" value={result.water_phone} />
          </div>
          <div>
            <div className="text-sm uppercase tracking-wide text-ui-subtext mb-2">Sewer</div>
            <Row label="Available" value={result.sewer_available ? "Yes" : "No"} />
            <Row label="Provider" value={result.sewer_provider} />
            <Row label="Phone" value={result.sewer_phone} />
          </div>
        </div>
      )}
    </div>
  );
}
