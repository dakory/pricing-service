"use client";
import dynamic from "next/dynamic";
import { Shell } from "./components/Shell";

const PrototypePricing = dynamic(() => import("./components/PrototypePricing"), { ssr:false, loading:() => <div className="prototype-loading">Loading calendar…</div> });

export default function CalendarPage() {
  return <Shell><PrototypePricing /></Shell>;
}
