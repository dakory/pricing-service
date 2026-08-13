"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type Override = { id: number; property_id: number; start_date: string; end_date: string; price: number; reason: string };
type Property = { id: number; name: string };
const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
const idr = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
export function OverrideList({ overrides, properties }: { overrides: Override[]; properties: Property[] }) {
  const router = useRouter(); const [message, setMessage] = useState(""); const names = Object.fromEntries(properties.map(p => [p.id, p.name]));
  async function remove(id: number) { const response = await fetch(`/api/overrides/${id}`, { method: "DELETE", headers: { "X-CSRF-Token": csrf() } }); setMessage(response.ok ? "Override removed. Generate recommendations to recalculate." : "Could not remove override."); router.refresh(); }
  if (!overrides.length) return null;
  return <div className="card override-list"><b>Active hard overrides</b>{overrides.map(item => <div className="override-row" key={item.id}><div><strong>{names[item.property_id]}</strong><span>{item.start_date} → {item.end_date}</span><small>{idr.format(item.price)} · {item.reason}</small></div><button className="button danger" onClick={() => remove(item.id)}>Remove</button></div>)}{message && <p className="muted">{message}</p>}</div>;
}
