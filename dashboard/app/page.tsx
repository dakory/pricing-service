import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "./components/Shell";

type Night = {
  property_name: string; date: string; actual_price: number | null; recommended_price: number;
  published_price: number | null; minimum_stay: number; explanation: Record<string, unknown>;
};

async function getCalendar(): Promise<Night[]> {
  const cookie = await cookies();
  const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}/api/calendar`, {
    headers: { cookie: cookie.toString() }, cache: "no-store",
  });
  if (response.status === 401) redirect("/login");
  if (!response.ok) return [];
  return response.json();
}

const idr = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });

export default async function Home() {
  const nights = await getCalendar();
  return (
    <Shell>
      <h1>Portfolio calendar</h1>
      <div className="muted">Twelve-month pricing recommendations in Asia/Makassar time.</div>
      <div className="stats">
        <div className="card stat"><span className="muted">Priced nights</span><b>{nights.length}</b></div>
        <div className="card stat"><span className="muted">Properties</span><b>{new Set(nights.map(n => n.property_name)).size}</b></div>
        <div className="card stat"><span className="muted">Overrides</span><b>{nights.filter(n => n.explanation.hard_override).length}</b></div>
        <div className="card stat"><span className="muted">Mode</span><b><span className="pill">Shadow</span></b></div>
      </div>
      <div className="toolbar"><b>Daily recommendations</b><span className="muted">Click an explanation in the API for full factors</span></div>
      <div className="card calendar">
        {nights.length ? <table><thead><tr><th>Date</th><th>Property</th><th>Current</th><th>Recommended</th><th>Published</th><th>Min stay</th><th>Why</th></tr></thead>
          <tbody>{nights.slice(0, 500).map((night) => <tr key={`${night.property_name}-${night.date}`}>
            <td>{night.date}</td><td>{night.property_name}</td><td>{night.actual_price ? idr.format(night.actual_price) : "—"}</td>
            <td className="price">{idr.format(night.recommended_price)}</td><td>{night.published_price ? idr.format(night.published_price) : "Shadow"}</td>
            <td>{night.minimum_stay} nights</td><td className="explain">Anchor {idr.format(Number(night.explanation.internal_anchor ?? 0))}; pace {Number(night.explanation.booking_pace_adjustment ?? 0) * 100}%</td>
          </tr>)}</tbody></table> : <div className="empty">No recommendations yet. Configure a property, then run the optimizer.</div>}
      </div>
    </Shell>
  );
}

