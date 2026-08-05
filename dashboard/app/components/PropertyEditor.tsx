"use client";

import { FormEvent, ReactNode, useState } from "react";
import { useRouter } from "next/navigation";

type UrgencyRule = { minimum_days: number; maximum_days: number; adjustment: number };
type PricingConfiguration = {
  base_price_mode: "market_median" | "manual";
  manual_base_price: number | null;
  guest_to_host_price_factor: number;
  market_positioning_factor: number;
  minimum_competitor_count: number;
  urgency_adjustment_enabled: boolean;
  urgency_adjustments: UrgencyRule[];
};
type Property = {
  id: number; name: string; active: boolean; booking_site_listing_id: string | null; pricing_group_id: number;
  min_price: number; max_price: number; rounding_increment: number;
  pricing_settings: Partial<PricingConfiguration>;
};
type PricingGroup = { id: number; name: string; competitor_urls: string[]; property_count: number; pricing_settings: Partial<PricingConfiguration> };

const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
const numberOrUndefined = (form: FormData, name: string) => { const value = String(form.get(name) ?? "").trim(); return value === "" ? undefined : Number(value); };
function Hint({ children }: { children: ReactNode }) { return <small className="muted">{children}</small>; }

function RuleEditor({ rules, setRules }: { rules: UrgencyRule[]; setRules: (rules: UrgencyRule[]) => void }) {
  return <div className="form-grid four">
    {rules.map((rule, index) => <div className="card" key={`${index}-${rule.minimum_days}`}>
      <label>From day<input type="number" min="0" value={rule.minimum_days} onChange={event => setRules(rules.map((item, i) => i === index ? { ...item, minimum_days: Number(event.target.value) } : item))} /></label>
      <label>To day<input type="number" min="0" value={rule.maximum_days} onChange={event => setRules(rules.map((item, i) => i === index ? { ...item, maximum_days: Number(event.target.value) } : item))} /></label>
      <label>Discount<input type="number" min="-1" max="0" step="0.01" value={rule.adjustment} onChange={event => setRules(rules.map((item, i) => i === index ? { ...item, adjustment: Number(event.target.value) } : item))} /><Hint>Only discounts, e.g. -0.10 = 10%.</Hint></label>
      <button type="button" className="button secondary" onClick={() => setRules(rules.filter((_, i) => i !== index))}>Remove</button>
    </div>)}
    {rules.length < 10 && <button type="button" className="button secondary" onClick={() => setRules([...rules, { minimum_days: rules.length ? rules[rules.length - 1].maximum_days + 1 : 0, maximum_days: rules.length ? rules[rules.length - 1].maximum_days + 4 : 3, adjustment: 0 }])}>Add urgency rule</button>}
  </div>;
}

function FormulaCard() {
  return <div className="card"><h2>How the price is calculated</h2>
    <p><code>manual override → manual base price or market price → urgency → round → min/max</code></p>
    <p><code>estimated host median = Airbnb guest median × guest-to-host factor</code></p>
    <p><code>base price = estimated host median × market positioning factor</code></p>
    <p><code>raw = base price × (1 + urgency adjustment)</code></p>
    <p><code>final = clamp(round(raw, pricing step), minimum, maximum)</code></p>
    <Hint>Date overrides bypass rounding and bounds; unavailable dates are always skipped.</Hint>
  </div>;
}

