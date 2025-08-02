import { useState } from "react";
import { login } from "../services/auth";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const inputCls = "w-full bg-ui-card border border-ui-border focus:border-ui-primary outline-none rounded-xl px-3 py-3 text-sm";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null); setLoading(true);
    try { await login(username, password); navigate("/"); }
    catch (e: any) { setErr(e?.response?.data?.detail || "Login failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <div className="bg-ui-card rounded-2xl border border-ui-border p-6 shadow-soft">
        <h2 className="text-xl font-semibold mb-4 text-ui-primary2">Login</h2>
        {err && <div className="text-ui-danger text-sm mb-2">{err}</div>}
        <form onSubmit={submit} className="space-y-3">
          <div><label className="text-xs text-ui-subtext">Email / Username</label>
            <input className={inputCls} value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username"/></div>
          <div><label className="text-xs text-ui-subtext">Password</label>
            <input className={inputCls} type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></div>
          <button className="bg-ui-primary hover:bg-ui-accent text-white px-5 py-3 rounded-xl w-full" disabled={loading}>
            {loading ? "Signing in…" : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
