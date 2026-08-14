import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/dashboard-version"];

/** Protect dashboard pages by validating the same database-backed API session. */
export async function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (PUBLIC_PATHS.includes(pathname)) return NextResponse.next();

  const sessionEndpoint = `${process.env.API_URL ?? "http://api:8000"}/api/auth/session`;
  try {
    const response = await fetch(sessionEndpoint, {
      headers: { cookie: request.headers.get("cookie") ?? "" },
      cache: "no-store",
    });
    if (response.ok) return NextResponse.next();
  } catch {
    // Treat an unavailable auth service as unauthenticated rather than serving
    // a page whose protected data cannot load.
  }

  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
