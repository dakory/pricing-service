const {IconButton}=window.NicerHomesDesignSystem_ea7f10;
function Sidebar({section,onSection,collapsed,onToggleCollapsed}){
const [peek,setPeek]=React.useState(false);
const items=[{label:'Calendar',value:'pricing'},{label:'Activity',value:'activity'}];
const content=(
<div onMouseLeave={()=>setPeek(false)} style={{width:240,padding:'28px 0',display:'flex',flexDirection:'column',gap:2,background:'var(--color-mist)',overflow:'hidden',flexShrink:0,minHeight:'100vh',boxSizing:'border-box'}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:28,marginTop:-6,paddingLeft:20,paddingRight:16,minWidth:220}}>
<span style={{fontFamily:'var(--font-logo)',fontSize:20,letterSpacing:'0.01em',color:'var(--color-logo-text)'}}>nicer</span>
<IconButton label="Collapse sidebar" onClick={onToggleCollapsed} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevrons-left.svg" style={{width:15,height:15}} />} size={28} />
</div>
{items.map(it=>{
const [hover,setHover]=React.useState(false);
const active=section===it.value;
return <div key={it.value} onClick={()=>onSection(it.value)} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)} style={{margin:'0 8px',padding:'10px 12px',borderRadius:'var(--radius-md)',fontFamily:'var(--font-sans)',fontSize:14,fontWeight:600,cursor:'pointer',whiteSpace:'nowrap',minWidth:204,color:active?'var(--text-primary)':'var(--text-secondary)',background:active?'rgba(11,12,14,0.06)':hover?'rgba(11,12,14,0.04)':'transparent'}}>{it.label}</div>;
})}
<div style={{flex:1}} />
</div>);
if(collapsed){
return (<React.Fragment>
<div onMouseEnter={()=>setPeek(true)} style={{position:'fixed',left:0,top:0,bottom:0,width:14,zIndex:39}} />
{!peek&&<div style={{position:'fixed',left:24,top:20,zIndex:41}}><IconButton label="Open sidebar" onClick={onToggleCollapsed} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevrons-right.svg" style={{width:15,height:15}} />} size={32} /></div>}
<div style={{position:'fixed',left:0,top:0,height:'100vh',zIndex:40,transform:`translateX(${peek?'0':'-100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',boxShadow:peek?'var(--shadow-lg)':'none'}}>{content}</div>
</React.Fragment>);
}
return content;
}
function TopBar({title}){
return (
<div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'28px 40px 0',position:'relative',zIndex:1,background:'var(--color-white)'}}>
<h2 style={{fontFamily:'var(--font-display)',fontWeight:500,fontSize:'var(--text-xl)',margin:0,color:'var(--text-primary)'}}>{title}</h2>
</div>);
}
function HostDashboardApp(){
const [section,setSection]=React.useState('pricing');
const [collapsed,setCollapsed]=React.useState(false);
const screens={pricing:window.Pricing,activity:window.Activity};
const titles={pricing:'Pricing & calendar',activity:'Activity'};
const Screen=screens[section];
return (
<div style={{display:'flex',minHeight:'100vh',fontFamily:'var(--font-sans)',background:'var(--surface-page)',position:'relative',overflow:'hidden'}}>
<Sidebar section={section} onSection={setSection} collapsed={collapsed} onToggleCollapsed={()=>setCollapsed(c=>!c)} />
<div style={{flex:1,position:'relative',zIndex:1,display:'flex',flexDirection:'column',minHeight:'100vh',minWidth:0,paddingTop:40,boxSizing:'border-box'}}>
{section==='activity'&&<TopBar title={titles[section]} />}
<div style={{padding:'24px 0 0 0',flex:1,display:'flex',minHeight:0,minWidth:0}}><Screen/></div>
</div>
</div>);
}
window.HostDashboardApp=HostDashboardApp;
