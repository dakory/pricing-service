"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Property = {
  id: number; name: string; active: boolean; booking_site_listing_id: string | null;
  base_price: number; min_price: number; max_price: number; rounding_increment: number;
  weekday_factors: Record<string, number>; season_factors: Record<string, number>;
  minimum_stay_rules: { default?: number }; orphan_gap_rules: { max_gap?: number; price_factor?: number; relax_minimum_stay?: boolean };
};

const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");

export function PropertyEditor({ property }: { property: Property }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…");
    const form = new FormData(event.currentTarget);
    const number = (name: string) => Number(form.get(name));
    const payload = {
      active: form.get("active") === "on",
      base_price: number("base_price"), min_price: number("min_price"), max_price: number("max_price"),
      rounding_increment: number("rounding_increment"),
      weekday_factors: Object.fromEntries(weekdays.map((_, index) => [String(index), number(`weekday_${index}`)])),
      season_factors: Object.fromEntries(months.map((_, index) => [String(index + 1), number(`month_${index + 1}`)])),
      minimum_stay_rules: { default: number("default_minimum_stay") },
      orphan_gap_rules: { max_gap: number("max_gap"), price_factor: number("gap_factor"), relax_minimum_stay: form.get("relax_gap") === "on" },
    };
    const response = await fetch(`/api/properties/${property.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    if (!response.ok) { setMessage((await response.json()).detail ?? "Save failed"); return; }
    setMessage("Saved"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}>
    <div className="policy-title"><div><h2>{property.name}</h2><span className="muted">BookingSite: {property.booking_site_listing_id ?? "Not mapped"}</span></div><label className="toggle"><input name="active" type="checkbox" defaultChecked={property.active}/> Shadow pricing enabled</label></div>
    <div className="form-grid four">
      <label>Canonical base<input name="base_price" type="number" min="1" defaultValue={property.base_price}/></label>
      <label>Minimum<input name="min_price" type="number" min="1" defaultValue={property.min_price}/></label>
      <label>Maximum<input name="max_price" type="number" min="1" defaultValue={property.max_price}/></label>
      <label>Rounding IDR<input name="rounding_increment" type="number" min="1" defaultValue={property.rounding_increment}/></label>
    </div>
    <h3>Weekday factors</h3><div className="factor-grid">{weekdays.map((day, index) => <label key={day}>{day}<input name={`weekday_${index}`} type="number" min="0.01" max="3" step="0.01" defaultValue={property.weekday_factors[String(index)] ?? 1}/></label>)}</div>
    <h3>Season factors</h3><div className="factor-grid months">{months.map((month, index) => <label key={month}>{month}<input name={`month_${index + 1}`} type="number" min="0.01" max="3" step="0.01" defaultValue={property.season_factors[String(index + 1)] ?? 1}/></label>)}</div>
    <h3>Stay and orphan-gap rules</h3><div className="form-grid four">
      <label>Default minimum stay<input name="default_minimum_stay" type="number" min="1" defaultValue={property.minimum_stay_rules.default ?? 2}/></label>
      <label>Maximum orphan gap<input name="max_gap" type="number" min="0" defaultValue={property.orphan_gap_rules.max_gap ?? 3}/></label>
      <label>Gap price factor<input name="gap_factor" type="number" min="0.01" max="3" step="0.01" defaultValue={property.orphan_gap_rules.price_factor ?? 0.9}/></label>
      <label className="toggle lower"><input name="relax_gap" type="checkbox" defaultChecked={property.orphan_gap_rules.relax_minimum_stay ?? true}/> Relax stay to exact gap</label>
    </div>
    <div className="form-actions"><button className="button">Save policy</button><span className="muted">{message}</span></div>
  </form>;
}

export function PricingActions() {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function action(path: string) {
    setMessage("Running…");
    const response = await fetch(path, { method: "POST", headers: { "X-CSRF-Token": csrf() } });
    const body = await response.json();
    setMessage(response.ok ? `${body.optimized ?? body.properties?.filter((p: {configured: boolean}) => p.configured).length} processed in shadow mode` : body.detail);
    router.refresh();
  }
  return <div className="action-row"><button className="button secondary" onClick={() => action("/api/pricing/bootstrap")}>Reset safe defaults</button><button className="button" onClick={() => action("/api/pricing/run")}>Generate 365 days</button><span className="muted">{message}</span></div>;
}
