import { useEffect, useState } from "react";
import { Routes, Route, Link, useNavigate } from "react-router-dom";
import LookupForm from "./components/LookupForm";
import ResultsCard, { ParcelResult } from "./components/ResultsCard";
import BulkUpload from "./components/BulkUpload";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { getStoredConfig, saveConfig } from "./services/config";

export default function App() {
  const [results, setResults] = useState<ParcelResult | null>(null);
  const [apiBase, setApiBase] = useState("");
  const [token, setToken] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const cfg = getStoredConfig();
    setApiBase(cfg.apiBase || "");
    setToken(cfg.token || "");
  }, []);

  const onSaveCfg = () => saveConfig({ apiBase, token });
  const logout = () => { saveConfig({ apiBase, token: "" }); setToken(""); navigate("/"); };

  return (
    <div className="min-h-screen">
      <header className="border-b border-ui-border bg-ui-bg sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-ui-primary flex items-center justify-center shadow-soft">
              <span className="font-black text-white">U</span>
            </div>
            <h1 className="text-xl md:text-2xl font-semibold tracking-wide">
              <span className="text-ui-primary">UTILIX</span>
              <span className="text-ui-subtext ml-2">• Utility Lookup</span>
            </h1>
          </Link>

          <div className="flex items-center gap-2">
            <input className="w-56 bg-ui-card border border-ui-border rounded-xl px-3 py-2 text-sm"
                   placeholder="API Base (http://localhost:8000)"
                   value={apiBase} onChange={e=>setApiBase(e.target.value)} />
            <input className="w-48 bg-ui-card border border-ui-border rounded-xl px-3 py-2 text-sm"
                   placeholder="Bearer token" value={token}
                   onChange={e=>setToken(e.target.value)} />
            <button className="bg-ui-primary hover:bg-ui-accent text-white px-4 py-2 rounded-xl"
                    onClick={onSaveCfg}>Save</button>

            {!token ? (
              <>
                <Link to="/login" className="px-4 py-2 rounded-xl border border-ui-border bg-ui-card">Login</Link>
                <Link to="/register" className="px-4 py-2 rounded-xl bg-ui-primary text-white">Register</Link>
              </>
            ) : (
              <button className="px-4 py-2 rounded-xl border border-ui-border bg-ui-card" onClick={logout}>
                Logout
              </button>
            )}
          </div>
        </div>
      </header>

      <Routes>
        <Route path="/" element={
          <main className="max-w-6xl mx-auto px-4 py-8 grid md:grid-cols-3 gap-6">
            <section className="md:col-span-2 space-y-6">
              <div className="bg-ui-card rounded-2xl border border-ui-border p-5 shadow-soft">
                <h2 className="text-lg font-semibold mb-4 text-ui-primary2">Single Lookup</h2>
                <LookupForm onResult={setResults} />
              </div>
              <div className="bg-ui-card rounded-2xl border border-ui-border p-5 shadow-soft">
                <h2 className="text-lg font-semibold mb-4 text-ui-primary2">Bulk Upload (CSV / Excel)</h2>
                <BulkUpload />
              </div>
            </section>
            <aside className="space-y-6">
              <ResultsCard result={results} />
              <div className="bg-ui-card rounded-2xl border border-ui-border p-5">
                <h3 className="font-medium text-ui-primary2 mb-2">Tips</h3>
                <ul className="text-sm text-ui-subtext list-disc ml-5 space-y-1">
                  <li>APN/STRAP can include punctuation; backend normalizes if needed.</li>
                  <li>“County” may be a city key (e.g., “Lehigh Acres”).</li>
                  <li>Set API Base & Token above; stored locally.</li>
                </ul>
              </div>
            </aside>
          </main>
        }/>
        <Route path="/login" element={<Login/>}/>
        <Route path="/register" element={<Register/>}/>
      </Routes>

      <footer className="border-t border-ui-border py-6 text-center text-xs text-ui-subtext">
        © {new Date().getFullYear()} UTILIX
      </footer>
    </div>
  );
}
