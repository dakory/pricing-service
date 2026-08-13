const {Input,IconButton,Select}=window.NicerHomesDesignSystem_ea7f10;
function genDays(n){
const start=new Date(2026,7,28);
return Array.from({length:n},(_,i)=>{const d=new Date(start);d.setDate(start.getDate()+i);return d;});
}
function monthLabel(d){return d.toLocaleDateString('en-US',{month:'long',year:'numeric'});}
function Pricing(){
const days=genDays(28);
const listings=[
{name:'Villa Kayu',loc:'Uluwatu',c:'var(--color-accent-300)',base:4850000},
{name:'Villa Alang',loc:'Canggu',c:'var(--color-mist)',base:3200000},
{name:'Rumah Terang',loc:'Ubud',c:'var(--color-ink-200)',base:5400000},
];
const [selected,setSelected]=React.useState(null);
const scrollRef=React.useRef(null);
const [canLeft,setCanLeft]=React.useState(false);
const [canRight,setCanRight]=React.useState(true);
const [currentMonth,setCurrentMonth]=React.useState(0);
const colWidth=96;
const labelColWidth=280;
const months=[];
days.forEach((d,i)=>{if(i===0||d.getDate()===1)months.push({label:monthLabel(d),start:i});});
const updateScrollState=()=>{
const el=scrollRef.current;if(!el)return;
setCanLeft(el.scrollLeft>4);
setCanRight(el.scrollLeft<el.scrollWidth-el.clientWidth-4);
const visibleCol=Math.round((el.scrollLeft)/colWidth);
let mi=0;
months.forEach((m,idx)=>{if(visibleCol>=m.start)mi=idx;});
setCurrentMonth(mi);
};
React.useEffect(()=>{updateScrollState();},[]);
const scrollBy=(dir)=>{const el=scrollRef.current;if(!el)return;el.scrollBy({left:dir*colWidth*4,behavior:'smooth'});setTimeout(updateScrollState,300)};
const scrollToCol=(colIdx)=>{const el=scrollRef.current;if(!el)return;el.scrollTo({left:colIdx*colWidth,behavior:'smooth'});setTimeout(updateScrollState,350)};
const scrollToToday=()=>scrollToCol(0);
const price=(base,i)=>Math.round((base+(Math.sin(i*1.7)*base*0.06)+(i%5===0?base*0.18:0))/1000)*1000;
const cols=`${labelColWidth}px repeat(${days.length},${colWidth}px)`;
return (
<div style={{flex:1,display:'flex',flexDirection:'column',minWidth:0,background:'var(--color-white)',position:'relative',zIndex:1}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'20px 24px',borderBottom:'1px solid var(--border-default)'}}>
<div style={{display:'flex',alignItems:'center',gap:12}}>
<Select value={String(currentMonth)} pill onChange={e=>scrollToCol(months[Number(e.target.value)].start)} options={months.map((m,idx)=>({label:m.label,value:String(idx)}))} />
<div onClick={scrollToToday} style={{padding:'0 16px',height:38,boxSizing:'border-box',display:'flex',alignItems:'center',borderRadius:'var(--radius-full)',border:'1px solid var(--border-default)',fontSize:13,fontWeight:600,cursor:'pointer'}}>Today</div>
</div>
</div>
<div style={{flex:1,position:'relative',minHeight:0,minWidth:0}}>
<div ref={scrollRef} onScroll={updateScrollState} style={{height:'100%',overflow:'auto'}}>
<div style={{display:'grid',gridTemplateColumns:cols,minWidth:'fit-content'}}>
<div style={{gridColumn:'1',gridRow:1,position:'sticky',left:0,top:0,zIndex:4,background:'var(--color-white)',padding:'20px 20px 12px',height:48,boxSizing:'border-box',display:'flex',alignItems:'center'}}>
<h3 style={{fontFamily:'var(--font-display)',fontSize:'var(--text-lg)',fontWeight:600,margin:0}}>{listings.length} Properties</h3>
</div>
{months.map((m,idx)=>(
<div key={m.label} style={{gridColumn:`${m.start+2} / ${idx+1<months.length?months[idx+1].start+2:days.length+2}`,gridRow:1,position:'sticky',top:0,left:labelColWidth,height:48,boxSizing:'border-box',zIndex:2,background:'var(--color-white)',padding:'14px 16px',fontFamily:'var(--font-display)',fontWeight:600,fontSize:15,width:'fit-content',maxWidth:'100%',whiteSpace:'nowrap'}}>{m.label}</div>
))}
<div style={{gridColumn:'1',gridRow:2,position:'sticky',left:0,top:48,zIndex:4,background:'var(--color-white)',borderBottom:'1px solid var(--border-default)',padding:'0 20px 12px'}}>
<Input placeholder="Search listings..." />
</div>
{days.map((d,i)=>(
<div key={i} style={{gridColumn:i+2,gridRow:2,position:'sticky',top:48,zIndex:2,background:'var(--color-white)',textAlign:'center',padding:'10px 4px',fontSize:12,color:'var(--text-secondary)',borderTop:'1px solid var(--border-default)',borderBottom:'1px solid var(--border-default)'}}>
<div>{d.toLocaleDateString('en-US',{weekday:'narrow'})}</div>
<div style={{fontWeight:600,color:'var(--text-primary)',marginTop:2}}>{d.getDate()}</div>
</div>
))}
{months.filter((m,idx)=>idx>0).map(m=>(
<div key={'div-'+m.label} style={{gridColumn:m.start+2,gridRow:'1 / 3',zIndex:3,borderLeft:'1px solid var(--border-default)',pointerEvents:'none'}} />
))}
<div style={{gridColumn:1,gridRow:`1 / ${listings.length+3}`,position:'sticky',left:labelColWidth,width:0,zIndex:5,borderRight:'1px solid var(--border-default)',pointerEvents:'none'}} />
{listings.map((l,li)=>{
const [hover,setHover]=React.useState(false);
return (
<React.Fragment key={l.name}>
<div onClick={()=>setSelected(l.name)} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)} style={{gridColumn:'1',gridRow:li+3,position:'sticky',left:0,zIndex:3,background:selected===l.name?'var(--surface-sunken)':hover?'var(--color-mist)':'var(--color-white)',display:'flex',alignItems:'center',gap:12,padding:'12px 20px',borderBottom:'1px solid var(--border-default)',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'}}>
<div style={{width:44,height:44,borderRadius:'var(--radius-md)',background:l.c,flexShrink:0}} />
<div>
<div style={{fontWeight:600,fontSize:14,color:'var(--text-primary)'}}>{l.name}</div>
<div style={{fontSize:12,color:'var(--text-secondary)'}}>{l.loc}</div>
</div>
</div>
{days.map((d,i)=>(
<div key={i} style={{gridColumn:i+2,gridRow:li+3,padding:'14px 6px',fontFamily:'var(--font-sans)',fontVariantNumeric:'tabular-nums',fontSize:12.5,color:'var(--text-primary)',background:selected===l.name?'var(--surface-sunken)':'transparent',borderLeft:d.getDate()===1?'1px solid var(--border-default)':'none',borderBottom:'1px solid var(--border-default)',transition:'background var(--duration-fast) var(--ease-standard)'}}>Rp{price(l.base,i).toLocaleString('en-US')}</div>
))}
</React.Fragment>);
})}
</div>
</div>
<div style={{position:'absolute',left:labelColWidth,top:0,bottom:0,width:32,background:'linear-gradient(to right, rgba(11,12,14,0.10), rgba(11,12,14,0))',pointerEvents:'none',opacity:canLeft?1:0,transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:5}} />
<div style={{position:'absolute',right:0,top:0,bottom:0,width:32,background:'linear-gradient(to left, rgba(11,12,14,0.10), rgba(11,12,14,0))',pointerEvents:'none',opacity:canRight?1:0,transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:5}} />
{canLeft&&<div style={{position:'absolute',left:labelColWidth+8,top:76,transform:'translateY(-50%)',zIndex:6}}><IconButton label="Scroll earlier" onClick={()=>scrollBy(-1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-left.svg" style={{width:16,height:16}} />} /></div>}
{canRight&&<div style={{position:'absolute',right:8,top:76,transform:'translateY(-50%)',zIndex:6}}><IconButton label="Scroll later" onClick={()=>scrollBy(1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-right.svg" style={{width:16,height:16}} />} /></div>}
</div>
</div>);
}
window.Pricing=Pricing;
