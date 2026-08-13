const {Tabs,IconButton}=window.NicerHomesDesignSystem_ea7f10;
function Sidebar({section,onSection,pinned,onTogglePin}){
const items=[{label:'Portfolio',value:'portfolio'},{label:'Pricing & calendar',value:'pricing'},{label:'Messages',value:'messaging'}];
const [hovering,setHovering]=React.useState(false);
const open=pinned||hovering;
return (
<div onMouseEnter={()=>setHovering(true)} onMouseLeave={()=>setHovering(false)} style={{width:open?240:16,transition:'width var(--duration-standard) var(--ease-standard)',padding:'28px 0',display:'flex',flexDirection:'column',gap:2,background:'var(--color-mist)',position:'relative',zIndex:2,overflow:'hidden',flexShrink:0,minHeight:'100vh'}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:28,paddingLeft:20,paddingRight:16,minWidth:220}}>
<img src="../../assets/logo/nicer-wordmark.png" style={{height:26,width:'auto'}} />
<IconButton label={pinned?'Unpin sidebar':'Pin sidebar'} active={pinned} onClick={onTogglePin} icon={<img src={pinned?'https://unpkg.com/lucide-static@latest/icons/pin-off.svg':'https://unpkg.com/lucide-static@latest/icons/pin.svg'} style={{width:15,height:15}} />} size={28} />
</div>
{items.map(it=>{
const [hover,setHover]=React.useState(false);
const active=section===it.value;
return <div key={it.value} onClick={()=>onSection(it.value)} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)} style={{margin:'0 8px',padding:'10px 12px',borderRadius:'var(--radius-md)',fontFamily:'var(--font-sans)',fontSize:14,fontWeight:600,cursor:'pointer',whiteSpace:'nowrap',minWidth:204,color:active?'var(--text-primary)':'var(--text-secondary)',background:active?'rgba(11,12,14,0.06)':hover?'rgba(11,12,14,0.04)':'transparent'}}>{it.label}</div>;
})}
<div style={{flex:1}} />
<div style={{display:'flex',alignItems:'center',gap:10,padding:'0 20px',minWidth:220}}>
<IconButton label="Notifications" icon={<img src="https://unpkg.com/lucide-static@latest/icons/bell.svg" style={{width:18,height:18}} />} />
<div style={{width:34,height:34,borderRadius:'var(--radius-full)',background:'var(--action-accent-soft)'}} />
</div>
</div>);
}
function TopBar({title}){
return (
<div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'28px 40px 0',position:'relative',zIndex:1,background:'var(--color-white)'}}>
<h2 style={{fontFamily:'var(--font-display)',fontWeight:500,fontSize:'var(--text-xl)',margin:0,color:'var(--text-primary)'}}>{title}</h2>
</div>);
}
function HostDashboardApp(){
const [section,setSection]=React.useState('portfolio');
const [pinned,setPinned]=React.useState(true);
const screens={portfolio:window.Portfolio,pricing:window.Pricing,messaging:window.Messaging};
const titles={portfolio:'Your properties',pricing:'Pricing & calendar',messaging:'Guest messages'};
const Screen=screens[section];
return (
<div style={{display:'flex',minHeight:'100vh',fontFamily:'var(--font-sans)',background:'var(--surface-page)',position:'relative',overflow:'hidden'}}>
<div className="glow-blob" style={{width:420,height:420,background:'var(--color-accent-300)',top:-140,right:-100,opacity:0.35}} />
<Sidebar section={section} onSection={setSection} pinned={pinned} onTogglePin={()=>setPinned(p=>!p)} />
<div style={{flex:1,position:'relative',zIndex:1,display:'flex',flexDirection:'column',minHeight:'100vh',minWidth:0}}>
{section!=='messaging'&&<TopBar title={titles[section]} />}
<div style={{padding:'24px 0 0 0',flex:1,display:'flex',minHeight:0,minWidth:0}}><Screen/></div>
</div>
</div>);
}
window.HostDashboardApp=HostDashboardApp;
