"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

/** Prototype host-dashboard shell; route links replace only prototype's in-memory navigation. */
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = React.useState(false);
  async function signOut() {
    const token = decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
    await fetch("/api/auth/logout", { method: "POST", headers: { "X-CSRF-Token": token } });
    router.push("/login");
  }
  const icon = (src: string) => <img src={src} style={{ width: 15, height: 15 }} alt="" />;
  const items = [{ label: "Calendar", href: "/" }, { label: "Activity", href: "/runs" }];
  const sidebar = <div style={{ width: 240, padding: "28px 0", display: "flex", flexDirection: "column", gap: 2, background: "var(--color-mist)", overflow: "hidden", flexShrink: 0, minHeight: "100vh", boxSizing: "border-box" }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, marginTop: -6, paddingLeft: 20, paddingRight: 16, minWidth: 220 }}>
      <span style={{ fontFamily: "var(--font-logo)", fontSize: 20, letterSpacing: "0.01em", color: "var(--color-logo-text)" }}>nicer</span>
      <button aria-label="Collapse sidebar" onClick={() => setCollapsed(true)} style={{ width: 28, height: 28, border: 0, borderRadius: "var(--radius-full)", background: "transparent", cursor: "pointer" }}>{icon("https://unpkg.com/lucide-static@latest/icons/chevrons-left.svg")}</button>
    </div>
    {items.map(item => <Link key={item.href} href={item.href} style={{ margin: "0 8px", padding: "10px 12px", borderRadius: "var(--radius-md)", fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", minWidth: 204, color: pathname === item.href ? "var(--text-primary)" : "var(--text-secondary)", background: pathname === item.href ? "rgba(11,12,14,0.06)" : "transparent" }}>{item.label}</Link>)}
    <div style={{ flex: 1 }} />
    <button type="button" onClick={() => void signOut()} style={{ margin: "0 8px", padding: "10px 12px", border: 0, background: "transparent", textAlign: "left", color: "var(--text-secondary)", fontWeight: 600, cursor: "pointer" }}>Sign out</button>
  </div>;
  if (collapsed) return <div style={{ display: "flex", minHeight: "100vh", fontFamily: "var(--font-sans)", background: "var(--surface-page)", position: "relative", overflow: "hidden" }}><button aria-label="Open sidebar" onClick={() => setCollapsed(false)} style={{ position: "fixed", left: 24, top: 20, zIndex: 41, width: 32, height: 32, border: 0, borderRadius: "var(--radius-full)", background: "transparent" }}>{icon("https://unpkg.com/lucide-static@latest/icons/chevrons-right.svg")}</button><main style={{ flex: 1, minWidth: 0 }}>{children}</main></div>;
  return <div style={{ display: "flex", minHeight: "100vh", fontFamily: "var(--font-sans)", background: "var(--surface-page)", position: "relative", overflow: "hidden" }}>{sidebar}<div style={{ flex: 1, position: "relative", zIndex: 1, display: "flex", flexDirection: "column", minHeight: "100vh", minWidth: 0, paddingTop: 40, boxSizing: "border-box" }}><div style={{ padding: "24px 0 0", flex: 1, display: "flex", minHeight: 0, minWidth: 0 }}>{children}</div></div></div>;
}
