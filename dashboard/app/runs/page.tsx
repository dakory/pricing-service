import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "../components/Shell";

export const dynamic = "force-dynamic";

type Run = { id:number; kind:string; status:string; started_at:string; finished_at:string|null; summary:Record<string,unknown>|null; error:string|null };

async function loadRuns(): Promise<Run[]> {
  const cookie=await cookies();
  const response=await fetch(`${process.env.API_URL??"http://api:8000"}/api/runs?limit=100`,{headers:{cookie:cookie.toString()},cache:"no-store"});
  if(response.status===401) redirect("/login");
  return response.ok?response.json():[];
}

function relativeTime(value:string) {
  const minutes=Math.max(0,Math.round((Date.now()-new Date(value).getTime())/60000));
  if(minutes<60) return `${minutes}m ago`;
  const hours=Math.floor(minutes/60); if(hours<24) return `${hours}h ago`;
  return `${Math.floor(hours/24)}d ago`;
}

function label(kind:string) { return kind.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase()); }

export default async function Runs() {
  const runs=await loadRuns();
  return <Shell><div style={{flex:1,minWidth:0,padding:"0 40px 40px",overflow:"auto"}}>
    <div style={{display:"flex",flexDirection:"column",gap:12,maxWidth:760}}>
      {runs.map(run=>{
        const status=run.status==="failed"?"error":run.status==="running"?"running":run.status==="warning"?"warning":"success";
        const tone=status==="error"?"var(--status-danger)":status==="warning"?"var(--color-accent-700)":status==="running"?"var(--color-accent-500)":"var(--status-success)";
        const statusLabel=status==="error"?"Failed":status==="warning"?"Needs review":status==="running"?"Running":"Completed";
        return <div key={run.id} style={{display:"flex",alignItems:"center",gap:16,padding:"16px 20px",border:"1px solid var(--border-default)",borderRadius:"var(--radius-lg)",background:"var(--surface-card-solid)",boxShadow:"var(--shadow-sm)"}}>
          <div style={{width:8,height:8,borderRadius:"var(--radius-full)",flexShrink:0,background:tone}} />
          <div style={{flex:1,minWidth:0}}>
            <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:2}}><span style={{fontWeight:600,fontSize:14,color:"var(--text-primary)"}}>{label(run.kind)}</span><span style={{fontSize:12,color:"var(--text-secondary)"}}>Run #{run.id}</span></div>
            <div style={{fontSize:13,color:run.error?"var(--status-danger)":"var(--text-secondary)",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{run.error??(run.summary?JSON.stringify(run.summary):"No additional details")}</div>
          </div>
          <span style={{fontSize:12,fontWeight:600,color:tone,whiteSpace:"nowrap"}}>{statusLabel}</span>
          <span style={{fontSize:12,color:"var(--text-muted)",width:70,textAlign:"right",flexShrink:0}}>{relativeTime(run.started_at)}</span>
        </div>;
      })}
      {!runs.length&&<div style={{padding:60, textAlign:"center", color:"var(--text-muted)",border:"1px solid var(--border-default)",borderRadius:"var(--radius-lg)"}}>No activity recorded yet.</div>}
    </div>
  </div></Shell>;
}