export function PropertyEditor({ property, globalConfiguration, pricingGroups }: { property: Property; globalConfiguration: PricingConfiguration; pricingGroups: PricingGroup[] }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  const local = property.pricing_settings;
  const [urgencyOverride, setUrgencyOverride] = useState<UrgencyRule[] | null>(local.urgency_adjustments ? [...local.urgency_adjustments] : null);
  const effectiveRules = urgencyOverride ?? globalConfiguration.urgency_adjustments;
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget); const pricingSettings: Record<string, unknown> = {};
    const mode = String(form.get("base_price_mode") ?? ""); if (mode) pricingSettings.base_price_mode = mode;
    for (const field of ["manual_base_price", "market_positioning_factor", "minimum_competitor_count"]) { const value = numberOrUndefined(form, field); if (value !== undefined) pricingSettings[field] = value; }
    const urgencyEnabled = String(form.get("urgency_adjustment_enabled") ?? ""); if (urgencyEnabled) pricingSettings.urgency_adjustment_enabled = urgencyEnabled === "true";
    if (urgencyOverride) pricingSettings.urgency_adjustments = urgencyOverride;
    const payload = { active: form.get("active") === "on", pricing_group_id: Number(form.get("pricing_group_id")), min_price: Number(form.get("min_price")), max_price: Number(form.get("max_price")), rounding_increment: Number(form.get("rounding_increment")), pricing_settings: pricingSettings };
    const response = await fetch(`/api/properties/${property.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    if (!response.ok) { setMessage((await response.json()).detail ?? "Save failed"); return; } setMessage("Saved"); router.refresh();
  }
  return <form className="card policy" onSubmit={save}><div className="policy-title"><div><h2>{property.name}</h2><span className="muted">BookingSite: {property.booking_site_listing_id ?? "Not mapped"}</span></div><label className="toggle"><input name="active" type="checkbox" defaultChecked={property.active}/> Pricing enabled</label></div>
    <label>Pricing group<select name="pricing_group_id" defaultValue={property.pricing_group_id}>{pricingGroups.map(group => <option value={group.id} key={group.id}>{group.name}</option>)}</select><Hint>Controls which competitor listings are used for this property.</Hint></label>
    <p className="muted">Leave a field blank to inherit the global value. A property urgency list replaces the inherited list.</p>
    <h3>Base price</h3><div className="form-grid four">
      <label>Method<select name="base_price_mode" defaultValue={local.base_price_mode ?? ""}><option value="">Use global ({globalConfiguration.base_price_mode})</option><option value="market_median">Market</option><option value="manual">Manual</option></select><Hint>Choose market median or a fixed manual base.</Hint></label>
      <label>Manual base price<input name="manual_base_price" type="number" min="1" defaultValue={local.manual_base_price ?? ""} placeholder={String(globalConfiguration.manual_base_price ?? "Required in manual mode")}/><Hint>Fixed IDR starting price.</Hint></label>
      <label>Market positioning factor<input name="market_positioning_factor" type="number" min="0.01" step="0.01" defaultValue={local.market_positioning_factor ?? ""} placeholder={String(globalConfiguration.market_positioning_factor)}/><Hint>0.90 means 10% below market.</Hint></label>
      <label>Minimum competitor count<input name="minimum_competitor_count" type="number" min="1" max="30" defaultValue={local.minimum_competitor_count ?? ""} placeholder={String(globalConfiguration.minimum_competitor_count)}/><Hint>Prices below this count use the saved median.</Hint></label>
    </div>
    <h3>Urgency</h3><label>Use urgency<select name="urgency_adjustment_enabled" defaultValue={local.urgency_adjustment_enabled == null ? "" : String(local.urgency_adjustment_enabled)}><option value="">Use global ({globalConfiguration.urgency_adjustment_enabled ? "enabled" : "disabled"})</option><option value="true">Enabled</option><option value="false">Disabled</option></select><Hint>Optional proximity discounts; gaps are 0%.</Hint></label>
    {urgencyOverride ? <><RuleEditor rules={urgencyOverride} setRules={setUrgencyOverride}/><button type="button" className="button secondary" onClick={() => setUrgencyOverride(null)}>Use inherited rules</button></> : <button type="button" className="button secondary" onClick={() => setUrgencyOverride([...globalConfiguration.urgency_adjustments])}>Customize urgency rules</button>}
    <h3>Bounds and rounding</h3><div className="form-grid four"><label>Minimum IDR<input name="min_price" type="number" min="1" defaultValue={property.min_price}/><Hint>Lower clamp after rounding.</Hint></label><label>Maximum IDR<input name="max_price" type="number" min="1" defaultValue={property.max_price}/><Hint>Upper clamp after rounding.</Hint></label><label>Pricing step IDR<input name="rounding_increment" type="number" min="1" defaultValue={property.rounding_increment}/><Hint>Rounding increment before clamp.</Hint></label></div>
    <div className="form-actions"><button className="button">Save property</button><span className="muted">{message}</span></div>
  </form>;
}

export function PricingGroupEditor({ group }: { group: PricingGroup }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget); const count = numberOrUndefined(form, "minimum_competitor_count"); const payload = { name: String(form.get("name")), competitor_urls: String(form.get("competitor_urls") ?? "").split("\n").map(value => value.trim()).filter(Boolean), pricing_settings: count === undefined ? {} : { minimum_competitor_count: count } }; const response = await fetch(`/api/pricing-groups/${group.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) }); setMessage(response.ok ? "Saved" : (await response.json()).detail ?? "Save failed"); if (response.ok) router.refresh(); }
  return <form className="card policy" onSubmit={save}><div className="policy-title"><div><h2>{group.name}</h2><span className="muted">{group.property_count} properties</span></div></div><div className="form-grid"><label>Group name<input name="name" required defaultValue={group.name}/><Hint>Properties inherit group settings before global settings.</Hint></label><label>Minimum competitor count<input name="minimum_competitor_count" type="number" min="1" max="30" defaultValue={group.pricing_settings.minimum_competitor_count ?? ""} placeholder="Use global"/><Hint>Threshold for refreshing the saved market median.</Hint></label><label className="wide">Competitor URLs<textarea name="competitor_urls" rows={8} defaultValue={group.competitor_urls.join("\n")} placeholder="One canonical Airbnb URL per line"/></label></div><div className="form-actions"><button className="button">Save pricing group</button><span className="muted">{message}</span></div></form>;
}

