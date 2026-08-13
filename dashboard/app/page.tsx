"use client";
import dynamic from "next/dynamic";
import { Shell } from "./components/Shell";
import { CalendarLoadingSkeleton } from "./components/CalendarLoadingSkeleton";

const PrototypePricing = dynamic(() => import("./components/PrototypePricing"), { ssr:false, loading:() => <CalendarLoadingSkeleton /> });

export default function CalendarPage() {
  return <Shell><PrototypePricing /></Shell>;
}
