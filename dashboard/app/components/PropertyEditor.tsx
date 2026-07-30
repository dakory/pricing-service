"use client";

import { FormEvent, ReactNode, useState } from "react";
import { useRouter } from "next/navigation";

type UrgencyTier = { maximum_days: number; adjustment: number };
type PricingConfiguration = {
  base_price_mode: "market_median" | "manual"; manual_base_price: number | null;
  market_price_adjustment: number; demand_adjustment_enabled: boolean;
  urgency_adjustment_enabled: boolean; competitor_weight: number;
  pricing_group_weight: number; neutral_demand_score: number;
  demand_adjustment_slope: number; minimum_demand_adjustment: number;
  maximum_demand_adjustment: number; urgency_adjustments: UrgencyTier[];
};
type Property = {
  id: number; name: string; active: boolean; booking_site_listing_id: string | null; pricing_group_id: number;
  min_price: number; max_price: number; rounding_increment: number;
  pricing_settings: Partial<PricingConfiguration>;
};
type PricingGroup = { id: number; name: string; competitor_urls: string[]; property_count: number; pricing_settings: Partial<PricingConfiguration> };

const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
const parseOptionalNumber = (form: FormData, name: string) => {
  const value = String(form.get(name) ?? "").trim();
  return value === "" ? undefined : Number(value);
};
const parseOptionalBoolean = (form: FormData, name: string) => {
  const value = String(form.get(name) ?? "");
  return value === "" ? undefined : value === "true";
};

function Hint({ children }: { children: ReactNode }) {
  return <small className="muted">{children}</small>;
}

function FormulaCard() {
  return <div className="card">
    <h2>How the price is calculated</h2>
    <p><code>base price = market median × (1 + market offset)</code> <span className="muted">or a manually entered base price</span></p>
    <p><code>demand score = competitor weight × competitor unavailability + pricing-group weight × pricing-group occupancy</code></p>
    <p><code>raw price = base price × (1 + demand adjustment + urgency adjustment)</code></p>
    <p><code>final price = manual date override ?? round(clamp(raw price, minimum, maximum), pricing step)</code></p>
    <Hint>Disabled adjustments contribute 0%. A date-range override is applied last and may exceed the configured bounds.</Hint>
  </div>;
}

