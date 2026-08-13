"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";

function NavGlyph({ children }: { children: React.ReactNode }) {
  return <span className="nav-glyph" aria-hidden="true">{children}</span>;
}

export function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  async function signOut() {
    const token = decodeURIComponent(document.cookie.split("; ").find(row => row.startsWith("pricing_csrf="))?.split("=")[1] ?? "");
    await fetch("/api/auth/logout", { method:"POST", headers:{"X-CSRF-Token":token} });
    router.push("/login");
  }
  return (
    <div className="shell">
      <aside>
        <div className="brand">nicer<span>.homes</span><small>pricing operations</small></div>
        <nav>
          <Link href="/"><NavGlyph>▦</NavGlyph>Calendar</Link>
          <Link href="/competitors"><NavGlyph>⌁</NavGlyph>Competitor freshness</Link>
          <Link href="/runs"><NavGlyph>◌</NavGlyph>Activity</Link>
        </nav>
        <button className="logout" type="button" onClick={() => void signOut()}><NavGlyph>↪</NavGlyph>Sign out</button>
      </aside>
      <main>{children}</main>
    </div>
  );
}
