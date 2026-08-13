const {Badge,Card}=window.NicerHomesDesignSystem_ea7f10;
function Portfolio(){
const props=[
{name:'Villa Kayu',loc:'Uluwatu · 4 bed',status:'Active',occ:'82%',rate:'Rp 4,850,000',c:'var(--action-accent-soft)'},
{name:'Villa Alang',loc:'Canggu · 3 bed',status:'Active',occ:'71%',rate:'Rp 3,200,000',c:'var(--color-white)'},
{name:'Rumah Terang',loc:'Ubud · 5 bed',status:'Maintenance',occ:'—',rate:'Rp 5,400,000',c:'var(--color-white)'},
];
return (
<div style={{display:'flex',flexDirection:'column',gap:16}}>
{props.map(p=>(
<Card key={p.name} style={{display:'flex',alignItems:'center',gap:20,padding:'18px 22px'}}>
<div style={{width:56,height:56,borderRadius:'var(--radius-md)',background:p.c,border:'1px solid var(--border-default)',flexShrink:0}} />
<div style={{flex:1}}>
<div style={{fontWeight:600,fontSize:15,color:'var(--text-primary)'}}>{p.name}</div>
<div style={{fontSize:13,color:'var(--text-secondary)'}}>{p.loc}</div>
</div>
<div style={{width:90,fontFamily:'var(--font-mono)',fontSize:14,color:'var(--text-primary)'}}>{p.occ}</div>
<div style={{width:130,fontFamily:'var(--font-mono)',fontSize:14,color:'var(--text-primary)'}}>{p.rate}</div>
<Badge tone={p.status==='Active'?'success':'neutral'}>{p.status}</Badge>
</Card>
))}
</div>);
}
window.Portfolio=Portfolio;
