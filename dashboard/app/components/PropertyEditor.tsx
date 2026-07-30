"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Property = {
  id: number; name: string; active: boolean; booking_site_listing_id: string | null;
  min_price: number; max_price: number; rounding_increment: number; competitor_urls: string[];
};
type PricingConfiguration = {
  competitor_weight: number; portfolio_weight: number; neutral_demand_score: number;
  demand_adjustment_slope: number; minimum_demand_adjustment: number;
  maximum_demand_adjustment: number;
  urgency_adjustments: { maximum_days: number; adjustment: number }[];
};

const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");

export function PropertyEditor({ property }: { property: Property }) {
  const router = useRouter();
  const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…");
    const form = new FormData(event.currentTarget);
    const payload = {
      active: form.get("active") === "on",
      min_price: Number(form.get("min_price")),
      max_price: Number(form.get("max_price")),
      rounding_increment: Number(form.get("rounding_increment")),
      competitor_urls: String(form.get("competitor_urls") ?? "").split("\n").map(value => value.trim()).filter(Boolean),
    };
    const response = await fetch(`/api/properties/${property.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    if (!response.ok) { setMessage((await response.json()).detail ?? "Save failed"); return; }
    setMessage("Saved"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}>
    <div className="policy-title"><div><h2>{property.name}</h2><span className="muted">BookingSite: {property.booking_site_listing_id ?? "Not mapped"}</span></div><label className="toggle"><input name="active" type="checkbox" defaultChecked={property.active}/> Pricing enabled</label></div>
    <div className="form-grid four">
      <label>Minimum IDR<input name="min_price" type="number" min="1" defaultValue={property.min_price}/></label>
      <label>Maximum IDR<input name="max_price" type="number" min="1" defaultValue={property.max_price}/></label>
      <label>Pricing step IDR<input name="rounding_increment" type="number" min="1" defaultValue={property.rounding_increment}/></label>
    </div>
    <label>Competitor URLs<textarea name="competitor_urls" rows={5} defaultValue={property.competitor_urls.join("\n")} placeholder="One canonical Airbnb URL per line"/></label>
    <div className="form-actions"><button className="button">Save property</button><span className="muted">{message}</span></div>
  </form>;
}

export function PricingConfigurationEditor({ configuration }: { configuration: PricingConfiguration }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget);
    const number = (name: string) => Number(form.get(name));
    const payload = {
      competitor_weight: number("competitor_weight"), portfolio_weight: number("portfolio_weight"),
      neutral_demand_score: number("neutral_demand_score"), demand_adjustment_slope: number("demand_adjustment_slope"),
      minimum_demand_adjustment: number("minimum_demand_adjustment"), maximum_demand_adjustment: number("maximum_demand_adjustment"),
      urgency_adjustments: configuration.urgency_adjustments.map((tier, index) => ({ maximum_days: tier.maximum_days, adjustment: number(`urgency_${index}`) })),
    };
    const response = await fetch("/api/settings/pricing", { method: "PUT", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    setMessage(response.ok ? "Saved" : (await response.json()).detail ?? "Save failed"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}><h2>Pricing Engine v2</h2>
    <div className="form-grid four">
      <label>Competitor weight<input name="competitor_weight" type="number" min="0" max="1" step="0.01" defaultValue={configuration.competitor_weight}/></label>
      <label>Portfolio weight<input name="portfolio_weight" type="number" min="0" max="1" step="0.01" defaultValue={configuration.portfolio_weight}/></label>
      <label>Neutral demand score<input name="neutral_demand_score" type="number" min="0" max="1" step="0.01" defaultValue={configuration.neutral_demand_score}/></label>
      <label>Demand slope<input name="demand_adjustment_slope" type="number" min="0" step="0.01" defaultValue={configuration.demand_adjustment_slope}/></label>
      <label>Minimum demand adjustment<input name="minimum_demand_adjustment" type="number" min="-1" max="0" step="0.01" defaultValue={configuration.minimum_demand_adjustment}/></label>
      <label>Maximum demand adjustment<input name="maximum_demand_adjustment" type="number" min="0" max="1" step="0.01" defaultValue={configuration.maximum_demand_adjustment}/></label>
      {configuration.urgency_adjustments.map((tier, index) => <label key={tier.maximum_days}>Urgency 0–{tier.maximum_days} days<input name={`urgency_${index}`} type="number" max="0" step="0.01" defaultValue={tier.adjustment}/></label>)}
    </div>
    <div className="form-actions"><button className="button">Save engine settings</button><span className="muted">{message}</span></div>
  </form>;
}

export function PricingActions() {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function action(path: string) {
    setMessage("Running…");
    const response = await fetch(path, { method: "POST", headers: { "X-CSRF-Token": csrf() } });
    const body = await response.json();
    setMessage(response.ok ? `${body.optimized ?? body.properties?.filter((item: {configured: boolean}) => item.configured).length} recommendations generated` : body.detail);
    router.refresh();
  }
  return <div className="action-row"><button className="button secondary" onClick={() => action("/api/pricing/bootstrap")}>Infer bounds</button><button className="button" onClick={() => action("/api/pricing/run")}>Generate 365 days</button><span className="muted">{message}</span></div>;
}
