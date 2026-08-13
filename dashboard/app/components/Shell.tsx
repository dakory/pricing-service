import Link from "next/link";

function NavGlyph({ children }: { children: React.ReactNode }) {
  return <span className="nav-glyph" aria-hidden="true">{children}</span>;
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      <aside>
        <div className="brand">nicer<span>.homes</span><small>pricing operations</small></div>
        <nav>
          <Link href="/"><NavGlyph>▦</NavGlyph>Calendar</Link>
          <Link href="/competitors"><NavGlyph>⌁</NavGlyph>Competitor freshness</Link>
          <Link href="/runs"><NavGlyph>◌</NavGlyph>Activity</Link>
        </nav>
        <form className="logout" action="/api/auth/logout" method="post"><button type="submit"><NavGlyph>↪</NavGlyph>Sign out</button></form>
      </aside>
      <main>{children}</main>
    </div>
  );
}