export function PropertyEditor({ property, globalConfiguration, pricingGroups }: { property: Property; globalConfiguration: PricingConfiguration; pricingGroups: PricingGroup[] }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  const local = property.pricing_settings;
  const localUrgency = Object.fromEntries((local.urgency_adjustments ?? []).map(tier => [tier.maximum_days, tier.adjustment]));
  const effective = {
    ...globalConfiguration,
    ...local,
    urgency_adjustments: globalConfiguration.urgency_adjustments.map(tier => ({
      ...tier,
      adjustment: localUrgency[tier.maximum_days] ?? tier.adjustment,
    })),
  };
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget);
    const pricingSettings: Record<string, unknown> = {};
    const mode = String(form.get("base_price_mode") ?? "");
    if (mode) pricingSettings.base_price_mode = mode;
    const numericFields = ["manual_base_price", "market_price_adjustment", "competitor_weight", "pricing_group_weight", "neutral_demand_score", "demand_adjustment_slope", "minimum_demand_adjustment", "maximum_demand_adjustment"];
    for (const field of numericFields) {
      const value = parseOptionalNumber(form, field);
      if (value !== undefined) pricingSettings[field] = value;
    }
    for (const field of ["demand_adjustment_enabled", "urgency_adjustment_enabled"]) {
      const value = parseOptionalBoolean(form, field);
      if (value !== undefined) pricingSettings[field] = value;
    }
    const urgencyValues = effective.urgency_adjustments.map((tier, index) => ({
      maximum_days: tier.maximum_days,
      adjustment: parseOptionalNumber(form, `urgency_${index}`),
    })).filter(tier => tier.adjustment !== undefined);
    if (urgencyValues.length) pricingSettings.urgency_adjustments = urgencyValues;
    const payload = {
      active: form.get("active") === "on",
      pricing_group_id: Number(form.get("pricing_group_id")),
      min_price: Number(form.get("min_price")), max_price: Number(form.get("max_price")),
      rounding_increment: Number(form.get("rounding_increment")),
      pricing_settings: pricingSettings,
    };
    const response = await fetch(`/api/properties/${property.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    if (!response.ok) { setMessage((await response.json()).detail ?? "Save failed"); return; }
    setMessage("Saved"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}>
    <div className="policy-title"><div><h2>{property.name}</h2><span className="muted">BookingSite: {property.booking_site_listing_id ?? "Not mapped"}</span></div><label className="toggle"><input name="active" type="checkbox" defaultChecked={property.active}/> Pricing enabled</label></div>
    <label>Pricing group<select name="pricing_group_id" defaultValue={property.pricing_group_id}>{pricingGroups.map(group => <option value={group.id} key={group.id}>{group.name}</option>)}</select><Hint>Defines the competitor set and the properties included in this property&apos;s occupancy signal.</Hint></label>
    <p className="muted">Leave a pricing-engine field blank to inherit its global value. The placeholder shows the effective global value.</p>
    <h3>Base price</h3><div className="form-grid four">
      <label>Base price method<select name="base_price_mode" defaultValue={local.base_price_mode ?? ""}><option value="">Use global ({globalConfiguration.base_price_mode})</option><option value="market_median">Market median</option><option value="manual">Manual</option></select><Hint>Chooses whether the starting price comes from competitors or a fixed amount.</Hint></label>
      <label>Manual base price<input name="manual_base_price" type="number" min="1" defaultValue={local.manual_base_price ?? ""} placeholder={globalConfiguration.manual_base_price?.toString() ?? "Required in manual mode"}/><Hint>Fixed starting price in IDR when the method is Manual.</Hint></label>
      <label>Market offset<input name="market_price_adjustment" type="number" min="-0.99" step="0.01" defaultValue={local.market_price_adjustment ?? ""} placeholder={String(globalConfiguration.market_price_adjustment)}/><Hint>Relative difference from the median; −0.10 means 10% below market.</Hint></label>
    </div>
    <h3>Demand adjustment</h3><div className="form-grid four">
      <label>Use demand adjustment<select name="demand_adjustment_enabled" defaultValue={local.demand_adjustment_enabled == null ? "" : String(local.demand_adjustment_enabled)}><option value="">Use global ({globalConfiguration.demand_adjustment_enabled ? "enabled" : "disabled"})</option><option value="true">Enabled</option><option value="false">Disabled</option></select><Hint>When disabled, demand contributes 0% to the formula.</Hint></label>
      <label>Competitor weight<input name="competitor_weight" type="number" min="0" max="1" step="0.01" defaultValue={local.competitor_weight ?? ""} placeholder={String(globalConfiguration.competitor_weight)}/><Hint>Share of demand score driven by competitor unavailability.</Hint></label>
      <label>Pricing-group weight<input name="pricing_group_weight" type="number" min="0" max="1" step="0.01" defaultValue={local.pricing_group_weight ?? ""} placeholder={String(globalConfiguration.pricing_group_weight)}/><Hint>Share driven by occupancy among properties in this pricing group. Both weights must total 1.</Hint></label>
      <label>Neutral demand score<input name="neutral_demand_score" type="number" min="0" max="1" step="0.01" defaultValue={local.neutral_demand_score ?? ""} placeholder={String(globalConfiguration.neutral_demand_score)}/><Hint>Demand score at which the price adjustment is exactly 0%.</Hint></label>
      <label>Demand slope<input name="demand_adjustment_slope" type="number" min="0" step="0.01" defaultValue={local.demand_adjustment_slope ?? ""} placeholder={String(globalConfiguration.demand_adjustment_slope)}/><Hint>Controls how strongly price reacts above or below neutral demand.</Hint></label>
      <label>Minimum demand adjustment<input name="minimum_demand_adjustment" type="number" min="-1" max="0" step="0.01" defaultValue={local.minimum_demand_adjustment ?? ""} placeholder={String(globalConfiguration.minimum_demand_adjustment)}/><Hint>Maximum demand-driven discount, expressed as a decimal.</Hint></label>
      <label>Maximum demand adjustment<input name="maximum_demand_adjustment" type="number" min="0" max="1" step="0.01" defaultValue={local.maximum_demand_adjustment ?? ""} placeholder={String(globalConfiguration.maximum_demand_adjustment)}/><Hint>Maximum demand-driven markup, expressed as a decimal.</Hint></label>
    </div>
    <h3>Urgency adjustment</h3><div className="form-grid four">
      <label>Use urgency adjustment<select name="urgency_adjustment_enabled" defaultValue={local.urgency_adjustment_enabled == null ? "" : String(local.urgency_adjustment_enabled)}><option value="">Use global ({globalConfiguration.urgency_adjustment_enabled ? "enabled" : "disabled"})</option><option value="true">Enabled</option><option value="false">Disabled</option></select><Hint>Applies a date-proximity discount; disabled means 0%.</Hint></label>
      {effective.urgency_adjustments.map((tier, index) => <label key={tier.maximum_days}>0–{tier.maximum_days} days<input name={`urgency_${index}`} type="number" max="0" step="0.01" defaultValue={localUrgency[tier.maximum_days] ?? ""} placeholder={String(globalConfiguration.urgency_adjustments[index]?.adjustment ?? tier.adjustment)}/><Hint>Discount for an unsold night no more than {tier.maximum_days} days away.</Hint></label>)}
    </div>
    <h3>Bounds and data</h3><div className="form-grid four">
      <label>Minimum IDR<input name="min_price" type="number" min="1" defaultValue={property.min_price}/><Hint>Lower clamp applied before rounding.</Hint></label>
      <label>Maximum IDR<input name="max_price" type="number" min="1" defaultValue={property.max_price}/><Hint>Upper clamp applied before rounding.</Hint></label>
      <label>Pricing step IDR<input name="rounding_increment" type="number" min="1" defaultValue={property.rounding_increment}/><Hint>Final non-override price is rounded to this increment.</Hint></label>
    </div>
    <div className="form-actions"><button className="button">Save property</button><span className="muted">{message}</span></div>
  </form>;
}

export function PricingGroupEditor({ group }: { group: PricingGroup }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget);
    const payload = {
      name: String(form.get("name")),
      competitor_urls: String(form.get("competitor_urls") ?? "").split("\n").map(value => value.trim()).filter(Boolean),
    };
    const response = await fetch(`/api/pricing-groups/${group.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    setMessage(response.ok ? "Saved" : (await response.json()).detail ?? "Save failed"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}><div className="policy-title"><div><h2>{group.name}</h2><span className="muted">{group.property_count} properties</span></div></div>
    <div className="form-grid"><label>Group name<input name="name" required defaultValue={group.name}/><Hint>Human-readable name for comparable properties sharing competitors and occupancy.</Hint></label>
    <label className="wide">Competitor URLs<textarea name="competitor_urls" rows={8} defaultValue={group.competitor_urls.join("\n")} placeholder="One canonical Airbnb URL per line"/><Hint>Shared listings used for market median and competitor unavailability across this group.</Hint></label></div>
    <div className="form-actions"><button className="button">Save pricing group</button><span className="muted">{message}</span></div>
  </form>;
}

export function NewPricingGroupForm() {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Creating…"); const form = new FormData(event.currentTarget);
    const response = await fetch("/api/pricing-groups", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify({ name: form.get("name"), competitor_urls: [], pricing_settings: {} }) });
    setMessage(response.ok ? "Created" : (await response.json()).detail ?? "Create failed"); if (response.ok) event.currentTarget.reset(); router.refresh();
  }
  return <form className="card action-row" onSubmit={create}><label>New pricing group<input name="name" required placeholder="For example: Canggu 2-bedroom villas"/></label><button className="button">Create group</button><span className="muted">{message}</span></form>;
}

