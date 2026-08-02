import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";

export const dynamic = "force-dynamic";

type Run = {
  id: number;
  kind: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  summary: Record<string, unknown> | null;
  error: string | null;
};

async function loadRuns(): Promise<Run[]> {
  const cookie = await cookies();
  const response = await fetch(
    `${process.env.API_URL ?? "http://api:8000"}/api/runs?limit=100`,
    { headers: { cookie: cookie.toString() }, cache: "no-store" },
  );
  if (response.status === 401) redirect("/login");
  if (!response.ok) return [];
  return response.json();
}

function timestamp(value: string | null) {
  return value ? new Date(value).toLocaleString() : "—";
}

export default async function Runs() {
  const runs = await loadRuns();
  return <Shell>
    <h1>Run history</h1>
    <p className="muted">Imports, competitor collection, optimization, publishing, and reconciliation. Reload this page to refresh running jobs.</p>
    {runs.length ? <div className="card calendar"><table>
      <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Started</th><th>Finished</th><th>Result</th></tr></thead>
      <tbody>{runs.map(run => <tr key={run.id}>
        <td>{run.id}</td>
        <td>{run.kind}</td>
        <td><span className={`pill ${run.status === "failed" ? "error" : ""}`}>{run.status}</span></td>
        <td>{timestamp(run.started_at)}</td>
        <td>{timestamp(run.finished_at)}</td>
        <td>{run.error
          ? <span className="error-cell">{run.error}</span>
          : run.summary
            ? <details><summary>Details</summary><pre>{JSON.stringify(run.summary, null, 2)}</pre></details>
            : "—"}</td>
      </tr>)}</tbody>
    </table></div> : <div className="card empty">No runs recorded yet.</div>}
  </Shell>;
}
