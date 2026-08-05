import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";
import { FormulaCard, NewPricingGroupForm, PricingActions, PricingConfigurationEditor, PricingGroupEditor, PropertyEditor } from "../components/PropertyEditor";

async function api(path: string) {
  const cookie = await cookies(); const response = await fetch(`${process.env.API_URL ?? "http://api:8000"}${path}`, { headers: { cookie: cookie.toString() }, cache: "no-store" });
  if (response.status === 401) redirect("/login"); return response.json();
}
export default async function Properties() {
  const [items, groups, configuration] = await Promise.all([api("/api/properties"), api("/api/pricing-groups"), api("/api/settings/pricing")]);
  return <Shell><h1>Pricing policies</h1><p className="muted">System defaults, pricing groups, and independent property-level overrides. Changes remain in shadow mode.</p><PricingActions/><FormulaCard/><PricingConfigurationEditor configuration={configuration}/><h2>Pricing groups</h2><p className="muted">Comparable properties in a group share competitor listings and minimum-count settings.</p><NewPricingGroupForm/><div className="policy-list">{groups.map((group: Parameters<typeof PricingGroupEditor>[0]["group"]) => <PricingGroupEditor group={group} key={group.id}/>)}</div><h2>Properties</h2><div className="policy-list">{items.map((item: Parameters<typeof PropertyEditor>[0]["property"]) => <PropertyEditor property={item} globalConfiguration={configuration} pricingGroups={groups} key={item.id}/>)}</div></Shell>;
}
