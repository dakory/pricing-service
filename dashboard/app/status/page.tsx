import { Shell } from "../components/Shell";
export default function Status() { return <Shell><h1>System status</h1><div className="stats"><div className="card stat"><span className="muted">Publishing</span><b><span className="pill">Shadow</span></b></div><div className="card stat"><span className="muted">API</span><b>Online</b></div></div><div className="card"><b>Activation safeguards</b><p className="muted">Production requires an explicit activation date. Complete seven shadow runs, a full competitor refresh, and a supervised canary before enabling it.</p></div></Shell>; }

