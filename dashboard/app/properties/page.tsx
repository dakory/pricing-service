import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";
import { PricingActions, PropertyEditor } from "../components/PropertyEditor";

async function properties() {
  const cookie = await cookies(); const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}/api/properties`, { headers: { cookie: cookie.toString() }, cache: "no-store" });
  if (response.status === 401) redirect("/login"); return response.json();
}
export default async function Properties() { const items = await properties(); return <Shell><h1>Pricing policies</h1><p className="muted">Canonical BookingSite bounds and explainable baseline factors. Changes remain in shadow mode.</p><PricingActions/><div className="policy-list">{items.map((item: Parameters<typeof PropertyEditor>[0]["property"]) => <PropertyEditor property={item} key={item.id}/>)}</div></Shell>; }
