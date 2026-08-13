import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { CompetitorScrapePanel } from "../components/CompetitorScrapePanel";
import { Shell } from "../components/Shell";

async function api(path: string) {
  const cookie = await cookies();
  const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}${path}`, {
    headers: { cookie: cookie.toString() },
    cache: "no-store",
  });
  if (response.status === 401) redirect("/login");
  if (!response.ok) return [];
  return response.json();
}

export default async function Competitors() {
  const [competitors, allRuns] = await Promise.all([
    api("/api/competitors"),
    api("/api/runs?limit=50"),
  ]);
  const runs = Array.isArray(allRuns)
    ? allRuns.filter((run: { kind: string }) => run.kind === "scrape")
    : [];
  return <Shell>
    <div className="eyebrow">Portfolio</div><h1>Competitor freshness</h1>
    <p className="muted">Monitor competitor availability, minNights and price freshness by pricing group.</p>
    <CompetitorScrapePanel competitors={competitors} initialRuns={runs}/>
  </Shell>;
}
