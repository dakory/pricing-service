import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";

type Listing = {
  id: number; property_name: string | null; listing_id: string; channel_type: string;
  readonly: boolean; imported_at: string;
};
type Night = { date: string; price: number | null; inventory: number | null; minimum_stay: number | null; imported_at: string };

async function api(path: string) {
  const cookie = await cookies();
  const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}${path}`, {
    headers: { cookie: cookie.toString() }, cache: "no-store",
  });
  if (response.status === 401) redirect("/login");
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  return response.json();
}

const idr = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });

export default async function HostexCalendars({
  searchParams,
}: {
  searchParams: Promise<{ listing?: string; channel?: string; start?: string; end?: string }>;
}) {
  const params = await searchParams;
  const listings: Listing[] = await api("/api/hostex/listings");
  const selected = listings.find(item => item.listing_id === params.listing && item.channel_type === params.channel) ?? listings[0];
  const today = new Date().toISOString().slice(0, 10);
  const endDefault = new Date(Date.now() + 31 * 86400000).toISOString().slice(0, 10);
  const start = params.start ?? today;
  const end = params.end ?? endDefault;
  const nights: Night[] = selected ? await api(`/api/hostex/calendar?listing_id=${encodeURIComponent(selected.listing_id)}&channel_type=${encodeURIComponent(selected.channel_type)}&start=${start}&end=${end}`) : [];

  return <Shell>
    <h1>Hostex calendars</h1>
    <p className="muted">Read-only prices and availability from the latest Hostex import.</p>
    <div className="hostex-layout">
      <div className="card listing-list">
        <b>Imported listings ({listings.length})</b>
        <div className="listing-links">{listings.map(item =>
          <Link className={selected?.id === item.id ? "listing-link selected" : "listing-link"} key={item.id}
            href={`/hostex?listing=${encodeURIComponent(item.listing_id)}&channel=${encodeURIComponent(item.channel_type)}&start=${start}&end=${end}`}>
            <span>{item.property_name ?? "Unmapped property"}</span><small>{item.channel_type} · {item.listing_id}</small>
          </Link>)}</div>
      </div>
      <div>
        {selected && <div className="toolbar"><div><b>{selected.property_name}</b><div className="muted">{selected.channel_type} · {selected.listing_id}</div></div>
          <form className="date-filter"><input aria-label="Start date" name="start" type="date" defaultValue={start}/><input aria-label="End date" name="end" type="date" defaultValue={end}/><input name="listing" type="hidden" value={selected.listing_id}/><input name="channel" type="hidden" value={selected.channel_type}/><button className="button">Show dates</button></form></div>}
        <div className="card calendar">{nights.length ? <table><thead><tr><th>Date</th><th>Nightly price</th><th>Inventory</th><th>Minimum stay</th></tr></thead>
          <tbody>{nights.map(night => <tr key={night.date}><td>{night.date}</td><td className="price">{night.price == null ? "—" : idr.format(night.price)}</td><td>{night.inventory == null ? "—" : night.inventory}</td><td>{night.minimum_stay == null ? "—" : `${night.minimum_stay} nights`}</td></tr>)}</tbody></table>
          : <div className="empty">No imported calendar entries in this date range.</div>}</div>
      </div>
    </div>
  </Shell>;
}
