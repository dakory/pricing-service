"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { IconButton } from "./design-system";

/** Prototype host-dashboard shell; route links replace only prototype's in-memory navigation. */
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);
  const [peek, setPeek] = React.useState(false);
  const items = [{ label: "Calendar", href: "/" }, { label: "Activity", href: "/runs" }];
  const sidebarContent = <div onMouseLeave={() => setPeek(false)} style={{ width: 240, padding: "28px 0", display: "flex", flexDirection: "column", gap: 2, background: "var(--color-mist)", overflow: "hidden", flexShrink: 0, minHeight: "100vh", boxSizing: "border-box" }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, marginTop: -6, paddingLeft: 20, paddingRight: 16, minWidth: 220 }}>
      <span style={{ fontFamily: "var(--font-logo)", fontSize: 20, letterSpacing: "0.01em", color: "var(--color-logo-text)" }}>nicer</span>
      <IconButton label="Collapse sidebar" onClick={() => setCollapsed(true)} size={28} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevrons-left.svg" style={{ width: 15, height: 15 }} alt="" />} />
    </div>
    {items.map(item => <Link key={item.href} href={item.href} style={{ margin: "0 8px", padding: "10px 12px", borderRadius: "var(--radius-md)", fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap", minWidth: 204, color: pathname === item.href ? "var(--text-primary)" : "var(--text-secondary)", background: pathname === item.href ? "rgba(11,12,14,0.06)" : "transparent" }}>{item.label}</Link>)}
    <div style={{ flex: 1 }} />
  </div>;
  if (collapsed) return <div style={{ display: "flex", minHeight: "100vh", fontFamily: "var(--font-sans)", background: "var(--surface-page)", position: "relative", overflow: "hidden" }}><div onMouseEnter={() => setPeek(true)} style={{ position: "fixed", left: 0, top: 0, bottom: 0, width: 14, zIndex: 39 }} />{!peek && <div style={{ position: "fixed", left: 24, top: 20, zIndex: 41 }}><IconButton label="Open sidebar" onClick={() => setCollapsed(false)} size={32} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevrons-right.svg" style={{ width: 15, height: 15 }} alt="" />} /></div>}<div style={{ position: "fixed", left: 0, top: 0, height: "100vh", zIndex: 40, transform: `translateX(${peek ? "0" : "-100%"})`, transition: "transform var(--duration-standard) var(--ease-standard)", boxShadow: peek ? "var(--shadow-lg)" : "none" }}>{sidebarContent}</div><main style={{ flex: 1, minWidth: 0 }}>{children}</main></div>;
  return <div style={{ display: "flex", minHeight: "100vh", fontFamily: "var(--font-sans)", background: "var(--surface-page)", position: "relative", overflow: "hidden" }}>{sidebarContent}<div style={{ flex: 1, position: "relative", zIndex: 1, display: "flex", flexDirection: "column", minHeight: "100vh", minWidth: 0, paddingTop: 40, boxSizing: "border-box" }}><div style={{ padding: "24px 0 0", flex: 1, display: "flex", minHeight: 0, minWidth: 0 }}>{children}</div></div></div>;
}
