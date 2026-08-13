"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Shell } from "./components/Shell";

type Property = { id:number; name:string; pricing_group_id:number; booking_site_listing_id:string|null };
type Day = { property_id:number; property_name:string; pricing_group_id:number; stay_date:string; available:boolean; inventory:number|null; minimum_stay:number|null; current_price:number|null; recommended_price:number|null; difference:number|null; difference_percentage:number|null; override:Record<string, unknown>|null; anchor:Record<string, unknown>|null; warnings:string[]; explanation:Record<string, unknown> };
type CalendarResponse = { properties:Property[]; days:Day[]; start:string; end:string };
type Drawer = "actions"|"global"|"group"|"property"|null;

const apiPrefix = "";
const isoToday = () => new Intl.DateTimeFormat("en-CA", { timeZone:"Asia/Makassar", year:"numeric", month:"2-digit", day:"2-digit" }).format(new Date());
const addDays = (value:string, days:number) => { const date = new Date(`${value}T00:00:00Z`); date.setUTCDate(date.getUTCDate()+days); return date.toISOString().slice(0,10); };
const money = (value:number|null) => value == null ? "—" : `Rp ${new Intl.NumberFormat("id-ID", { maximumFractionDigits:0 }).format(value)}`;
const dateLabel = (value:string) => new Intl.DateTimeFormat("en-US", { weekday:"short", day:"numeric", month:"short", timeZone:"UTC" }).format(new Date(`${value}T00:00:00Z`));
const monthLabel = (value:string) => new Intl.DateTimeFormat("en-US", { month:"long", year:"numeric", timeZone:"UTC" }).format(new Date(`${value}T00:00:00Z`));
const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");

function Drawer({ children, open, onClose, width=460 }: { children:React.ReactNode; open:boolean; onClose:()=>void; width?:number }) {
  return <><div className={`prototype-scrim ${open ? "open" : ""}`} onClick={onClose} /><aside className={`prototype-drawer ${open ? "open" : ""}`} style={{ width }}><button className="prototype-close" onClick={onClose} aria-label="Close">×</button>{children}</aside></>;
}

