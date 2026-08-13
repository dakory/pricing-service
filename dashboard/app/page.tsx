"use client";

import { useEffect, useMemo, useState } from "react";
import { Shell } from "./components/Shell";

type Property = { id:number; name:string; pricing_group_id:number; booking_site_listing_id:string|null };
type Day = { property_id:number; property_name:string; pricing_group_id:number; stay_date:string; available:boolean; inventory:number|null; minimum_stay:number|null; current_price:number|null; recommended_price:number|null; difference:number|null; difference_percentage:number|null; override:Record<string, unknown>|null; anchor:Record<string, unknown>|null; warnings:string[]; explanation:Record<string, unknown> };
type CalendarResponse = { properties:Property[]; days:Day[]; start:string; end:string };

const today = () => new Intl.DateTimeFormat("en-CA", { timeZone:"Asia/Makassar", year:"numeric", month:"2-digit", day:"2-digit" }).format(new Date());
const addDays = (value:string, days:number) => { const d = new Date(`${value}T00:00:00Z`); d.setUTCDate(d.getUTCDate()+days); return d.toISOString().slice(0,10); };
const money = (value:number|null) => value == null ? "—" : `Rp ${new Intl.NumberFormat("id-ID", { maximumFractionDigits:0 }).format(value)}`;
const shortDate = (value:string) => new Intl.DateTimeFormat("en-US", { weekday:"short", day:"numeric", month:"short", timeZone:"UTC" }).format(new Date(`${value}T00:00:00Z`));
const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");

export default function CalendarPage() {
  const [range, setRange] = useState({ start: today(), end: addDays(today(), 43) });
  const [data, setData] = useState<CalendarResponse>({ properties:[], days:[], start:"", end:"" });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [selectedProperty, setSelectedProperty] = useState<Property|null>(null);
  const [actionsOpen, setActionsOpen] = useState(false);

  async function load(nextRange = range) {
    setLoading(true);
    const response = await fetch(`/api/pricing-calendar?start=${nextRange.start}&end=${nextRange.end}`, { cache:"no-store" });
    if (response.status === 401) { window.location.href = "/login"; return; }
    if (response.ok) setData(await response.json());
    setLoading(false);
  }
  useEffect(() => { void load(); }, []);

  const dates = useMemo(() => { const result:string[]=[]; let cursor=range.start; while(cursor<=range.end){ result.push(cursor); cursor=addDays(cursor,1); } return result; }, [range]);
  const byKey = useMemo(() => new Map(data.days.map(day => [`${day.property_id}:${day.stay_date}`, day])), [data.days]);
  const groups = useMemo(() => { const map = new Map<number, Property[]>(); data.properties.forEach(property => map.set(property.pricing_group_id, [...(map.get(property.pricing_group_id)??[]), property])); return map; }, [data.properties]);

  async function action(path:string, label:string) {
    setMessage(`${label}…`);
    const response = await fetch(path, { method:"POST", headers:{"X-CSRF-Token":csrf()} });
    const body = await response.json().catch(() => ({}));
    setMessage(response.ok ? `${label} completed` : body.detail ?? `${label} failed`);
    if (response.ok && path.includes("booking-site")) await load();
  }
  function extend(direction:"past"|"future") {
    const next = direction === "future" ? { start:range.start, end:addDays(range.end,30) } : { start:addDays(range.start,-30), end:range.end };
    setRange(next); void load(next);
  }

  return <Shell><div className="calendar-page">
    <header className="page-head calendar-head"><div><div className="eyebrow">Portfolio</div><h1>Calendar</h1><p className="muted">BookingSite prices and recommendations by property.</p></div><div className="calendar-actions"><button className="button secondary" onClick={() => setActionsOpen(true)}>Actions</button><button className="button" onClick={() => void action("/api/pricing/run", "Generating recommendations")}>Generate recommendations</button></div></header>
    {message && <div className="toast card">{message}</div>}
    <div className="calendar-toolbar"><button className="button secondary" onClick={() => extend("past")}>← Earlier</button><span className="date-range">{shortDate(range.start)} — {shortDate(range.end)}</span><button className="button secondary" onClick={() => extend("future")}>Later →</button><button className="button secondary" onClick={() => { const next={start:today(),end:addDays(today(),43)}; setRange(next); void load(next); }}>Today</button></div>
    <div className="calendar-frame card"><div className="calendar-scroll"><table className="pricing-grid"><thead><tr><th className="property-sticky">Property</th>{dates.map(date => <th key={date}>{shortDate(date)}</th>)}</tr></thead><tbody>{Array.from(groups.entries()).map(([groupId, properties]) => <>{<tr className="group-row" key={`group-${groupId}`}><th className="property-sticky" colSpan={dates.length+1}>Pricing group {groupId}</th></tr>}{properties.map(property => <tr key={property.id}><th className="property-sticky property-name" onClick={() => setSelectedProperty(property)}><span className="property-dot" />{property.name}</th>{dates.map(date => { const day=byKey.get(`${property.id}:${date}`); return <td key={date} className={`${day?.available ? "" : "blocked"} ${day?.override ? "has-override" : ""}`} title={day?.explanation ? JSON.stringify(day.explanation) : undefined}>{day?.available ? <><strong>{money(day.current_price)}</strong>{day.recommended_price != null && <small className={day.difference && day.difference < 0 ? "negative" : "positive"}>{money(day.recommended_price)} {day.difference_percentage == null ? "" : `${day.difference_percentage>=0?"+":""}${(day.difference_percentage*100).toFixed(1)}%`}</small>}</> : <span className="unavailable">Unavailable</span>}</td>; })}</tr>)}</>)}</tbody></table>{loading && <div className="calendar-loading">Loading calendar…</div>}{!loading && !data.properties.length && <div className="empty">No active properties are available.</div>}</div></div>
    {selectedProperty && <aside className="drawer"><button className="drawer-close" onClick={() => setSelectedProperty(null)}>×</button><div className="eyebrow">Property settings</div><h2>{selectedProperty.name}</h2><p className="muted">BookingSite listing {selectedProperty.booking_site_listing_id ?? "not mapped"}</p><div className="drawer-section"><label>Base price mode<select defaultValue="market_median"><option value="market_median">Market median</option><option value="manual">Manual</option></select></label><label>Minimum competitor count<input type="number" defaultValue="10" min="1" max="30" /></label><label>Minimum price<input type="number" placeholder="Rp" /></label><label>Maximum price<input type="number" placeholder="Rp" /></label></div><button className="button" onClick={() => { setMessage("Property settings saved"); setSelectedProperty(null); }}>Save property</button></aside>}
    {actionsOpen && <aside className="drawer actions-drawer"><button className="drawer-close" onClick={() => setActionsOpen(false)}>×</button><div className="eyebrow">Actions</div><h2>Pricing operations</h2><div className="action-block"><b>Fetch current prices</b><p className="muted">Refresh BookingSite calendars only.</p><button className="button secondary" onClick={() => void action(`/api/imports/hostex/booking-site?start=${today()}&end=${addDays(today(),365)}`, "Fetching current prices")}>Fetch now</button></div><div className="action-block"><b>Generate recommendations</b><p className="muted">Calculate recommendations without publishing.</p><button className="button" onClick={() => void action("/api/pricing/run", "Generating recommendations")}>Generate</button></div><div className="action-block"><b>Apply recommendations</b><p className="muted">Review and confirm before publishing prices.</p><button className="button accent" disabled>Review changes</button></div></aside>}
  </div></Shell>;
}
