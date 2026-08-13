const {Badge,Card}=window.NicerHomesDesignSystem_ea7f10;
function relTime(mins){if(mins<60)return mins+'m ago';const h=Math.floor(mins/60);if(h<24)return h+'h ago';return Math.floor(h/24)+'d ago';}
function Activity(){
const events=[
{type:'Price update',scope:'Villa Kayu \u00b7 Beachfront Collection',detail:'Applied 6 recommended price changes for August\u2013September.',status:'success',mins:4},
{type:'Competitor sync',scope:'Uluwatu market',detail:'Refreshed rates from 14 comparable listings.',status:'success',mins:22},
{type:'Price fetch',scope:'All properties',detail:'Pulled current live rates from connected channels.',status:'success',mins:41},
{type:'Market data collection',scope:'Canggu market',detail:'Collecting demand signals for the next 90 days.',status:'running',mins:2},
{type:'Price update',scope:'Rumah Terang \u00b7 Ubud Retreats',detail:'2 of 5 recommended changes applied \u2014 3 skipped (below minimum rate).',status:'warning',mins:96},
{type:'Competitor sync',scope:'Ubud market',detail:'Could not reach one data source; retried automatically.',status:'error',mins:130},
{type:'Price fetch',scope:'Villa Alang',detail:'Pulled current live rates from connected channels.',status:'success',mins:260},
{type:'Market data collection',scope:'All markets',detail:'Weekly demand and event scan completed.',status:'success',mins:1400},
];
const tones={success:'success',warning:'accent',error:'danger',running:'neutral'};
const labels={success:'Completed',warning:'Needs review',error:'Failed',running:'Running'};
return (
<div style={{flex:1,minWidth:0,padding:'0 40px 40px',overflow:'auto'}}>
<div style={{display:'flex',flexDirection:'column',gap:12,maxWidth:760}}>
{events.map((e,i)=>(
<Card key={i} padding="16px 20px" style={{display:'flex',alignItems:'center',gap:16}}>
<div style={{width:8,height:8,borderRadius:'var(--radius-full)',flexShrink:0,background:e.status==='running'?'var(--color-accent-500)':e.status==='error'?'var(--status-danger)':e.status==='warning'?'var(--color-accent-700)':'var(--status-success)'}} />
<div style={{flex:1,minWidth:0}}>
<div style={{display:'flex',alignItems:'center',gap:8,marginBottom:2}}>
<span style={{fontWeight:600,fontSize:14,color:'var(--text-primary)'}}>{e.type}</span>
<span style={{fontSize:12,color:'var(--text-secondary)'}}>{e.scope}</span>
</div>
<div style={{fontSize:13,color:'var(--text-secondary)'}}>{e.detail}</div>
</div>
<Badge tone={tones[e.status]}>{labels[e.status]}</Badge>
<div style={{fontSize:12,color:'var(--text-muted)',width:70,textAlign:'right',flexShrink:0}}>{relTime(e.mins)}</div>
</Card>
))}
</div>
</div>);
}
window.Activity=Activity;
