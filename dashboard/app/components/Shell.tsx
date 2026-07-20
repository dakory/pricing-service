import Link from "next/link";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      <aside>
        <div className="brand">Nicer Homes<br />Pricing</div>
        <nav>
          <Link href="/">Portfolio calendar</Link>
          <Link href="/properties">Properties</Link>
          <Link href="/competitors">Competitor freshness</Link>
          <Link href="/runs">Run history</Link>
          <Link href="/status">System status</Link>
        </nav>
      </aside>
      <main>{children}</main>
    </div>
  );
}