export default function CalendarPage() {
  const initialStart = isoToday();
  const [range, setRange] = useState({ start:initialStart, end:addDays(initialStart,43) });
  const [data, setData] = useState<CalendarResponse>({ properties:[], days:[], start:"", end:"" });
  const [loading, setLoading] = useState(true);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const [selectedProperty, setSelectedProperty] = useState<Property|null>(null);
  const [selectedGroup, setSelectedGroup] = useState<number|null>(null);
  const [selection, setSelection] = useState<{start:string; end:string; minProperty:number; maxProperty:number}|null>(null);
  const [selectionAnchor, setSelectionAnchor] = useState<{date:string; property:number}|null>(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState<string|null>(null);
  const cache = useRef(new Map<string,Day>());
  const scrollRef = useRef<HTMLDivElement>(null);

  async function load(next=range) {
    setLoading(true);
    const response = await fetch(`${apiPrefix}/api/pricing-calendar?start=${next.start}&end=${next.end}`, { cache:"no-store" });
    if (response.status === 401) { window.location.href="/login"; return; }
    if (response.ok) {
      const payload:CalendarResponse = await response.json();
      payload.days.forEach(day => cache.current.set(`${day.property_id}:${day.stay_date}`, day));
      setData({ ...payload, days:Array.from(cache.current.values()).filter(day => day.stay_date>=next.start && day.stay_date<=next.end) });
    }
    setLoading(false);
  }
  useEffect(() => { void load(); }, []);

  const dates = useMemo(() => { const values:string[]=[]; let cursor=range.start; while(cursor<=range.end){ values.push(cursor); cursor=addDays(cursor,1); } return values; }, [range]);
  const dayMap = useMemo(() => new Map(data.days.map(day => [`${day.property_id}:${day.stay_date}`,day])), [data.days]);
  const groups = useMemo(() => { const result:{id:number; properties:Property[]}[]=[]; data.properties.forEach(property => { let group=result.find(item=>item.id===property.pricing_group_id); if(!group){group={id:property.pricing_group_id,properties:[]};result.push(group);} group.properties.push(property); }); return result; }, [data.properties]);
  const rows = useMemo(() => groups.flatMap(group => [{ type:"group" as const, group }, ...group.properties.map(property => ({ type:"property" as const, property }))]), [groups]);
  const gridColumns = `280px repeat(${dates.length}, 96px)`;

  function clickCell(propertyIndex:number, date:string) {
    if (!selectionAnchor) { setSelectionAnchor({ property:propertyIndex, date }); setSelection({ start:date, end:date, minProperty:propertyIndex, maxProperty:propertyIndex }); return; }
    setSelection({ start:selectionAnchor.date < date ? selectionAnchor.date : date, end:selectionAnchor.date > date ? selectionAnchor.date : date, minProperty:Math.min(selectionAnchor.property,propertyIndex), maxProperty:Math.max(selectionAnchor.property,propertyIndex) });
    setSelectionAnchor(null);
  }
  function setNoticeFor(text:string) { setNotice(text); window.setTimeout(() => setNotice(""), 2800); }
  async function action(path:string, label:string) {
    setBusy(label);
    const response = await fetch(path, { method:"POST", headers:{"X-CSRF-Token":csrf()} });
    const body = await response.json().catch(() => ({}));
    setBusy(null); setNoticeFor(response.ok ? label : body.detail ?? `${label} failed`);
    if (response.ok && (path.includes("booking-site") || path.includes("pricing/run") || path.includes("pricing/publish"))) await load();
  }
  function moveWindow(direction:"back"|"forward") { const next=direction==="back" ? {start:addDays(range.start,-30),end:range.end} : {start:range.start,end:addDays(range.end,30)}; setRange(next); void load(next); }
  function openProperty(property:Property) { setSelectedProperty(property); setDrawer("property"); }
  function openGroup(group:number) { setSelectedGroup(group); setDrawer("group"); }

  return <Shell><main className="prototype-dashboard">
    <header className="prototype-topbar"><div><div className="prototype-kicker">Portfolio</div><h1>Calendar</h1></div><div className="prototype-top-actions"><button className="prototype-button secondary" onClick={() => setDrawer("global")}>Global settings</button><button className="prototype-button secondary" onClick={() => setDrawer("actions")}>Actions</button></div></header>
    <div className="prototype-calendar-toolbar"><button className="prototype-pill" onClick={() => { const next={start:isoToday(),end:addDays(isoToday(),43)}; setRange(next); void load(next); }}>Today</button><button className="prototype-pill" onClick={() => moveWindow("back")}>‹</button><span>{monthLabel(range.start)}{monthLabel(range.start)!==monthLabel(range.end) ? ` — ${monthLabel(range.end)}` : ""}</span><button className="prototype-pill" onClick={() => moveWindow("forward")}>›</button><span className="prototype-toolbar-spacer" /><span className="prototype-date-note">{dates.length} dates loaded</span></div>
    {notice && <div className="prototype-toast">{notice}</div>}
    {selection && <div className="prototype-selection"><b>{dateLabel(selection.start)} — {dateLabel(selection.end)}</b><span>{selection.maxProperty-selection.minProperty+1} properties</span><button className="prototype-button accent" onClick={() => setDrawer("actions")}>Set price</button><button className="prototype-icon-button" onClick={() => {setSelection(null);setSelectionAnchor(null);}}>×</button></div>}
    <div className="prototype-calendar-shell"><div className="prototype-calendar-scroll" ref={scrollRef}><div className="prototype-grid" style={{ gridTemplateColumns:gridColumns }}>
      <div className="prototype-corner">{data.properties.length} Properties</div>
      {dates.map((date,index) => <div className={`prototype-month-cell ${index===0 || date.endsWith("-01") ? "month-start" : ""}`} key={`month-${date}`}>{index===0 || date.endsWith("-01") ? monthLabel(date) : ""}</div>)}
      <div className="prototype-property-header">Search listings...</div>{dates.map(date => <div className="prototype-date-header" key={`date-${date}`}><span>{new Intl.DateTimeFormat("en-US",{weekday:"narrow",timeZone:"UTC"}).format(new Date(`${date}T00:00:00Z`))}</span><b>{Number(date.slice(-2))}</b></div>)}
      {rows.map((row,rowIndex) => row.type==="group" ? <><button className="prototype-group-label" key={`group-label-${row.group.id}`} onClick={() => openGroup(row.group.id)}>Pricing group {row.group.id}<span>{row.group.properties.length} properties</span></button>{dates.map(date => <div className="prototype-group-band" key={`group-band-${row.group.id}-${date}`} />)}</> : <><button className="prototype-property-label" key={`property-label-${row.property.id}`} onClick={() => openProperty(row.property)}><span className="prototype-property-color" /><span><b>{row.property.name}</b><small>IDR (Rp)</small></span></button>{dates.map((date,dateIndex) => { const day=dayMap.get(`${row.property.id}:${date}`); const propertyIndex=data.properties.findIndex(item=>item.id===row.property.id); const selected=selection && propertyIndex>=selection.minProperty && propertyIndex<=selection.maxProperty && date>=selection.start && date<=selection.end; return <div className={`prototype-price-cell ${day?.available ? "" : "unavailable"} ${selected ? "selected" : ""}`} key={`${row.property.id}-${date}`} onClick={() => day?.available && clickCell(propertyIndex,date)}>{day?.available ? <><b>{money(day.current_price)}</b>{day.recommended_price!=null && <small className={day.difference!=null && day.difference<0 ? "down" : "up"}>{money(day.recommended_price)} {day.difference_percentage==null ? "" : `${day.difference_percentage>=0?"+":""}${(day.difference_percentage*100).toFixed(1)}%`}</small>}{day.explanation && Object.keys(day.explanation).length>0 && <span className="prototype-tooltip"><strong>Why this price</strong><br />Source: {String(day.explanation.price_source??"—")}<br />Base: {money(Number(day.explanation.base_price??0))}<br />Urgency: {day.explanation.urgency_adjustment_applied ? `${Number(day.explanation.urgency_adjustment??0)*100}%` : "Not applied"}<br />Final: {money(Number(day.explanation.final_price??day.recommended_price??0))}</span>}</> : <span className="prototype-blocked">Unavailable</span>}</div>; })}</>)}
    </div>{loading && <div className="prototype-loading">Loading calendar…</div>}</div></div>
    <Drawer open={drawer==="actions"} onClose={() => setDrawer(null)}><div className="prototype-drawer-kicker">Actions</div><h2>Pricing operations</h2><p className="prototype-muted">Run operations against the connected BookingSite and pricing engine.</p><div className="prototype-action-card"><b>Fetch current prices</b><span>BookingSite calendar only</span><button className="prototype-button secondary" disabled={!!busy} onClick={() => void action(`/api/imports/hostex/booking-site?start=${isoToday()}&end=${addDays(isoToday(),365)}`, "Prices fetched from Hostex")}>{busy==="Prices fetched from Hostex" ? "Fetching…" : "Fetch current prices"}</button></div><div className="prototype-action-card"><b>Refresh competitor data</b><span>Update monitored competitor calendars</span><button className="prototype-button secondary" disabled>Refresh competitor data</button></div><div className="prototype-action-card"><b>Generate price recommendations</b><span>Calculate without changing Hostex</span><button className="prototype-button secondary" disabled={!!busy} onClick={() => void action("/api/pricing/run", "Price recommendations generated")}>{busy==="Price recommendations generated" ? "Generating…" : "Generate price recommendations"}</button></div><div className="prototype-action-card"><b>Apply prices</b><span>Publish recommendations to BookingSite</span><button className="prototype-button accent" disabled={!!busy} onClick={() => void action("/api/pricing/publish", "Prices applied to your calendar")}>{busy==="Prices applied to your calendar" ? "Applying…" : "Apply prices"}</button></div></Drawer>
    <Drawer open={drawer==="global"} onClose={() => setDrawer(null)}><div className="prototype-drawer-kicker">Pricing defaults</div><h2>Global settings</h2><p className="prototype-muted">Defaults every group and property inherit from.</p><div className="prototype-form-section"><label>Guest-to-host factor<input defaultValue="0.839" /></label><h3>Base price</h3><div className="prototype-segmented"><button className="active">Market median</button><button>Manual</button></div><label>Market positioning factor<input defaultValue="1.0" /></label><label>Minimum competitor count<input defaultValue="10" type="number" /></label><h3>Discounts by days left until stay</h3><label className="prototype-switch"><input type="checkbox" defaultChecked /> Enable urgency adjustments</label><div className="prototype-urgency-chart"><i /><i /><i /><i /></div>{["0–3 · -15%","4–7 · -10%","8–14 · -5%","15–30 · -2%"].map(rule => <div className="prototype-rule" key={rule}>{rule}<input type="range" min="0" max="50" defaultValue="10" /></div>)}<h3>Bounds and rounding</h3><label>Minimum price<input placeholder="Rp" /></label><label>Maximum price<input placeholder="Rp" /></label><label>Round to nearest<input placeholder="Rp" /></label></div><button className="prototype-button accent full" onClick={() => {setDrawer(null);setNoticeFor("Global settings saved");}}>Save</button></Drawer>
    <Drawer open={drawer==="group"} onClose={() => setDrawer(null)} width={400}><div className="prototype-drawer-kicker">Pricing group</div><h2>Group {selectedGroup}</h2><p className="prototype-muted">Properties in this group inherit these settings.</p><div className="prototype-chip-row">{groups.find(group=>group.id===selectedGroup)?.properties.map(property => <span key={property.id}>{property.name}</span>)}</div><label>Minimum competitor count<input defaultValue="10" type="number" /></label><label>Competitor URLs<textarea rows={8} placeholder="One canonical Airbnb URL per line" /></label><button className="prototype-button accent full" onClick={() => {setDrawer(null);setNoticeFor("Pricing group saved");}}>Save</button></Drawer>
    <Drawer open={drawer==="property"} onClose={() => setDrawer(null)}><div className="prototype-drawer-kicker">Property settings</div><h2>{selectedProperty?.name}</h2><p className="prototype-muted">{selectedProperty?.booking_site_listing_id ? `BookingSite listing ${selectedProperty.booking_site_listing_id}` : "BookingSite listing not mapped"}</p><label className="prototype-switch"><input type="checkbox" defaultChecked /> Suggest pricing</label><h3>Base price</h3><div className="prototype-segmented"><button className="active">Market median</button><button>Manual</button></div><label>Market positioning factor<input defaultValue="1.0" /></label><label>Minimum competitor count<input defaultValue="10" type="number" /></label><h3>Discounts by days left until stay</h3><label className="prototype-switch"><input type="checkbox" defaultChecked /> Enable urgency adjustments</label><div className="prototype-urgency-chart"><i /><i /><i /><i /></div><h3>Bounds and rounding</h3><label>Minimum price<input placeholder="Rp" /></label><label>Maximum price<input placeholder="Rp" /></label><label>Round to nearest<input placeholder="Rp" /></label><button className="prototype-button accent full" onClick={() => {setDrawer(null);setNoticeFor("Property settings saved");}}>Save</button></Drawer>
  </main></Shell>;
}
