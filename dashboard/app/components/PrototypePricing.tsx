// @ts-nocheck
"use client";
// This file is the host-dashboard prototype with a data/API adapter at its edges.
import React from "react";
import ReactDOM from "react-dom";
// These implementations mirror the corresponding design-system sources in
// nicer.homes_design_system/components. They are kept local because the
// design-system bundle is browser-global in the original prototype.
function Input({label,type='text',placeholder,value,onChange,error,prefix}){const [focus,setFocus]=React.useState(false);return <label style={{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}}>{label&&<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>{label}</span>}<div style={{display:'flex',alignItems:'center',gap:8,height:38,boxSizing:'border-box',border:'1px solid '+(error?'var(--status-danger)':focus?'var(--focus-ring)':'var(--border-default)'),borderRadius:'var(--radius-full)',padding:'0 20px',background:'var(--surface-card)',transition:'border-color var(--duration-fast) var(--ease-standard)'}}>{prefix&&<span style={{color:'var(--text-muted)',fontSize:14}}>{prefix}</span>}<input type={type} placeholder={placeholder} value={value} onChange={onChange} onFocus={()=>setFocus(true)} onBlur={()=>setFocus(false)} style={{border:'none',outline:'none',fontSize:14,fontFamily:'var(--font-sans)',color:'var(--text-primary)',width:'100%',background:'transparent'}} /></div>{error&&<span style={{fontSize:12,color:'var(--status-danger)'}}>{error}</span>}</label>}
function IconButton({icon,label,size=36,active=false,onClick}){const [hover,setHover]=React.useState(false);const style={width:size,height:size,borderRadius:'var(--radius-full)',border:'none',background:active?'var(--surface-sunken)':hover?'var(--surface-sunken)':'transparent',color:'var(--text-primary)',display:'inline-flex',alignItems:'center',justifyContent:'center',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'};return <button type="button" aria-label={label} title={label} style={style} onClick={onClick} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>{icon}</button>}
function Select({label,options=[],value,onChange,pill=true}){return <label style={{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}}>{label&&<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>{label}</span>}<select value={value} onChange={onChange} style={{border:'1px solid var(--border-default)',borderRadius:'var(--radius-full)',height:38,boxSizing:'border-box',padding:'0 36px 0 20px',fontSize:14,fontWeight:pill?600:400,fontFamily:'var(--font-sans)',color:'var(--text-primary)',background:'var(--surface-card)',appearance:'none',backgroundImage:'url("https://unpkg.com/lucide-static@latest/icons/chevron-down.svg")',backgroundRepeat:'no-repeat',backgroundPosition:'right 14px center',backgroundSize:14,cursor:'pointer'}}>{options.map(o=><option key={o.value||o} value={o.value||o}>{o.label||o}</option>)}</select></label>}
function Button({variant='primary',size='md',disabled=false,children,onClick,type='button',style:styleProp}){const sizeMap={sm:{padding:'0 16px',fontSize:13,height:38},md:{padding:'0 20px',fontSize:14,height:44},lg:{padding:'0 26px',fontSize:15,height:52}};const base={fontFamily:'var(--font-sans)',fontWeight:600,borderRadius:'var(--radius-full)',border:'1px solid transparent',boxSizing:'border-box',cursor:disabled?'default':'pointer',transition:'background var(--duration-fast) var(--ease-standard), color var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)',opacity:disabled?0.45:1,display:'inline-flex',alignItems:'center',justifyContent:'center',gap:8,...sizeMap[size]};const variants={primary:{background:'var(--action-primary)',color:'var(--text-inverse)'},accent:{background:'var(--action-accent)',color:'var(--action-accent-ink)',boxShadow:'var(--glow-accent)'},secondary:{background:'var(--action-secondary)',color:'var(--text-primary)',borderColor:'var(--border-strong)'},ghost:{background:'transparent',color:'var(--text-primary)'}};return <button type={type} disabled={disabled} style={{...base,...variants[variant],...styleProp}} onClick={onClick}>{children}</button>}
function Toast({tone='neutral',children,onClose}){const tones={neutral:'var(--color-ink-600)',success:'var(--color-success-700)',danger:'var(--color-danger)'};return <div style={{background:tones[tone],color:'#fff',borderRadius:'var(--radius-md)',padding:'12px 16px',display:'flex',alignItems:'center',gap:12,fontFamily:'var(--font-sans)',fontSize:13,boxShadow:'var(--shadow-md)',maxWidth:340}}><span style={{flex:1}}>{children}</span>{onClose&&<button onClick={onClose} style={{border:'none',background:'none',color:'rgba(255,255,255,0.7)',cursor:'pointer',fontSize:14}}>×</button>}</div>}
function Switch({checked,onChange,label}){return <label style={{display:'inline-flex',alignItems:'center',gap:10,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-primary)',cursor:'pointer'}}><span onClick={()=>onChange&&onChange(!checked)} style={{width:38,height:22,borderRadius:'var(--radius-full)',background:checked?'var(--action-accent)':'var(--border-strong)',position:'relative',transition:'background var(--duration-standard) var(--ease-standard)'}}><span style={{position:'absolute',top:2,left:checked?18:2,width:18,height:18,borderRadius:'var(--radius-full)',background:'#fff',transition:'left var(--duration-standard) var(--ease-standard)',boxShadow:'var(--shadow-sm)'}} /></span>{label}</label>}
function InputWithSelectField({label,options=[],value,onChange,placeholder='Enter a value'}){const [focused,setFocused]=React.useState(false);const [activeIdx,setActiveIdx]=React.useState(-1);const ref=React.useRef(null);const isMatched=options.some(o=>o.value===value);const isCustom=value!=null&&value!==''&&!isMatched;const selectedOpt=options.find(o=>o.value===value);React.useEffect(()=>{if(!focused)return;const onDoc=e=>{if(ref.current&&!ref.current.contains(e.target))setFocused(false)};document.addEventListener('mousedown',onDoc);return()=>document.removeEventListener('mousedown',onDoc)},[focused]);const selectOption=o=>{onChange&&onChange(o.value);setFocused(false)};return <label style={{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}}>{label&&<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>{label}</span>}<div ref={ref} style={{position:'relative',height:38}}><div style={{position:focused?'absolute':'static',top:0,left:0,right:0,border:'1px solid '+(focused?'var(--focus-ring)':'var(--border-default)'),borderRadius:19,overflow:'hidden',background:'var(--color-white)',boxShadow:focused?'var(--shadow-lg)':'none',zIndex:10}}>{!focused?<div onClick={()=>setFocused(true)} style={{height:38,display:'flex',alignItems:'center',padding:'0 20px',cursor:'text'}}>{isCustom?<span style={{fontSize:14,color:'var(--text-primary)'}}>{value}</span>:selectedOpt?<span style={{fontSize:14,color:'var(--text-secondary)'}}>{selectedOpt.label}</span>:<span style={{fontSize:14,color:'var(--text-muted)'}}>{placeholder}</span>}</div>:<div style={{height:38,display:'flex',alignItems:'center',padding:'0 20px'}}><input autoFocus value={isCustom?value:''} onChange={e=>onChange&&onChange(e.target.value)} placeholder={placeholder} style={{border:'none',outline:'none',background:'transparent',fontSize:14,fontFamily:'var(--font-sans)',width:'100%'}} /></div>}{focused&&options.length>0&&<div style={{maxHeight:152,overflowY:'auto'}}>{options.map((o,i)=><div key={o.value} onMouseDown={e=>{e.preventDefault();selectOption(o)}} onMouseEnter={()=>setActiveIdx(i)} style={{display:'flex',alignItems:'center',height:38,padding:'0 20px',background:o.value===value?'#F5F5F5':activeIdx===i?'var(--color-mist)':'transparent',cursor:'pointer'}}>{o.label}</div>)}</div>}</div></div></label>}
function UrgencyRulesEditor({rules,setRules}){
const [hover,setHover]=React.useState(null);
const sorted=[...rules].sort((a,b)=>a.f-b.f);
const display=[];
let cursor=0;
sorted.forEach(r=>{if(r.f>cursor)display.push({f:cursor,t:r.f-1,d:0,gap:true});display.push(r);cursor=r.t+1;});
const max=Math.max(1,cursor);
const maxAbsD=Math.max(...rules.map(r=>Math.abs(parseFloat(r.d))||0),0.0001);
const colorFor=r=>{const a=r.gap?0:0.22+0.78*(Math.abs(parseFloat(r.d))||0)/maxAbsD;return `rgba(39,17,242,${a})`;};
const pct=r=>`${Math.round(parseFloat(r.d)*100)}%`;
const update=(i,k,v)=>setRules(rs=>rs.map((r,idx)=>idx===i?{...r,[k]:v}:r));
const remove=i=>setRules(rs=>rs.filter((_,idx)=>idx!==i));
const add=()=>setRules(rs=>{const last=rs[rs.length-1];const f=last?last.t+1:0;return [...rs,{f,t:f+3,d:-0.05}];});
const addGap=g=>setRules(rs=>[...rs,{f:g.f,t:g.t,d:0}]);
return (
<div>
<div style={{position:'relative',height:72,marginBottom:8,display:'flex',alignItems:'flex-end',gap:0}}>
{display.map((r,i)=>(
<div key={i} onMouseEnter={()=>setHover(i)} onMouseLeave={()=>setHover(h=>h===i?null:h)} style={{width:`${((r.t-r.f+1)/max)*100}%`,height:`${r.gap?4:Math.max(6,(Math.abs(parseFloat(r.d))||0)/maxAbsD*100)}%`,background:colorFor(r),position:'relative',marginRight:i<display.length-1?2:0,borderRadius:4,cursor:'default'}}>
{hover===i&&<div style={{position:'absolute',bottom:'calc(100% + 8px)',left:'50%',transform:'translateX(-50%)',background:'var(--color-ink-900)',color:'var(--color-white)',fontSize:11,fontWeight:600,padding:'6px 10px',borderRadius:'var(--radius-sm)',whiteSpace:'nowrap',zIndex:5,boxShadow:'var(--shadow-md)'}}>Day {r.f}–{r.t}: {pct(r)}</div>}
</div>
))}
</div>
<div style={{display:'flex',justifyContent:'space-between',fontSize:10.5,color:'var(--text-muted)',marginBottom:22}}><span>Day 0</span><span>Day {max-1}</span></div>
<div style={{display:'flex',flexDirection:'column',gap:6}}>
{display.map((r,i)=>r.gap?(
<div key={'gap'+i} onClick={()=>addGap(r)} style={{borderRadius:'var(--radius-md)',padding:'10px 14px',display:'flex',alignItems:'center',gap:14,background:'rgba(11,12,14,0.03)',cursor:'pointer'}}>
<span style={{fontSize:12,fontWeight:600,color:'var(--text-muted)',minWidth:90}}>Day {r.f}–{r.t}</span>
<span style={{fontSize:11.5,color:'var(--text-muted)',flex:1}}>Gap — click to set a discount</span>
</div>
):(()=>{const idx=rules.indexOf(r);return(
<div key={idx} style={{borderRadius:'var(--radius-md)',padding:'8px 14px',display:'flex',alignItems:'center',gap:16}}>
<span style={{fontSize:12,fontWeight:600,color:'var(--text-primary)',minWidth:80,flexShrink:0}}>Day <input className="tf2" style={{width:26,textAlign:'center',display:'inline',borderRadius:'var(--radius-sm)'}} value={r.f} onChange={e=>update(idx,'f',+e.target.value||0)} />–<input className="tf2" style={{width:26,textAlign:'center',display:'inline',borderRadius:'var(--radius-sm)'}} value={r.t} onChange={e=>update(idx,'t',+e.target.value||0)} /></span>
<input type="range" className="rng2" min="0" max="50" value={Math.round(Math.abs(parseFloat(r.d))*100)||0} onChange={e=>update(idx,'d',(-(+e.target.value)/100).toFixed(2))} style={{flex:1}} />
<span style={{fontSize:12,fontWeight:700,color:'var(--text-primary)',width:34,textAlign:'right'}}>{pct(r)}</span>
<IconButton label="Remove" onClick={()=>remove(idx)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:12,height:12,opacity:0.5}} />} />
</div>
);})())}
<div onClick={add} style={{borderRadius:'var(--radius-md)',padding:'10px 14px',display:'flex',alignItems:'center',gap:8,opacity:0.35,cursor:'pointer'}} onMouseEnter={e=>e.currentTarget.style.opacity=0.65} onMouseLeave={e=>e.currentTarget.style.opacity=0.35}>
<img src="https://unpkg.com/lucide-static@latest/icons/plus.svg" style={{width:13,height:13}} />
<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Add period</span>
</div>
</div>
</div>);
}
function genDays(n){
const start=new Date(2026,7,28);
return Array.from({length:n},(_,i)=>{const d=new Date(start);d.setDate(start.getDate()+i);return d;});
}
function monthLabel(d){return d.toLocaleDateString('en-US',{month:'long',year:'numeric'});}
function Pricing(){
const [days,setDays]=React.useState(genDays(28));
const [listings,setListings]=React.useState([
{name:'Villa Kayu',c:'var(--color-accent-300)',base:4850000,group:'Beachfront Collection'},
{name:'Villa Alang',c:'var(--color-mist)',base:3200000,group:'Beachfront Collection'},
{name:'Rumah Terang',c:'var(--color-ink-200)',base:5400000,group:'Ubud Retreats'},
]);
React.useEffect(()=>{fetch('/api/pricing-calendar?start='+new Date().toISOString().slice(0,10)+'&end='+new Date(Date.now()+27*86400000).toISOString().slice(0,10)).then(r=>r.ok?r.json():null).then(payload=>{if(!payload?.properties)return;const dates=(payload.days||[]).map(d=>d.stay_date).filter((d,i,a)=>a.indexOf(d)===i);setDays(dates.map(d=>new Date(d+'T00:00:00Z')));setListings(payload.properties.map((p,i)=>({name:p.name,c:['var(--color-accent-300)','var(--color-mist)','var(--color-ink-200)'][i%3],base:Number((payload.days||[]).find(d=>d.property_id===p.id)?.current_price||0),group:'Pricing group '+p.pricing_group_id,prices:Object.fromEntries((payload.days||[]).filter(d=>d.property_id===p.id).map(d=>[d.stay_date,Number(d.current_price||0)]))})));}).catch(()=>{});},[]);
const groupOrder=[];listings.forEach(l=>{if(!groupOrder.includes(l.group))groupOrder.push(l.group);});
let rowCursor=3;let propCursor=0;
const groups=groupOrder.map(gname=>{
const items=listings.filter(l=>l.group===gname);
const row=rowCursor;rowCursor+=1;
items.forEach(it=>{it.row=rowCursor;rowCursor+=1;it.propIndex=propCursor;propCursor+=1;});
return {name:gname,items,row};
});
const totalRows=rowCursor;
const [selected,setSelected]=React.useState(null);
const [hoverCellKey,setHoverCellKey]=React.useState(null);
const [rangeAnchor,setRangeAnchor]=React.useState(null);
const [rangeSelection,setRangeSelection]=React.useState(null);
const lastPointer=React.useRef({x:0,y:0});
const [toast,setToast]=React.useState(null);
const [busy,setBusy]=React.useState(null);
const [lastSync,setLastSync]=React.useState({fetch:'2 hours ago',comp:'Yesterday at 6:40 PM',generate:'5 hours ago',apply:'3 days ago'});
const [actionsOpen,setActionsOpen]=React.useState(false);
const [globalOpen,setGlobalOpen]=React.useState(false);
const [globalSettings,setGlobalSettings]=React.useState({minComp:'3',positioning:'1',guestToHost:'0.839',minIDR:'900,000',maxIDR:'1,800,000',step:'1,000',useUrgency:'on',method:'median',manualBase:'',rules:[{f:0,t:3,d:-0.3},{f:4,t:7,d:-0.2},{f:8,t:14,d:-0.1},{f:15,t:30,d:-0.05}]});
const setGlobalField=(field,val)=>setGlobalSettings(s=>({...s,[field]:val}));
const saveGlobal=()=>{setToast('Global settings saved.');setTimeout(()=>setToast(null),2600);setGlobalOpen(false);};
const [tooltipData,setTooltipData]=React.useState(null);
const [priceOverrides,setPriceOverrides]=React.useState({});
const [rangePriceInput,setRangePriceInput]=React.useState('');
const [propertyData,setPropertyData]=React.useState({});
const [groupPickerOpen,setGroupPickerOpen]=React.useState(false);
const [groupOverrides,setGroupOverrides]=React.useState({});
const groupPickerRef=React.useRef(null);
const [groupActiveIdx,setGroupActiveIdx]=React.useState(-1);
React.useEffect(()=>{
if(!groupPickerOpen)return;
const onDoc=(e)=>{if(groupPickerRef.current&&!groupPickerRef.current.contains(e.target))setGroupPickerOpen(false);};
document.addEventListener('mousedown',onDoc);
return ()=>document.removeEventListener('mousedown',onDoc);
},[groupPickerOpen]);
const [posInfoOpen,setPosInfoOpen]=React.useState(false);
const activeProperty=selected&&!selected.startsWith('group:')?listings.find(l=>l.name===selected):null;
const propFor=(name)=>propertyData[name]||{enabled:true,method:'median',manualBase:'',positioning:'1',minComp:'',useUrgency:'global',urgencyOpen:false,rules:[{f:0,t:3,d:-0.3},{f:4,t:7,d:-0.2},{f:8,t:14,d:-0.1},{f:15,t:30,d:-0.05}],minIDR:'',maxIDR:'',step:''};
const setPropField=(name,field,val)=>setPropertyData(d=>({...d,[name]:{...propFor(name),[field]:val}}));
const setPropRules=(name,updater)=>setPropertyData(d=>{const cur=propFor(name);const rules=typeof updater==='function'?updater(cur.rules):updater;return {...d,[name]:{...cur,rules}};});
const saveProperty=(name)=>{setToast('Property settings saved.');setTimeout(()=>setToast(null),2600);setSelected(null);};
const [groupData,setGroupData]=React.useState({});
const defaultGroupUrls=(gname)=>Array.from({length:9},(_,i)=>`https://www.airbnb.com/rooms/${1500000000000+Math.abs(Math.round(Math.sin(gname.length+i*3.1)*99999999999))}`).join('\n');
const activeGroupName=selected&&selected.startsWith('group:')?selected.slice(6):null;
const groupFor=(gname)=>groupData[gname]||{name:gname,minComp:'',urls:defaultGroupUrls(gname)};
const setGroupField=(gname,field,val)=>setGroupData(d=>({...d,[gname]:{...groupFor(gname),[field]:val}}));
const saveGroup=(gname)=>{setToast('Pricing group saved.');setTimeout(()=>setToast(null),2600);setSelected(null);};
const scrollRef=React.useRef(null);
const [canLeft,setCanLeft]=React.useState(false);
const [canRight,setCanRight]=React.useState(true);
const [currentMonth,setCurrentMonth]=React.useState(0);
const colWidth=96;
const labelColWidth=280;
const months=[];
days.forEach((d,i)=>{if(i===0||d.getDate()===1)months.push({label:monthLabel(d),start:i});});
const updateHoverFromPointer=(x,y)=>{
const el=document.elementFromPoint(x,y);
const cellEl=el&&el.closest&&el.closest('[data-cell-key]');
if(!cellEl){setHoverCellKey(null);setTooltipData(null);return;}
setHoverCellKey(cellEl.getAttribute('data-cell-key'));
const diff=Number(cellEl.getAttribute('data-diff')||0);
const breakdownStr=cellEl.getAttribute('data-breakdown');
if(!diff||!breakdownStr){setTooltipData(null);return;}
const cur=Number(cellEl.getAttribute('data-cur')||0);
const breakdown=JSON.parse(breakdownStr);
const rect=cellEl.getBoundingClientRect();
const placeBelow=rect.top<320;
const left=Math.min(Math.max(rect.left+rect.width/2,140),window.innerWidth-140);
setTooltipData({left,top:placeBelow?rect.bottom+8:rect.top-8,placeBelow,diff,cur,breakdown});
};
const updateScrollState=()=>{
const el=scrollRef.current;if(!el)return;
updateHoverFromPointer(lastPointer.current.x,lastPointer.current.y);
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
const fmtRp=n=>'Rp '+Math.round(n).toLocaleString('id-ID');
const buildBreakdown=(base,i,li,cur)=>{
const seed=Math.sin(i*3.1+li*5.7);
const guestMedian=Math.round(base*(0.75+0.35*Math.abs(Math.sin(i*2.1+li*1.3))));
const hasCompetitorData=Math.abs(Math.sin(i*0.9+li))>0.15;
const requiredComp=3;
const availableComp=hasCompetitorData?(1+Math.floor(Math.abs(Math.sin(i*1.3+li*0.7))*3)):null;
const guestToHostFactor=+(0.75+0.2*Math.abs(Math.cos(i*0.5+li))).toFixed(3);
const hostMedian=Math.round(guestMedian*guestToHostFactor);
const positioningApplies=Math.abs(Math.sin(i*0.4+li*1.9))>0.1;
const positioningFactor=positioningApplies?+(0.9+0.2*Math.abs(Math.sin(i*0.3+li*2))).toFixed(2):null;
const basePrice=Math.round(hostMedian*(positioningFactor==null?1:positioningFactor));
const urgencyApplies=i<=14;
const urgencyPct=urgencyApplies?+(seed*30).toFixed(1):null;
const raw=urgencyApplies?Math.round(basePrice*(1+urgencyPct/100)):basePrice;
const rounded=Math.round(raw/1000)*1000;
const dateOverride=Math.abs(Math.sin(i*4.4+li*3.3))>0.93;
const final=dateOverride?cur:rounded;
return {source:'airbnb_market_median',guestMedian,availableComp,requiredComp,guestToHostFactor,hostMedian,positioningFactor,basePrice,daysUntilStay:urgencyApplies?i:null,urgencyPct,raw,rounded,final,dateOverride};
};
const recommendation=(base,i,li)=>{
const cur=price(base,i);
const breakdown=buildBreakdown(base,i,li,cur);
const rec=breakdown.final;
if(rec===cur)return {rec:cur,breakdown:null};
return {rec,breakdown};
};
const runAction=(key,label)=>{
setBusy(key);
const paths={fetch:'/api/imports/hostex/booking-site',generate:'/api/pricing/run',apply:'/api/pricing/publish'};
const path=paths[key];
if(!path){setTimeout(()=>{setBusy(null);setToast(label);},500);return;}
fetch(path,{method:'POST',headers:{'X-CSRF-Token':decodeURIComponent(document.cookie.split('; ').find(row=>row.startsWith('pricing_csrf='))?.split('=')[1]||'')}}).then(async response=>{const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.detail||label+' failed');setBusy(null);setToast(label);if(key==='fetch')setLastSync(s=>({...s,fetch:'Just now'}));if(key==='generate')setLastSync(s=>({...s,generate:'Just now'}));if(key==='apply')setLastSync(s=>({...s,apply:'Just now'}));setTimeout(()=>setToast(null),2600);}).catch(error=>{setBusy(null);setToast(error.message);});
};
const handleCellClick=(propIndex,dayIndex)=>{
if(!rangeAnchor){
setRangeAnchor({propIndex,dayIndex});
setRangeSelection({minProp:propIndex,maxProp:propIndex,minDay:dayIndex,maxDay:dayIndex});
}else{
setRangeSelection({minProp:Math.min(rangeAnchor.propIndex,propIndex),maxProp:Math.max(rangeAnchor.propIndex,propIndex),minDay:Math.min(rangeAnchor.dayIndex,dayIndex),maxDay:Math.max(rangeAnchor.dayIndex,dayIndex)});
setRangeAnchor(null);
}
};
const clearRange=()=>{setRangeAnchor(null);setRangeSelection(null);setRangePriceInput('');};
const saveRangePrice=()=>{
const val=Number(String(rangePriceInput).replace(/[^0-9]/g,''));
if(!val||!rangeSelection)return;
const updates={};
listings.forEach(l=>{
if(l.propIndex<rangeSelection.minProp||l.propIndex>rangeSelection.maxProp)return;
for(let i=rangeSelection.minDay;i<=rangeSelection.maxDay;i++){updates[l.name+'-'+i]=val;}
});
setPriceOverrides(o=>({...o,...updates}));
const nDates=(rangeSelection.maxDay-rangeSelection.minDay+1)*(rangeSelection.maxProp-rangeSelection.minProp+1);
setToast(`Price updated for ${nDates} date${nDates===1?'':'s'}.`);
setTimeout(()=>setToast(null),2600);
clearRange();
};
const dateLabel=d=>d.toLocaleDateString('en-US',{month:'short',day:'numeric'});
const cols=`${labelColWidth}px repeat(${days.length},${colWidth}px)`;
return (
<div style={{flex:1,display:'flex',flexDirection:'column',minWidth:0,background:'var(--color-white)',position:'relative',zIndex:1}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',rowGap:12,padding:'20px 24px',borderBottom:'1px solid var(--border-default)'}}>
<div style={{display:'flex',alignItems:'center',gap:12}}>
<Select value={String(currentMonth)} pill onChange={e=>scrollToCol(months[Number(e.target.value)].start)} options={months.map((m,idx)=>({label:m.label,value:String(idx)}))} />
<div onClick={scrollToToday} style={{padding:'0 16px',height:38,boxSizing:'border-box',display:'flex',alignItems:'center',borderRadius:'var(--radius-full)',border:'1px solid var(--border-default)',fontSize:13,fontWeight:600,cursor:'pointer'}}>Today</div>
</div>
<div style={{display:'flex',alignItems:'center',gap:8}}>
<Button variant="secondary" size="sm" onClick={()=>setGlobalOpen(true)}>Global settings</Button>
<Button variant="secondary" size="sm" onClick={()=>setActionsOpen(true)}>Actions</Button>
</div>
</div>
{toast&&<div style={{position:'absolute',top:20,right:24,zIndex:20}}><Toast tone="success" onClose={()=>setToast(null)}>{toast}</Toast></div>}
<div style={{flex:1,position:'relative',minHeight:0,minWidth:0}}>
<div ref={scrollRef} onScroll={updateScrollState} onMouseMove={e=>{lastPointer.current={x:e.clientX,y:e.clientY};updateHoverFromPointer(e.clientX,e.clientY);}} onMouseLeave={()=>{setHoverCellKey(null);setTooltipData(null);}} style={{height:'100%',overflow:'auto'}}>
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
<div style={{gridColumn:1,gridRow:`1 / ${totalRows}`,position:'sticky',left:labelColWidth,width:0,zIndex:5,borderRight:'1px solid var(--border-default)',pointerEvents:'none'}} />
{groups.map(g=>{
const headerRow=g.row;
return (
<React.Fragment key={g.name}>
<div style={{gridColumn:'1',gridRow:headerRow,position:'sticky',left:0,top:96,zIndex:5,boxSizing:'border-box'}}>
<div onClick={()=>setSelected('group:'+g.name)} style={{width:labelColWidth,height:'100%',boxSizing:'border-box',display:'flex',alignItems:'center',padding:'10px 20px',cursor:'pointer',background:selected==='group:'+g.name?'var(--surface-sunken)':'var(--color-mist)',borderBottom:'1px solid var(--border-default)',borderTop:'1px solid var(--border-default)'}}>
<span style={{fontWeight:700,fontSize:13,color:'var(--text-primary)'}}>{g.name}</span>
</div>
</div>
<div style={{gridColumn:'2 / -1',gridRow:headerRow,position:'sticky',top:96,background:'var(--color-mist)',borderBottom:'1px solid var(--border-default)',borderTop:'1px solid var(--border-default)',boxSizing:'border-box',zIndex:4}} />
{g.items.map((l,li)=>{
return (
<React.Fragment key={l.name}>
<div onClick={()=>setSelected(l.name)} style={{gridColumn:'1',gridRow:l.row,position:'sticky',left:0,zIndex:3,background:selected===l.name?'var(--surface-sunken)':'var(--color-white)',display:'flex',alignItems:'center',gap:12,padding:'12px 20px',borderBottom:'1px solid var(--border-default)',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'}}>
<div style={{width:44,height:44,borderRadius:'var(--radius-md)',background:l.c,flexShrink:0}} />
<div>
<div style={{fontWeight:600,fontSize:14,color:'var(--text-primary)'}}>{l.name}</div>
<div style={{fontSize:12,color:'var(--text-secondary)'}}>IDR (Rp)</div>
</div>
</div>
{days.map((d,i)=>{
const cur=priceOverrides[l.name+'-'+i]??(l.prices?.[days[i]?.toISOString().slice(0,10)]||price(l.base,i));
const {rec,breakdown}=recommendation(l.base,i,li);
const diff=rec-cur;
const cellKey=l.name+'-'+i;
const isHover=hoverCellKey===cellKey;
const inRange=rangeSelection&&l.propIndex>=rangeSelection.minProp&&l.propIndex<=rangeSelection.maxProp&&i>=rangeSelection.minDay&&i<=rangeSelection.maxDay;
const isAnchor=rangeAnchor&&rangeAnchor.propIndex===l.propIndex&&rangeAnchor.dayIndex===i;
const edgeTop=(isAnchor||inRange)&&l.propIndex===(rangeSelection?rangeSelection.minProp:l.propIndex);
const edgeBottom=(isAnchor||inRange)&&l.propIndex===(rangeSelection?rangeSelection.maxProp:l.propIndex);
const edgeLeft=(isAnchor||inRange)&&i===(rangeSelection?rangeSelection.minDay:i);
const edgeRight=(isAnchor||inRange)&&i===(rangeSelection?rangeSelection.maxDay:i);
const cellBg=isAnchor?'var(--action-accent-soft)':inRange?'rgba(207,242,17,0.16)':isHover?'rgba(11,12,14,0.04)':selected===l.name?'var(--surface-sunken)':'var(--color-white)';
return (
<div key={i} onClick={()=>handleCellClick(l.propIndex,i)} data-cell-key={cellKey} data-diff={diff} data-cur={cur} data-breakdown={breakdown?JSON.stringify(breakdown):''} style={{gridColumn:i+2,gridRow:l.row,position:'relative',padding:'14px 8px',textAlign:'right',fontFamily:'var(--font-sans)',fontVariantNumeric:'tabular-nums',fontSize:12.5,color:'var(--text-primary)',background:cellBg,borderTop:edgeTop?'1.5px solid var(--color-accent-500)':'none',borderBottom:edgeBottom?'1.5px solid var(--color-accent-500)':'1px solid var(--border-default)',borderLeft:edgeLeft?'1.5px solid var(--color-accent-500)':(d.getDate()===1?'1px solid var(--border-default)':'none'),borderRight:edgeRight?'1.5px solid var(--color-accent-500)':'none',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'}}>
<div>{cur.toLocaleString('en-US')}</div>
{diff!==0&&<div style={{marginTop:2,fontSize:11,fontWeight:600,color:diff>0?'var(--status-success)':'var(--status-danger)'}}>{rec.toLocaleString('en-US')}</div>}
</div>);
})}
</React.Fragment>);
})}
</React.Fragment>);
})}
</div>
</div>
<div style={{position:'absolute',left:labelColWidth,top:0,bottom:0,width:32,background:'linear-gradient(to right, rgba(11,12,14,0.10), rgba(11,12,14,0))',pointerEvents:'none',opacity:canLeft?1:0,transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:5}} />
<div style={{position:'absolute',right:0,top:0,bottom:0,width:32,background:'linear-gradient(to left, rgba(11,12,14,0.10), rgba(11,12,14,0))',pointerEvents:'none',opacity:canRight?1:0,transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:5}} />
{canLeft&&<div style={{position:'absolute',left:labelColWidth+8,top:76,transform:'translateY(-50%)',zIndex:6}}><IconButton label="Scroll earlier" onClick={()=>scrollBy(-1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-left.svg" style={{width:16,height:16}} />} /></div>}
{canRight&&<div style={{position:'absolute',right:8,top:76,transform:'translateY(-50%)',zIndex:6}}><IconButton label="Scroll later" onClick={()=>scrollBy(1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-right.svg" style={{width:16,height:16}} />} /></div>}
{tooltipData&&ReactDOM.createPortal(
<div style={{position:'fixed',left:tooltipData.left,top:tooltipData.top,transform:`translate(-50%, ${tooltipData.placeBelow?'0':'-100%'})`,width:264,background:'var(--color-ink-600)',color:'#fff',fontSize:11.5,lineHeight:1.5,padding:'12px 14px',borderRadius:'var(--radius-sm)',fontFamily:'var(--font-sans)',zIndex:1000,boxShadow:'var(--shadow-md)',textAlign:'left',pointerEvents:'none'}}>
<div style={{fontWeight:700,marginBottom:8,fontSize:13,color:tooltipData.diff>0?'#8fe8bd':'#ffb4b4'}}>{tooltipData.diff>0?'+':'-'}Rp{Math.abs(tooltipData.diff).toLocaleString('en-US')} ({tooltipData.diff>0?'+':'-'}{Math.abs(Math.round(tooltipData.diff/tooltipData.cur*100))}%)</div>
<div style={{display:'flex',flexDirection:'column',gap:3}}>
{[
['Price source',tooltipData.breakdown.source],
['Airbnb guest median',fmtRp(tooltipData.breakdown.guestMedian)],
 tooltipData.breakdown.availableComp!=null&&['Available / required competitors',`${tooltipData.breakdown.availableComp} / ${tooltipData.breakdown.requiredComp}`],
['Guest-to-host factor',tooltipData.breakdown.guestToHostFactor],
['Estimated host median',fmtRp(tooltipData.breakdown.hostMedian)],
 tooltipData.breakdown.positioningFactor!=null&&['Positioning factor',tooltipData.breakdown.positioningFactor],
['Base price',fmtRp(tooltipData.breakdown.basePrice)],
 tooltipData.breakdown.daysUntilStay!=null&&['Days until stay',tooltipData.breakdown.daysUntilStay],
 tooltipData.breakdown.urgencyPct!=null&&['Urgency adjustment',`${tooltipData.breakdown.urgencyPct>0?'+':''}${tooltipData.breakdown.urgencyPct.toFixed(1)}%`],
['Raw / rounded / final',`${fmtRp(tooltipData.breakdown.raw)} / ${fmtRp(tooltipData.breakdown.rounded)} / ${fmtRp(tooltipData.breakdown.final)}`],
['Date override',tooltipData.breakdown.dateOverride?'Yes':'No'],
].filter(Boolean).map(([k,v])=>(
<div key={k} style={{display:'flex',justifyContent:'space-between',gap:12}}>
<span style={{color:'rgba(255,255,255,0.6)'}}>{k}</span>
<span style={{fontWeight:600,textAlign:'right'}}>{v}</span>
</div>
))}
</div>
</div>, document.body)}
{ReactDOM.createPortal(
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:300,background:'var(--color-white)',boxShadow:actionsOpen?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${actionsOpen?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:201,display:'flex',flexDirection:'column',padding:24,boxSizing:'border-box'}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:20}}>
<h3 style={{fontFamily:'var(--font-display)',fontSize:'var(--text-lg)',fontWeight:600,margin:0}}>Actions</h3>
<IconButton label="Close" onClick={()=>setActionsOpen(false)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} />
</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'flex',flexDirection:'column',gap:4}}>
<Button variant="secondary" size="sm" style={{width:'100%'}} onClick={()=>runAction('fetch','Prices fetched from your channels.')} disabled={busy==='fetch'}>{busy==='fetch'?'Fetching…':'Fetch current prices'}</Button>
<span style={{fontSize:11,color:'var(--text-muted)',textAlign:'center'}}>Last fetched: {lastSync.fetch}</span>
</div>
<div style={{display:'flex',flexDirection:'column',gap:4}}>
<Button variant="secondary" size="sm" style={{width:'100%'}} onClick={()=>runAction('comp','Competitor data refreshed.')} disabled={busy==='comp'}>{busy==='comp'?'Refreshing…':'Refresh competitor data'}</Button>
<span style={{fontSize:11,color:'var(--text-muted)',textAlign:'center'}}>Last refreshed: {lastSync.comp}</span>
</div>
<div style={{display:'flex',flexDirection:'column',gap:4}}>
<Button variant="secondary" size="sm" style={{width:'100%'}} onClick={()=>runAction('generate','Price recommendations generated.')} disabled={busy==='generate'}>{busy==='generate'?'Generating…':'Generate price recommendations'}</Button>
<span style={{fontSize:11,color:'var(--text-muted)',textAlign:'center'}}>Last generated: {lastSync.generate}</span>
</div>
<div style={{display:'flex',flexDirection:'column',gap:4}}>
<Button variant="accent" size="sm" style={{width:'100%'}} onClick={()=>runAction('apply','Prices applied to your calendar.')} disabled={busy==='apply'}>{busy==='apply'?'Applying…':'Apply prices'}</Button>
<span style={{fontSize:11,color:'var(--text-muted)',textAlign:'center'}}>Last applied: {lastSync.apply}</span>
</div>
</div>
</div>, document.body)}
{ReactDOM.createPortal(
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:300,background:'var(--color-white)',boxShadow:(rangeSelection&&!rangeAnchor)?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${rangeSelection&&!rangeAnchor?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:202,display:'flex',flexDirection:'column',padding:24,boxSizing:'border-box'}}>
<div style={{marginBottom:20,display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:12}}>
<div>
{rangeSelection&&<div style={{fontSize:16,fontWeight:600,color:'var(--text-primary)',marginBottom:4}}>{dateLabel(days[rangeSelection.minDay])} – {dateLabel(days[rangeSelection.maxDay])}</div>}
{rangeSelection&&<div style={{fontSize:14,color:'var(--text-secondary)'}}>{rangeSelection.maxProp-rangeSelection.minProp+1} propert{rangeSelection.maxProp-rangeSelection.minProp+1===1?'y':'ies'} selected</div>}
</div>
<IconButton label="Close" onClick={clearRange} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} />
</div>
<Input label="Nightly price" prefix="Rp" placeholder="e.g. 4,500,000" value={rangePriceInput} onChange={e=>setRangePriceInput(e.target.value)} />
<Button variant="accent" size="sm" style={{width:'100%',marginTop:16}} onClick={saveRangePrice}>Save</Button>
</div>, document.body)}
{ReactDOM.createPortal(
<div onClick={()=>setGlobalOpen(false)} style={{position:'fixed',inset:0,background:'rgba(11,12,14,0.28)',backdropFilter:'blur(2px)',opacity:globalOpen?1:0,pointerEvents:globalOpen?'auto':'none',transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:207}} />, document.body)}
{ReactDOM.createPortal(
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:460,background:'var(--color-white)',boxShadow:globalOpen?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${globalOpen?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:208,display:'flex',flexDirection:'column'}}>
<div style={{padding:'24px 28px 20px',borderBottom:'1px solid var(--border-default)',display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:12}}>
<div>
<div style={{fontFamily:'var(--font-display)',fontSize:20,fontWeight:600,color:'var(--text-primary)'}}>Global settings</div>
<div style={{fontSize:12,color:'var(--text-secondary)',marginTop:4}}>Defaults every group and property inherit from</div>
</div>
<IconButton label="Close" onClick={()=>setGlobalOpen(false)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} />
</div>
<div style={{flex:1,overflow:'auto',padding:'20px 28px',display:'flex',flexDirection:'column',gap:20}}>
<div>
<Input label="Guest-to-host factor" value={globalSettings.guestToHost} onChange={e=>setGlobalField('guestToHost',e.target.value)} />
<div style={{fontSize:11.5,color:'var(--text-muted)',marginTop:6}}>Converts Airbnb guest median to estimated host revenue.</div>
</div>
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Base price</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'flex',gap:0,background:'var(--surface-sunken)',borderRadius:'var(--radius-md)',padding:3}}>
{[{label:'Market median',value:'median'},{label:'Manual',value:'manual'}].map(o=>(
<div key={o.value} onClick={()=>setGlobalField('method',o.value)} style={{flex:1,textAlign:'center',padding:'7px 0',borderRadius:'var(--radius-sm)',fontSize:12.5,fontWeight:600,cursor:'pointer',background:globalSettings.method===o.value?'var(--color-white)':'transparent',color:globalSettings.method===o.value?'var(--text-primary)':'var(--text-secondary)',boxShadow:globalSettings.method===o.value?'var(--shadow-sm)':'none',transition:'background var(--duration-fast) var(--ease-standard)'}}>{o.label}</div>
))}
</div>
{globalSettings.method==='manual'&&<Input label="Manual base price" placeholder="Example: 4,500,000" value={globalSettings.manualBase} onChange={e=>setGlobalField('manualBase',e.target.value)} />}
{globalSettings.method==='median'&&<React.Fragment>
<Input label="Market positioning factor" value={globalSettings.positioning} onChange={e=>setGlobalField('positioning',e.target.value)} />
<Input label="Minimum competitor count" value={globalSettings.minComp} onChange={e=>setGlobalField('minComp',e.target.value)} />
</React.Fragment>}
</div>
</div>
<div>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:14}}>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)'}}>Discounts by days left until stay</div>
<Switch checked={globalSettings.useUrgency!=='off'} onChange={v=>setGlobalField('useUrgency',v?'on':'off')} />
</div>
{globalSettings.useUrgency!=='off'&&<UrgencyRulesEditor rules={globalSettings.rules} setRules={u=>setGlobalSettings(s=>({...s,rules:typeof u==='function'?u(s.rules):u}))} />}
</div>
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Bounds and rounding</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
<Input label="Minimum price" value={globalSettings.minIDR} onChange={e=>setGlobalField('minIDR',e.target.value)} />
<Input label="Maximum price" value={globalSettings.maxIDR} onChange={e=>setGlobalField('maxIDR',e.target.value)} />
</div>
<Input label="Round to nearest" value={globalSettings.step} onChange={e=>setGlobalField('step',e.target.value)} />
</div>
</div>
</div>
<div style={{padding:'16px 28px',borderTop:'1px solid var(--border-default)',display:'flex',gap:10}}>
<Button variant="accent" size="sm" style={{width:'100%'}} onClick={saveGlobal}>Save</Button>
</div>
</div>, document.body)}
{ReactDOM.createPortal(
<div onClick={()=>setSelected(null)} style={{position:'fixed',inset:0,background:'rgba(11,12,14,0.28)',backdropFilter:'blur(2px)',opacity:activeGroupName?1:0,pointerEvents:activeGroupName?'auto':'none',transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:203}} />, document.body)}
{ReactDOM.createPortal((()=>{
const g=activeGroupName?groups.find(x=>x.name===activeGroupName):null;
const gd=activeGroupName?groupFor(activeGroupName):null;
return (
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:400,background:'var(--color-white)',boxShadow:activeGroupName?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${activeGroupName?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:204,display:'flex',flexDirection:'column'}}>
{g&&gd&&<React.Fragment>
<div style={{padding:'24px 28px 20px',borderBottom:'1px solid var(--border-default)',display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:12}}>
<div style={{flex:1,minWidth:0}}>
<div style={{fontSize:11,fontWeight:700,letterSpacing:'0.04em',textTransform:'uppercase',color:'var(--text-muted)',marginBottom:6}}>Pricing group</div>
<div style={{display:'flex',alignItems:'center',gap:8}}>
<input value={gd.name} onChange={e=>setGroupField(g.name,'name',e.target.value)} style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:600,color:'var(--text-primary)',border:'none',outline:'none',background:'transparent',padding:0,minWidth:0,flex:'0 1 auto',borderRadius:'var(--radius-sm)'}} onFocus={e=>e.target.style.background='var(--color-mist)'} onBlur={e=>e.target.style.background='transparent'} />
<img src="https://unpkg.com/lucide-static@latest/icons/pencil.svg" style={{width:14,height:14,opacity:0.35,flexShrink:0}} />
</div>
</div>
<IconButton label="Close" onClick={()=>setSelected(null)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} />
</div>
<div style={{flex:1,overflow:'auto',padding:'20px 28px',display:'flex',flexDirection:'column',gap:20}}>
<div>
<div style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)',marginBottom:8}}>Properties in this group</div>
<div style={{display:'flex',flexWrap:'wrap',gap:8}}>
{g.items.map(it=>(
<div key={it.name} style={{display:'flex',alignItems:'center',gap:6,padding:'6px 12px 6px 6px',borderRadius:'var(--radius-full)',background:'var(--color-mist)',border:'1px solid var(--border-default)'}}>
<div style={{width:20,height:20,borderRadius:'50%',background:it.c,flexShrink:0}} />
<span style={{fontSize:12,fontWeight:600,color:'var(--text-primary)'}}>{it.name}</span>
</div>
))}
</div>
</div>
<div>
<InputWithSelectField label="Minimum competitor count" value={gd.minComp} onChange={v=>setGroupField(g.name,'minComp',v)} options={[{label:'Global: '+globalSettings.minComp,value:'',linked:true}]} />
<div style={{fontSize:11.5,color:'var(--text-muted)',marginTop:6}}>Threshold for refreshing the saved market median.</div>
</div>
<div>
<div style={{fontSize:13,fontWeight:600,color:'var(--text-primary)',marginBottom:8}}>Competitor URLs</div>
<textarea value={gd.urls} onChange={e=>setGroupField(g.name,'urls',e.target.value)} rows={9} style={{width:'100%',boxSizing:'border-box',resize:'vertical',fontFamily:'var(--font-sans)',fontSize:12,lineHeight:1.7,color:'var(--text-primary)',padding:'12px 14px',borderRadius:'var(--radius-md)',border:'1px solid var(--border-default)',outline:'none'}} />
</div>
</div>
<div style={{padding:'16px 28px',borderTop:'1px solid var(--border-default)',display:'flex',gap:10}}>
<Button variant="accent" size="sm" style={{width:'100%'}} onClick={()=>saveGroup(g.name)}>Save</Button>
</div>
</React.Fragment>}
</div>);
})(), document.body)}
{ReactDOM.createPortal(
<div onClick={()=>setSelected(null)} style={{position:'fixed',inset:0,background:'rgba(11,12,14,0.28)',backdropFilter:'blur(2px)',opacity:activeProperty?1:0,pointerEvents:activeProperty?'auto':'none',transition:'opacity var(--duration-standard) var(--ease-standard)',zIndex:205}} />, document.body)}
{ReactDOM.createPortal((()=>{
const l=activeProperty;
const pd=l?propFor(l.name):null;
return (
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:460,background:'var(--color-white)',boxShadow:activeProperty?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${activeProperty?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:206,display:'flex',flexDirection:'column'}}>
{l&&pd&&<React.Fragment>
<div style={{padding:'24px 28px 20px',borderBottom:'1px solid var(--border-default)',display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:12}}>
<div>
<div style={{fontFamily:'var(--font-display)',fontSize:20,fontWeight:600,color:'var(--text-primary)'}}>{l.name}</div>
<div ref={groupPickerRef} style={{position:'relative',marginTop:4}}>
<div onClick={()=>{setGroupPickerOpen(o=>!o);setGroupActiveIdx(-1);}} onKeyDown={e=>{
if(e.key==='Enter'||e.key===' '){e.preventDefault();setGroupPickerOpen(o=>!o);setGroupActiveIdx(-1);}
else if(e.key==='ArrowDown'){e.preventDefault();setGroupPickerOpen(true);setGroupActiveIdx(i=>Math.min(i+1,groups.length-1));}
else if(e.key==='ArrowUp'){e.preventDefault();setGroupActiveIdx(i=>Math.max(i-1,0));}
else if(e.key==='Enter'&&groupActiveIdx>=0){}
else if(e.key==='Escape'){setGroupPickerOpen(false);}
}} tabIndex={0} role="button" aria-haspopup="listbox" aria-expanded={groupPickerOpen} style={{display:'inline-flex',alignItems:'center',gap:6,cursor:'pointer',padding:'3px 8px',margin:'-3px -8px',borderRadius:'var(--radius-sm)',outline:'none',transition:'background var(--duration-fast) var(--ease-standard)'}} onMouseEnter={e=>e.currentTarget.style.background='rgba(11,12,14,0.05)'} onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
<span style={{fontSize:14,fontWeight:500,color:'var(--text-primary)'}}>{groupOverrides[l.name]||l.group}</span>
<img src="https://unpkg.com/lucide-static@latest/icons/pencil.svg" style={{width:12,height:12,opacity:0.35}} />
</div>
{groupPickerOpen&&<div role="listbox" style={{position:'absolute',top:'calc(100% + 6px)',left:0,background:'var(--color-white)',border:'1px solid var(--border-default)',borderRadius:'var(--radius-md)',boxShadow:'var(--shadow-lg)',padding:6,zIndex:10,minWidth:200,maxHeight:38*5,overflowY:'auto'}}>
{groups.map((g,gi)=>{
const cur=groupOverrides[l.name]||l.group;
const isSelected=g.name===cur;
const isActive=groupActiveIdx===gi;
return (
<div key={g.name} role="option" aria-selected={isSelected} onMouseDown={e=>{e.preventDefault();setGroupOverrides(o=>({...o,[l.name]:g.name}));setGroupPickerOpen(false);}} onMouseEnter={()=>setGroupActiveIdx(gi)} style={{display:'flex',alignItems:'center',justifyContent:'space-between',height:36,padding:'0 10px',borderRadius:'var(--radius-sm)',fontSize:12.5,fontWeight:600,color:isSelected?'var(--text-primary)':'var(--text-secondary)',background:isSelected?'var(--color-mist)':isActive?'rgba(11,12,14,0.04)':'transparent',cursor:'pointer'}}>
<span>{g.name}</span>
{isSelected&&<img src="https://unpkg.com/lucide-static@latest/icons/check.svg" style={{width:13,height:13,opacity:0.6}} />}
</div>);
})}
</div>}
</div>
</div>
<IconButton label="Close" onClick={()=>setSelected(null)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} />
</div>
<div style={{flex:1,overflow:'auto',padding:'20px 28px',display:'flex',flexDirection:'column',gap:20}}>
<Switch label="Suggest pricing" checked={pd.enabled} onChange={v=>setPropField(l.name,'enabled',v)} />
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Base price</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'flex',gap:0,background:'var(--surface-sunken)',borderRadius:'var(--radius-md)',padding:3}}>
{[{label:'Market median',value:'median'},{label:'Manual',value:'manual'}].map(o=>(
<div key={o.value} onClick={()=>setPropField(l.name,'method',o.value)} style={{flex:1,textAlign:'center',padding:'7px 0',borderRadius:'var(--radius-sm)',fontSize:12.5,fontWeight:600,cursor:'pointer',background:pd.method===o.value?'var(--color-white)':'transparent',color:pd.method===o.value?'var(--text-primary)':'var(--text-secondary)',boxShadow:pd.method===o.value?'var(--shadow-sm)':'none',transition:'background var(--duration-fast) var(--ease-standard)'}}>{o.label}</div>
))}
</div>
{pd.method==='manual'&&<Input label="Manual base price" placeholder="Example: 4,500,000" value={pd.manualBase} onChange={e=>setPropField(l.name,'manualBase',e.target.value)} />}
{pd.method==='median'&&<React.Fragment>
<div>
<div style={{display:'flex',alignItems:'center',gap:6,marginBottom:6,position:'relative'}}>
<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Market positioning factor</span>
<img src={`https://unpkg.com/lucide-static@latest/icons/${posInfoOpen?'x':'info'}.svg`} onClick={()=>setPosInfoOpen(o=>!o)} style={{width:13,height:13,opacity:0.45,cursor:'pointer'}} />
{posInfoOpen&&<div style={{position:'absolute',top:'calc(100% + 8px)',left:0,zIndex:10,width:260,background:'var(--color-white)',color:'var(--text-secondary)',border:'1px solid var(--border-default)',fontSize:12,lineHeight:1.5,padding:'10px 12px',borderRadius:'var(--radius-md)',boxShadow:'var(--shadow-lg)'}}>Positioning of this property's price relative to the market median.<br/>Example:<br/>1.1 = 10% above market<br/>0.9 = 10% below market</div>}
</div>
<Input value={pd.positioning} onChange={e=>setPropField(l.name,'positioning',e.target.value)} />
</div>
<InputWithSelectField label="Minimum competitor count" value={pd.minComp} onChange={v=>setPropField(l.name,'minComp',v)} options={[{label:'Global: '+globalSettings.minComp,value:'',linked:true}]} />
</React.Fragment>}
</div>
</div>
<div>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:14}}>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)'}}>Discounts by days left until stay</div>
<Switch checked={pd.useUrgency!=='off'} onChange={v=>setPropField(l.name,'useUrgency',v?'on':'off')} />
</div>
{pd.useUrgency!=='off'&&<UrgencyRulesEditor rules={pd.rules} setRules={u=>setPropRules(l.name,u)} />}
</div>
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Bounds and rounding</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
<InputWithSelectField label="Minimum price" value={pd.minIDR} onChange={v=>setPropField(l.name,'minIDR',v)} options={[{label:'Global: '+globalSettings.minIDR,value:'',linked:true}]} />
<InputWithSelectField label="Maximum price" value={pd.maxIDR} onChange={v=>setPropField(l.name,'maxIDR',v)} options={[{label:'Global: '+globalSettings.maxIDR,value:'',linked:true}]} />
</div>
<InputWithSelectField label="Round to nearest" value={pd.step} onChange={v=>setPropField(l.name,'step',v)} options={[{label:'Global: '+globalSettings.step,value:'',linked:true}]} />
</div>
</div>
</div>
<div style={{padding:'16px 28px',borderTop:'1px solid var(--border-default)',display:'flex',gap:10}}>
<Button variant="accent" size="sm" style={{width:'100%'}} onClick={()=>saveProperty(l.name)}>Save</Button>
</div>
</React.Fragment>}
</div>);
})(), document.body)}
</div>
</div>);
}
export default Pricing;
