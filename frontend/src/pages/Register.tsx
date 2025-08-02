import { useState } from "react";
import { registerUser } from "../services/auth";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  the
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const inputCls = "w-full bg-ui-card border border-ui-border focus:border-ui-primary outline-none rounded-xl px-3 py-3 text-sm";

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null); setOk(null); setLoading(true);
    try { await registerUser({ email, password, full_name: fullName || undefined }); setOk("Account created. You can now log in."); setTimeout(()=>navigate("/login"), 800); }
    catch (e: any) { setErr(e?.response?.data?.detail || "Registration failed"); }
    finally { setLoading(false); }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <div className="bg-ui-card rounded-2xl border border-ui-border p-6 shadow-soft">
        <h2 className="text-xl font-semibold mb-4 text-ui-primary2">Register</h2>
        {err && <div className="text-ui-danger text-sm mb-2">{err}</div>}
        {ok && <div className="text-ui-success text-sm mb-2">{ok}</div>}
        <form onSubmit={submit} className="space-y-3">
          <div><label className="text-xs text-ui-subtext">Full name (optional)</label>
            <input className={inputCls} value={fullName} onChange={e=>setFullName(e.target.value)} autoComplete="name"/></div>
          <div><label className="text-xs text-ui-subtext">Email (username)</label>
            <input className={inputCls} value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/></div>
          <div><label className="text-xs text-ui-subtext">Password</label>
            <input className={inputCls} type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="new-password"/></div>
          <button className="bg-ui-primary hover:bg-ui-accent text-white px-5 py-3 rounded-xl w-full" disabled={loading}>
            {loading ? "Creating account…" : "Register"}
          </button>
        </form>
      </div>
    </div>
  );
}
