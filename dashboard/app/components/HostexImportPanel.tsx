"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type HostexStatus = {
  configured: boolean;
  last_successful_import_at: string | null;
  schedule: {
    enabled: boolean;
    description: string;
    timezone: string;
    next_import_at: string | null;
  };
  last_import: {
    id: number;
    status: string;
    started_at: string;
    finished_at: string | null;
    error: string | null;
  } | null;
};

const csrf = () => decodeURIComponent(
  document.cookie
    .split("; ")
    .find(row => row.startsWith("pricing_csrf="))
    ?.split("=")[1] ?? "",
);

function timestamp(value: string | null) {
  if (!value) return "—";
  return `${new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Makassar",
  }).format(new Date(value))} WITA`;
}

export function HostexImportPanel({ status }: { status: HostexStatus }) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function importNow() {
    setRunning(true);
    setMessage("Importing properties, reservations, and 365-day calendars…");
    try {
      const response = await fetch("/api/imports/hostex", {
        method: "POST",
        headers: { "X-CSRF-Token": csrf() },
      });
      const body = await response.json();
      setMessage(
        response.ok
          ? `Import ${body.run_id} completed successfully`
          : body.detail ?? "Hostex import failed",
      );
      if (response.ok) router.refresh();
    } catch {
      setMessage("Could not reach the import endpoint");
    } finally {
      setRunning(false);
    }
  }

  return <div className="card policy">
    <div className="policy-title"><div>
      <h2>Hostex import status</h2>
      <p className="muted">Dashboard prices and availability come from the latest successful import.</p>
    </div></div>
    <div className="stats">
      <div className="stat"><span className="muted">Last successful import</span><b>{timestamp(status.last_successful_import_at)}</b></div>
      <div className="stat"><span className="muted">Next scheduled import</span><b>{status.schedule.enabled ? timestamp(status.schedule.next_import_at) : "Not scheduled"}</b><small className="muted">{status.schedule.description}</small></div>
      <div className="stat"><span className="muted">Last attempt</span><b>{status.last_import ? status.last_import.status : "—"}</b><small className="muted">{status.last_import ? timestamp(status.last_import.started_at) : "No attempts"}</small></div>
    </div>
    {status.last_import?.error && <p className="error-cell">{status.last_import.error}</p>}
    <div className="action-row">
      <button className="button" type="button" disabled={running || !status.configured} onClick={importNow}>
        {running ? "Importing…" : "Import from Hostex now"}
      </button>
      <span className="muted">{message || (!status.configured ? "Hostex token is not configured" : "")}</span>
    </div>
  </div>;
}
