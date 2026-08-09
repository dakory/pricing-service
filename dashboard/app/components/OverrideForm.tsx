"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Property = { id: number; name: string };
const csrf = () => decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");

export function OverrideForm({ properties, selectedId, start, end }: { properties: Property[]; selectedId?: number; start: string; end: string }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    const payload = { property_id: Number(data.get("property_id")), start_date: data.get("start_date"), end_date: data.get("end_date"), price: Number(data.get("price")), reason: data.get("reason") };
    const response = await fetch("/api/overrides", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    const body = response.status === 204 ? {} : await response.json(); setMessage(response.ok ? "Override saved. Run shadow pricing to apply it." : body.detail); router.refresh();
  }
  return <form className="card override-form" onSubmit={submit}><b>Add hard override</b><div className="form-grid">
    <label>Property<select name="property_id" defaultValue={selectedId}>{properties.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label>
    <label>Start<input name="start_date" type="date" defaultValue={start} required/></label><label>End<input name="end_date" type="date" defaultValue={end} required/></label>
    <label>Price<input name="price" type="number" min="1" required/></label>
    <label className="wide">Reason<input name="reason" required placeholder="Owner lock, event, maintenance…"/></label></div><div className="form-actions"><button className="button">Save override</button><span className="muted">{message}</span></div></form>;
}

export function ManualBaseForm({ properties, selectedId, start, end }: { properties: Property[]; selectedId?: number; start: string; end: string }) {
  const router = useRouter(); const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    const payload = { property_id: Number(data.get("property_id")), start_date: data.get("start_date"), end_date: data.get("end_date"), price: Number(data.get("price")), reason: data.get("reason") };
    const response = await fetch("/api/price-anchors", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf() }, body: JSON.stringify(payload) });
    const body = await response.json(); setMessage(response.ok ? `${body.count} manual base anchor(s) saved. Run shadow pricing.` : body.detail); router.refresh();
  }
  return <form className="card override-form" onSubmit={submit}><b>Add manual base price</b><div className="form-grid"><label>Property<select name="property_id" defaultValue={selectedId}>{properties.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label><label>Start<input name="start_date" type="date" defaultValue={start} required/></label><label>End<input name="end_date" type="date" defaultValue={end} required/></label><label>Base price<input name="price" type="number" min="1" required/></label><label className="wide">Reason<input name="reason" required placeholder="Special event, owner pricing…"/></label></div><div className="form-actions"><button className="button">Save manual base</button><span className="muted">{message}</span></div></form>;
}