export function NewPricingGroupForm() { const router = useRouter(); const [message, setMessage] = useState(""); async function create(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setMessage("Creating…"); const form = new FormData(event.currentTarget); const response = await fetch("/api/pricing-groups", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify({ name: form.get("name"), competitor_urls: [], pricing_settings: {} }) }); setMessage(response.ok ? "Created" : (await response.json()).detail ?? "Create failed"); if (response.ok) { event.currentTarget.reset(); router.refresh(); } } return <form className="card action-row" onSubmit={create}><label>New pricing group<input name="name" required placeholder="For example: Canggu villas"/></label><button className="button">Create group</button><span className="muted">{message}</span></form>; }

export function PricingConfigurationEditor({ configuration }: { configuration: PricingConfiguration }) {
  const router = useRouter(); const [message, setMessage] = useState(""); const [rules, setRules] = useState<UrgencyRule[]>([...configuration.urgency_adjustments]);
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setMessage("Saving…"); const form = new FormData(event.currentTarget); const manualValue = String(form.get("manual_base_price") ?? "").trim(); const payload = { base_price_mode: form.get("base_price_mode"), manual_base_price: manualValue ? Number(manualValue) : null, guest_to_host_price_factor: Number(form.get("guest_to_host_price_factor")), market_positioning_factor: Number(form.get("market_positioning_factor")), minimum_competitor_count: Number(form.get("minimum_competitor_count")), urgency_adjustment_enabled: form.get("urgency_adjustment_enabled") === "on", urgency_adjustments: rules }; const response = await fetch("/api/settings/pricing", { method: "PUT", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) }); setMessage(response.ok ? "Saved" : (await response.json()).detail ?? "Save failed"); if (response.ok) router.refresh(); }
  return <form className="card policy" onSubmit={save}><h2>Global pricing defaults</h2><p className="muted">Properties inherit these values unless overridden at group or property level.</p><h3>Base price</h3><div className="form-grid four"><label>Method<select name="base_price_mode" defaultValue={configuration.base_price_mode}><option value="market_median">Market median</option><option value="manual">Manual</option></select><Hint>Starting price source.</Hint></label><label>Manual base price<input name="manual_base_price" type="number" min="1" defaultValue={configuration.manual_base_price ?? ""}/><Hint>Required in Manual mode.</Hint></label><label>Guest-to-host factor<input name="guest_to_host_price_factor" type="number" min="0.01" step="0.001" defaultValue={configuration.guest_to_host_price_factor}/><Hint>Converts Airbnb guest median to estimated host revenue.</Hint></label><label>Market positioning factor<input name="market_positioning_factor" type="number" min="0.01" step="0.01" defaultValue={configuration.market_positioning_factor}/><Hint>0.90 means 10% below market.</Hint></label><label>Minimum competitor count<input name="minimum_competitor_count" type="number" min="1" max="30" defaultValue={configuration.minimum_competitor_count}/><Hint>Minimum prices needed to refresh the saved median.</Hint></label></div><h3>Urgency</h3><label className="toggle lower"><input name="urgency_adjustment_enabled" type="checkbox" defaultChecked={configuration.urgency_adjustment_enabled}/> Enable urgency discounts<Hint>Only configured ranges apply; gaps are 0%.</Hint></label><RuleEditor rules={rules} setRules={setRules}/><div className="form-actions"><button className="button">Save global defaults</button><span className="muted">{message}</span></div></form>;
}

export { FormulaCard };
export function PricingActions() { const router = useRouter(); const [message, setMessage] = useState(""); async function action(path: string) { setMessage("Running…"); const response = await fetch(path, { method: "POST", headers: { "X-CSRF-Token": csrf() } }); const body = await response.json(); setMessage(response.ok ? `${body.optimized} recommendations generated` : body.detail); router.refresh(); } return <div className="action-row"><button className="button" onClick={() => action("/api/pricing/run")}>Generate 365 days</button><span className="muted">{message}</span></div>; }
