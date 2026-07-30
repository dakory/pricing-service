import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";
import { PricingActions, PricingConfigurationEditor, PropertyEditor } from "../components/PropertyEditor";

async function api(path: string) {
  const cookie = await cookies(); const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}${path}`, { headers: { cookie: cookie.toString() }, cache: "no-store" });
  if (response.status === 401) redirect("/login"); return response.json();
}
export default async function Properties() {
  const [items, configuration] = await Promise.all([api("/api/properties"), api("/api/settings/pricing")]);
  return <Shell><h1>Pricing policies</h1><p className="muted">Market-based Pricing Engine v2 settings. Changes remain in shadow mode.</p><PricingActions/><PricingConfigurationEditor configuration={configuration}/><div className="policy-list">{items.map((item: Parameters<typeof PropertyEditor>[0]["property"]) => <PropertyEditor property={item} key={item.id}/>)}</div></Shell>;
}
