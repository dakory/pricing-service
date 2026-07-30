import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Shell } from "./components/Shell";
import { OverrideForm } from "./components/OverrideForm";
import { OverrideList } from "./components/OverrideList";

type Property = { id: number; name: string };
type Night = {
  property_id: number; property_name: string; date: string; actual_price: number | null; recommended_price: number;
  difference: number | null; difference_percentage: number | null; warnings: string[];
  explanation: Record<string, unknown>;
};
async function api(path: string) { const cookie = await cookies(); const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}${path}`, { headers: { cookie: cookie.toString() }, cache: "no-store" }); if (response.status === 401) redirect("/login"); if (!response.ok) return []; return response.json(); }
const idr = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
const pct = (value: number | null) => value == null ? "—" : `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%`;
const warningLabel: Record<string, string> = { stale_hostex_import: "Stale import", missing_hostex_calendar: "No calendar", missing_current_price: "No current price", large_price_change: "Large change", price_at_bound: "At bound" };
const businessToday = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Makassar", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
const addDays = (value: string, days: number) => { const parsed = new Date(`${value}T00:00:00Z`); parsed.setUTCDate(parsed.getUTCDate() + days); return parsed.toISOString().slice(0, 10); };

export default async function Home({ searchParams }: { searchParams: Promise<{ property?: string; start?: string; end?: string; warning?: string }> }) {
  const params = await searchParams; const today = businessToday(); const defaultEnd = addDays(today, 30);
  const start = params.start ?? today; const end = params.end ?? defaultEnd; const propertyId = params.property ? Number(params.property) : undefined;
  const properties: Property[] = await api("/api/properties");
  const overrides = await api("/api/overrides");
  const query = new URLSearchParams({ start, end }); if (propertyId) query.set("property_id", String(propertyId));
  let nights: Night[] = await api(`/api/calendar?${query}`); if (params.warning) nights = nights.filter(n => n.warnings.includes(params.warning!));
  const increases = nights.filter(n => (n.difference ?? 0) > 0).length; const decreases = nights.filter(n => (n.difference ?? 0) < 0).length; const unchanged = nights.filter(n => n.difference === 0).length; const warned = nights.filter(n => n.warnings.length).length;
  return <Shell><div className="page-head"><div><h1>Shadow recommendations</h1><div className="muted">Canonical BookingSite prices. Nothing on Hostex is modified.</div></div><span className="pill">Shadow only</span></div>
    <form className="card filters"><label>Property<select name="property" defaultValue={params.property ?? ""}><option value="">All properties</option>{properties.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>From<input name="start" type="date" defaultValue={start}/></label><label>To<input name="end" type="date" defaultValue={end}/></label><label>Warning<select name="warning" defaultValue={params.warning ?? ""}><option value="">All rows</option>{Object.entries(warningLabel).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label><button className="button">Apply filters</button><Link className="button secondary" href="/properties">Edit policies / run</Link></form>
    <div className="stats"><div className="card stat"><span className="muted">Displayed nights</span><b>{nights.length}</b></div><div className="card stat"><span className="muted">Increases</span><b>{increases}</b></div><div className="card stat"><span className="muted">Decreases / unchanged</span><b>{decreases} / {unchanged}</b></div><div className="card stat"><span className="muted">Warnings</span><b>{warned}</b></div></div>
    <div className="card calendar">{nights.length ? <table><thead><tr><th>Date</th><th>Property</th><th>Hostex current</th><th>Recommended</th><th>Difference</th><th>Warnings</th><th>Explanation</th></tr></thead><tbody>{nights.map(n => <tr key={`${n.property_id}-${n.date}`}><td>{n.date}</td><td>{n.property_name}</td><td>{n.actual_price == null ? "—" : idr.format(n.actual_price)}</td><td className="price">{idr.format(n.recommended_price)}</td><td className={(n.difference ?? 0) > 0 ? "positive" : (n.difference ?? 0) < 0 ? "negative" : ""}>{n.difference == null ? "—" : `${n.difference >= 0 ? "+" : ""}${idr.format(n.difference)} (${pct(n.difference_percentage)})`}</td><td>{n.warnings.length ? <div className="badges">{n.warnings.map(w => <span className="warning" key={w}>{warningLabel[w] ?? w}</span>)}</div> : <span className="muted">None</span>}</td><td><details><summary>Why this price</summary><div className="explanation-grid"><span>Base method</span><b>{String(n.explanation.base_price_mode ?? "—")}</b><span>Market median / offset</span><b>{n.explanation.market_price == null ? "—" : idr.format(Number(n.explanation.market_price))} / {pct(Number(n.explanation.market_price_adjustment ?? 0))}</b><span>Base price</span><b>{idr.format(Number(n.explanation.base_price ?? 0))}</b><span>Available competitors</span><b>{String(n.explanation.available_competitor_count ?? 0)}</b><span>Competitor unavailability</span><b>{pct(Number(n.explanation.competitor_unavailability ?? 0))}</b><span>Pricing-group occupancy</span><b>{pct(Number(n.explanation.pricing_group_occupancy ?? 0))}</b><span>Demand adjustment</span><b>{n.explanation.demand_adjustment_enabled ? pct(Number(n.explanation.demand_adjustment ?? 0)) : "Disabled"}</b><span>Days until stay</span><b>{String(n.explanation.days_until_stay ?? "—")}</b><span>Urgency adjustment</span><b>{n.explanation.urgency_adjustment_enabled ? pct(Number(n.explanation.urgency_adjustment ?? 0)) : "Disabled"}</b><span>Raw / bounded</span><b>{idr.format(Number(n.explanation.raw_price ?? 0))} / {idr.format(Number(n.explanation.bounded_price ?? 0))}</b><span>Date override</span><b>{n.explanation.manual_override == null ? "No" : idr.format(Number(n.explanation.manual_override))}</b></div></details></td></tr>)}</tbody></table> : <div className="empty">No recommendations in this range. Median mode requires competitor observations; manual mode does not.</div>}</div>
    <OverrideForm properties={properties} selectedId={propertyId} start={start} end={end}/><OverrideList overrides={overrides} properties={properties}/>
  </Shell>;
}
