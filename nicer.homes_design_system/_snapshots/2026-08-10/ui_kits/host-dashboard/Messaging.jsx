const {Input,Button}=window.NicerHomesDesignSystem_ea7f10;
function Messaging(){
const threads=[{name:'Sarah T.',prop:'Villa Kayu',preview:'What time is check-in on the 14th?',active:true},{name:'Michael R.',prop:'Villa Alang',preview:'Thank you, see you soon!',active:false},{name:'Lena W.',prop:'Rumah Terang',preview:'Is early check-out possible?',active:false}];
return (
<div style={{display:'flex',flex:1,width:'100%',borderRadius:'var(--radius-lg)',overflow:'hidden',background:'var(--color-white)'}}>
<div style={{width:260,background:'var(--color-mist)',display:'flex',flexDirection:'column'}}>
{threads.map(t=>(
<div key={t.name} style={{padding:'14px 20px',background:t.active?'var(--color-white)':'transparent'}}>
<div style={{fontWeight:600,fontSize:14,color:'var(--text-primary)'}}>{t.name}</div>
<div style={{fontSize:12,color:'var(--text-secondary)'}}>{t.prop}</div>
<div style={{fontSize:12,color:'var(--text-muted)',marginTop:4,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{t.preview}</div>
</div>
))}
</div>
<div style={{flex:1,display:'flex',flexDirection:'column',minHeight:0}}>
<div style={{flex:1,padding:20,display:'flex',flexDirection:'column',gap:12,overflow:'auto'}}>
<div style={{alignSelf:'flex-start',background:'var(--color-mist)',borderRadius:'var(--radius-md)',padding:'10px 14px',fontSize:14,maxWidth:320}}>What time is check-in on the 14th?</div>
<div style={{alignSelf:'flex-end',background:'var(--color-ink-600)',color:'#fff',borderRadius:'var(--radius-md)',padding:'10px 14px',fontSize:14,maxWidth:320}}>Hi Sarah — check-in is 14:00, and our team will be at the villa to greet you.</div>
</div>
<div style={{display:'flex',gap:8,padding:'16px 20px',background:'var(--color-mist)'}}>
<div style={{flex:1}}><Input placeholder="Write a reply..." /></div>
<Button variant="primary">Send</Button>
</div>
</div>
</div>);
}
window.Messaging=Messaging;
