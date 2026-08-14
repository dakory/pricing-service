import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    service: "pricing-dashboard",
    commit: process.env.BUILD_SHA ?? process.env.NEXT_PUBLIC_BUILD_SHA ?? "dev",
  });
}