export function PricingConfigurationEditor({ configuration }: { configuration: PricingConfiguration }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget);
    const number = (name: string) => Number(form.get(name));
    const manualValue = String(form.get("manual_base_price") ?? "").trim();
    const payload = {
      base_price_mode: form.get("base_price_mode"), manual_base_price: manualValue ? Number(manualValue) : null,
      market_price_adjustment: number("market_price_adjustment"),
      demand_adjustment_enabled: form.get("demand_adjustment_enabled") === "on",
      urgency_adjustment_enabled: form.get("urgency_adjustment_enabled") === "on",
      competitor_weight: number("competitor_weight"), pricing_group_weight: number("pricing_group_weight"),
      neutral_demand_score: number("neutral_demand_score"), demand_adjustment_slope: number("demand_adjustment_slope"),
      minimum_demand_adjustment: number("minimum_demand_adjustment"), maximum_demand_adjustment: number("maximum_demand_adjustment"),
      urgency_adjustments: configuration.urgency_adjustments.map((tier, index) => ({ maximum_days: tier.maximum_days, adjustment: number(`urgency_${index}`) })),
    };
    const response = await fetch("/api/settings/pricing", { method: "PUT", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    setMessage(response.ok ? "Saved" : (await response.json()).detail ?? "Save failed"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}><h2>Global pricing defaults</h2><p className="muted">Properties inherit these values unless a property-specific override is entered.</p>
    <h3>Base price</h3><div className="form-grid four">
      <label>Base price method<select name="base_price_mode" defaultValue={configuration.base_price_mode}><option value="market_median">Market median</option><option value="manual">Manual</option></select><Hint>Default source of the starting price.</Hint></label>
      <label>Manual base price<input name="manual_base_price" type="number" min="1" defaultValue={configuration.manual_base_price ?? ""}/><Hint>Required when the global method is Manual.</Hint></label>
      <label>Market offset<input name="market_price_adjustment" type="number" min="-0.99" step="0.01" defaultValue={configuration.market_price_adjustment}/><Hint>−0.10 prices 10% below the competitor median.</Hint></label>
    </div>
    <h3>Demand</h3><div className="form-grid four">
      <label className="toggle lower"><input name="demand_adjustment_enabled" type="checkbox" defaultChecked={configuration.demand_adjustment_enabled}/> Enable demand adjustment<Hint>Uncheck to make demand adjustment 0% by default.</Hint></label>
      <label>Competitor weight<input name="competitor_weight" type="number" min="0" max="1" step="0.01" defaultValue={configuration.competitor_weight}/><Hint>Weight of competitor unavailability in demand score.</Hint></label>
      <label>Pricing-group weight<input name="pricing_group_weight" type="number" min="0" max="1" step="0.01" defaultValue={configuration.pricing_group_weight}/><Hint>Weight of occupancy inside the pricing group; weights must total 1.</Hint></label>
      <label>Neutral demand score<input name="neutral_demand_score" type="number" min="0" max="1" step="0.01" defaultValue={configuration.neutral_demand_score}/><Hint>Score producing no demand adjustment.</Hint></label>
      <label>Demand slope<input name="demand_adjustment_slope" type="number" min="0" step="0.01" defaultValue={configuration.demand_adjustment_slope}/><Hint>Price sensitivity to demand.</Hint></label>
      <label>Minimum adjustment<input name="minimum_demand_adjustment" type="number" min="-1" max="0" step="0.01" defaultValue={configuration.minimum_demand_adjustment}/><Hint>Lowest permitted demand adjustment.</Hint></label>
      <label>Maximum adjustment<input name="maximum_demand_adjustment" type="number" min="0" max="1" step="0.01" defaultValue={configuration.maximum_demand_adjustment}/><Hint>Highest permitted demand adjustment.</Hint></label>
    </div>
    <h3>Urgency</h3><div className="form-grid four">
      <label className="toggle lower"><input name="urgency_adjustment_enabled" type="checkbox" defaultChecked={configuration.urgency_adjustment_enabled}/> Enable urgency adjustment<Hint>Uncheck to make date proximity contribute 0%.</Hint></label>
      {configuration.urgency_adjustments.map((tier, index) => <label key={tier.maximum_days}>0–{tier.maximum_days} days<input name={`urgency_${index}`} type="number" max="0" step="0.01" defaultValue={tier.adjustment}/><Hint>Discount for dates within this lead-time tier.</Hint></label>)}
    </div>
    <div className="form-actions"><button className="button">Save global defaults</button><span className="muted">{message}</span></div>
  </form>;
}

export { FormulaCard };

export function PricingActions() {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function action(path: string) {
    setMessage("Running…"); const response = await fetch(path, { method: "POST", headers: { "X-CSRF-Token": csrf() } }); const body = await response.json();
    setMessage(response.ok ? `${body.optimized} recommendations generated` : body.detail); router.refresh();
  }
  return <div className="action-row"><button className="button" onClick={() => action("/api/pricing/run")}>Generate 365 days</button><span className="muted">{message}</span></div>;
}
