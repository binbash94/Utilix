import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { lookupParcel } from "../services/api";
import { useState } from "react";

const Schema = z.object({
  apn: z.string().min(3, "APN/STRAP required"),
  street_address: z.string().optional(),
  county: z.string().min(2, "County/City key required"),
  state: z.string().min(2).max(2)
});
type FormData = z.infer<typeof Schema>;

export default function LookupForm({ onResult }: { onResult: (r: any) => void }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(Schema),
    defaultValues: { state: "FL" }
  });
  const [err, setErr] = useState<string | null>(null);
  const inputCls = "w-full bg-ui-card border border-ui-border focus:border-ui-primary outline-none rounded-xl px-3 py-3 text-sm";

  const onSubmit = async (data: FormData) => {
    setErr(null);
    try {
      const res = await lookupParcel({
        apn: data.apn,
        street_address: data.street_address || null,
        county: data.county,
        state: data.state.toUpperCase()
      });
      onResult(res);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || e.message || "Request failed");
      onResult(null);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {err && <div className="text-ui-danger text-sm">{err}</div>}
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-ui-subtext">APN / STRAP</label>
          <input className={inputCls} placeholder="124423C1023650290" {...register("apn")} />
          {errors.apn && <p className="text-ui-danger text-xs mt-1">{errors.apn.message}</p>}
        </div>
        <div>
          <label className="text-xs text-ui-subtext">Street Address (optional)</label>
          <input className={inputCls} placeholder="123 Sunshine Blvd" {...register("street_address")} />
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-ui-subtext">County</label>
          <input className={inputCls} placeholder="Lee" {...register("county")} />
          {errors.county && <p className="text-ui-danger text-xs mt-1">{errors.county.message}</p>}
        </div>
        <div>
          <label className="text-xs text-ui-subtext">State</label>
          <input className={inputCls} placeholder="FL" maxLength={2} {...register("state")} />
          {errors.state && <p className="text-ui-danger text-xs mt-1">{errors.state.message}</p>}
        </div>
      </div>
      <button className="bg-ui-primary hover:bg-ui-accent transition text-white px-5 py-3 rounded-xl" disabled={isSubmitting}>
        {isSubmitting ? "Looking up…" : "Lookup"}
      </button>
    </form>
  );
}
