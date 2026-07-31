"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Competitor = {
  id: number;
  pricing_group_name: string;
  canonical_url: string;
  external_listing_id: string;
  current_minimum_stay: number | null;
  last_scraped_at: string | null;
  last_error: string | null;
};
type Run = {
  id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  summary: Record<string, unknown>;
  error: string | null;
};

const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
const isoDate = (date: Date) => date.toISOString().slice(0, 10);

export function CompetitorScrapePanel({ competitors, initialRuns }: { competitors: Competitor[]; initialRuns: Run[] }) {
  const router = useRouter();
  const today = isoDate(new Date());
  const nextWeek = new Date(); nextWeek.setUTCDate(nextWeek.getUTCDate() + 6);
  const [message, setMessage] = useState("");
  const [activeRunId, setActiveRunId] = useState<number | null>(
    initialRuns.find(run => run.status === "running")?.id ?? null,
  );

  useEffect(() => {
    if (!activeRunId) return;
    const timer = window.setInterval(async () => {
      const response = await fetch(`/api/competitor-scrapes/${activeRunId}`);
      if (!response.ok) return;
      const run = await response.json();
      if (run.status !== "running") {
        setActiveRunId(null);
        setMessage(run.error ?? run.summary?.result_status ?? run.status);
        router.refresh();
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [activeRunId, router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("Starting…");
    const form = new FormData(event.currentTarget);
    const payload = {
      competitor_listing_id: Number(form.get("competitor_listing_id")),
      start_date: form.get("start_date"),
      end_date: form.get("end_date"),
      force_refresh: form.get("force_refresh") === "on",
    };
    const response = await fetch("/api/competitor-scrapes", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      setMessage(body.detail ?? "Collection could not be started");
      router.refresh();
      return;
    }
    setMessage(body.status === "skipped" ? "All selected dates are fresh." : "Collector is running…");
    if (body.status === "running") setActiveRunId(body.run_id);
    router.refresh();
  }

  return <>
    <form className="card filters competitor-launch" onSubmit={submit}>
      <label>Competitor<select name="competitor_listing_id" required disabled={!competitors.length}>
        {competitors.map(item => <option value={item.id} key={item.id}>{item.pricing_group_name} · {item.external_listing_id}</option>)}
      </select></label>
      <label>From<input name="start_date" type="date" defaultValue={today} required/></label>
      <label>To<input name="end_date" type="date" defaultValue={isoDate(nextWeek)} required/></label>
      <label className="toggle lower"><input name="force_refresh" type="checkbox"/> Force refresh</label>
      <button className="button" disabled={!competitors.length || activeRunId !== null}>{activeRunId ? "Running…" : "Start collection"}</button>
      <span className={message.toLowerCase().includes("error") ? "error" : "muted"}>{message}</span>
    </form>
    {!competitors.length ? <div className="card empty">Add canonical competitor URLs to a pricing group first.</div> :
      <div className="card calendar competitor-table"><table><thead><tr><th>Group</th><th>Listing</th><th>Current minNights</th><th>Last success</th><th>Last error</th></tr></thead><tbody>
        {competitors.map(item => <tr key={item.id}><td>{item.pricing_group_name}</td><td><a className="table-link" href={item.canonical_url} target="_blank" rel="noreferrer">{item.external_listing_id}</a></td><td>{item.current_minimum_stay ?? "—"}</td><td>{item.last_scraped_at ? new Date(item.last_scraped_at).toLocaleString() : "Never"}</td><td className="error-cell">{item.last_error ?? "—"}</td></tr>)}
      </tbody></table></div>}
    <div className="card calendar competitor-runs"><b>Recent collection runs</b>{initialRuns.length ? <table><thead><tr><th>Started</th><th>Listing</th><th>Range</th><th>Skipped</th><th>Status</th><th>Result</th></tr></thead><tbody>
      {initialRuns.map(run => <tr key={run.id}><td>{new Date(run.started_at).toLocaleString()}</td><td>{String(run.summary.external_listing_id ?? "—")}</td><td>{String(run.summary.start_date ?? "—")} – {String(run.summary.end_date ?? "—")}</td><td>{Array.isArray(run.summary.skipped_dates) ? run.summary.skipped_dates.length : 0}</td><td><span className="pill">{run.status}</span></td><td>{run.error ?? String(run.summary.result_status ?? run.summary.reason ?? "—")}</td></tr>)}
    </tbody></table> : <div className="empty">No competitor collection runs yet.</div>}</div>
  </>;
}
