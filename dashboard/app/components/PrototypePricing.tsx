// @ts-nocheck
"use client";
// This file is the host-dashboard prototype with a data/API adapter at its edges.
import React from "react";
import ReactDOM from "react-dom";
import { Input, IconButton, Select, Button, Toast, Switch, InputWithSelectField } from "./design-system";
import { CalendarLoadingSkeleton } from "./CalendarLoadingSkeleton";
const csrfToken=()=>decodeURIComponent(document.cookie.split('; ').find(row=>row.startsWith('pricing_csrf='))?.split('=')[1]||'');
// These implementations mirror the corresponding design-system sources in
// nicer.homes_design_system/components. They are kept local because the
// design-system bundle is browser-global in the original prototype.
function UrgencyRulesEditor({rules,setRules,loading=false}){
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
{loading?[0,1,2,3].map(i=><div key={`chart-loading-${i}`} className="urgency-chart-value-skeleton" style={{width:`${[13,13,22,52][i]}%`,height:[72,54,34,12][i]}}/>):display.map((r,i)=>(
<div key={i} onMouseEnter={()=>setHover(i)} onMouseLeave={()=>setHover(h=>h===i?null:h)} style={{width:`${((r.t-r.f+1)/max)*100}%`,height:`${r.gap?4:Math.max(6,(Math.abs(parseFloat(r.d))||0)/maxAbsD*100)}%`,background:colorFor(r),position:'relative',marginRight:i<display.length-1?2:0,borderRadius:4,cursor:'default'}}>
{hover===i&&<div style={{position:'absolute',bottom:'calc(100% + 8px)',left:'50%',transform:'translateX(-50%)',background:'var(--color-ink-900)',color:'var(--color-white)',fontSize:11,fontWeight:600,padding:'6px 10px',borderRadius:'var(--radius-sm)',whiteSpace:'nowrap',zIndex:5,boxShadow:'var(--shadow-md)'}}>Day {r.f}–{r.t}: {pct(r)}</div>}
</div>
))}
</div>
<div style={{display:'flex',justifyContent:'space-between',fontSize:10.5,color:'var(--text-muted)',marginBottom:22}}><span>Day 0</span><span>Day {max-1}</span></div>
<div style={{display:'flex',flexDirection:'column',gap:6}}>
{loading&&[0,1,2,3].map(i=><div key={`loading-${i}`} className="urgency-rule-value-skeleton"><span className="field-value-skeleton"/></div>)}
{!loading&&display.map((r,i)=>r.gap?(
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
function monthLabel(d){return d.toLocaleDateString('en-US',{month:'long',year:'numeric',timeZone:'UTC'});}
function normalizeUrgencyRules(value){
  if(Array.isArray(value)) return value.filter(rule=>rule&&typeof rule==='object');
  if(value&&typeof value==='object'){
    if(Array.isArray(value.rules)) return normalizeUrgencyRules(value.rules);
    return Object.values(value).filter(rule=>rule&&typeof rule==='object');
  }
  return [];
}
function effectiveSetting(value){
  return value&&typeof value==='object'&&Object.prototype.hasOwnProperty.call(value,'value')?value.value:value;
}
function calendarDate(value){return new Date(`${value}T00:00:00Z`);}
function dateString(value){return value.toISOString().slice(0,10);}
function shiftDate(value,days){const next=new Date(value);next.setUTCDate(next.getUTCDate()+days);return next;}
function Pricing(){
const [days,setDays]=React.useState([]);
const [listings,setListings]=React.useState([]);
const [calendarLoading,setCalendarLoading]=React.useState(true);
const [calendarRecords,setCalendarRecords]=React.useState({});
const [globalSettings,setGlobalSettings]=React.useState({minComp:'10',positioning:'1',guestToHost:'0.839',minIDR:'1',maxIDR:'999999999',step:'50000',useUrgency:'on',method:'median',manualBase:'',rules:[{f:0,t:3,d:-0.15},{f:4,t:7,d:-0.10},{f:8,t:14,d:-0.05},{f:15,t:30,d:-0.02}]});
const [pricingGroups,setPricingGroups]=React.useState([]);
const [searchQuery,setSearchQuery]=React.useState('');
const calendarRangeRef=React.useRef({start:null,end:null});
const loadingRangeRef=React.useRef(null);
const loadingDatesRef=React.useRef(new Set());
const pendingLeftCompensationRef=React.useRef(0);
const [loadingDates,setLoadingDates]=React.useState([]);
const loadCalendarRange=React.useCallback((startValue,endValue)=>{const start=dateString(startValue);const end=dateString(endValue);const requestKey=`${start}:${end}`;if(loadingRangeRef.current===requestKey)return Promise.resolve();loadingRangeRef.current=requestKey;return fetch('/api/pricing-calendar?start='+start+'&end='+end).then(r=>r.ok?r.json():null).then(payload=>{if(!payload?.properties)return;calendarRangeRef.current={start:calendarRangeRef.current.start&&calendarRangeRef.current.start<start?calendarRangeRef.current.start:start,end:calendarRangeRef.current.end&&calendarRangeRef.current.end>end?calendarRangeRef.current.end:end};setCalendarRecords(previous=>{const merged={...previous};(payload.days||[]).forEach(record=>{merged[`${record.property_id}:${record.stay_date}`]=record;});const records=Object.values(merged);const dates=[...new Set(records.map(record=>record.stay_date))].sort();setDays(dates.map(calendarDate));setListings(payload.properties.map((property,index)=>{const propertyRecords=records.filter(record=>String(record.property_id)===String(property.id));const first=propertyRecords.find(record=>record.current_price!=null);return {id:property.id,name:property.name,thumbnailUrl:property.thumbnail_url||'',c:['var(--color-accent-300)','var(--color-mist)','var(--color-ink-200)'][index%3],base:Number(first?.current_price||0),groupId:property.pricing_group_id,group:property.pricing_group_name||('Pricing group '+property.pricing_group_id),prices:Object.fromEntries(propertyRecords.map(record=>[record.stay_date,Number(record.current_price||0)]))};}));return merged;});}).finally(()=>{loadingRangeRef.current=null;});},[]);
const initialLoad=React.useCallback(()=>loadCalendarRange(shiftDate(new Date(),-7),shiftDate(new Date(),43)),[loadCalendarRange]);
React.useEffect(()=>{let active=true;Promise.all([initialLoad(),fetch('/api/settings/pricing',{cache:'no-store'}).then(r=>r.ok?r.json():null),fetch('/api/pricing-groups',{cache:'no-store'}).then(r=>r.ok?r.json():[])]).then(([,settings,groups])=>{if(active&&settings){setGlobalSettings({minComp:String(settings.minimum_competitor_count),positioning:String(settings.market_positioning_factor),guestToHost:String(settings.guest_to_host_price_factor),minIDR:String(settings.minimum_price??1),maxIDR:String(settings.maximum_price??999999999),step:String(settings.rounding_increment??50000),useUrgency:settings.urgency_adjustment_enabled?'on':'off',method:settings.base_price_mode==='manual'?'manual':'median',manualBase:settings.manual_base_price?String(settings.manual_base_price):'',rules:normalizeUrgencyRules(settings.urgency_adjustments).map(r=>({f:r.minimum_days,t:r.maximum_days,d:r.adjustment}))});}if(active){setPricingGroups(groups||[]);setGroupData(Object.fromEntries((groups||[]).map(g=>[g.name,{name:g.name,minComp:g.pricing_settings?.minimum_competitor_count?String(g.pricing_settings.minimum_competitor_count):'',urls:(g.competitor_urls||[]).join('\n')}])));}}).catch(()=>{}).finally(()=>{if(active)setCalendarLoading(false);});return()=>{active=false;};},[initialLoad]);
const visibleListings=listings.filter(l=>l.name.toLowerCase().includes(searchQuery.trim().toLowerCase())).map(l=>({...l,group:pricingGroups.find(g=>String(g.id)===String(l.groupId))?.name||l.group}));
const groupOrder=[];visibleListings.forEach(l=>{if(!groupOrder.includes(l.group))groupOrder.push(l.group);});
let rowCursor=3;let propCursor=0;
const groups=groupOrder.map(gname=>{
const items=visibleListings.filter(l=>l.group===gname);
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
const [scrapeOpen,setScrapeOpen]=React.useState(false);
const [competitors,setCompetitors]=React.useState([]);
const [scrapeForm,setScrapeForm]=React.useState({listingId:'',start:new Date().toISOString().slice(0,10),end:new Date(Date.now()+6*86400000).toISOString().slice(0,10),force:false});
const [globalOpen,setGlobalOpen]=React.useState(false);
const setGlobalField=(field,val)=>setGlobalSettings(s=>({...s,[field]:val}));
const saveGlobal=()=>{if(!globalSettings)return;const min=Number(String(globalSettings.minIDR||'').replace(/,/g,''));const max=Number(String(globalSettings.maxIDR||'').replace(/,/g,''));const step=Number(String(globalSettings.step||'').replace(/,/g,''));if(!min||!max||min>max||!step){setToast('Check minimum, maximum, and rounding values.');setTimeout(()=>setToast(null),2600);return;}fetch('/api/settings/pricing',{method:'PUT',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify({base_price_mode:globalSettings.method==='median'?'market_median':'manual',manual_base_price:globalSettings.manualBase?Number(String(globalSettings.manualBase).replace(/,/g,'')):null,guest_to_host_price_factor:Number(globalSettings.guestToHost),market_positioning_factor:Number(globalSettings.positioning),minimum_competitor_count:Number(globalSettings.minComp),minimum_price:min,maximum_price:max,rounding_increment:step,urgency_adjustment_enabled:globalSettings.useUrgency!=='off',urgency_adjustments:globalSettings.rules.map(r=>({minimum_days:r.f,maximum_days:r.t,adjustment:Number(r.d)}))})}).then(async r=>{if(!r.ok)throw new Error((await r.json()).detail||'Could not save global settings');setToast('Global settings saved.');setGlobalOpen(false);}).catch(e=>setToast(e.message));};
const [tooltipData,setTooltipData]=React.useState(null);
const [priceOverrides,setPriceOverrides]=React.useState({});
const [rangePriceInput,setRangePriceInput]=React.useState('');
const [rangeSuggestPrices,setRangeSuggestPrices]=React.useState(true);
const [assignmentEditor,setAssignmentEditor]=React.useState(null);
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
React.useEffect(()=>{fetch('/api/competitors',{cache:'no-store'}).then(r=>r.ok?r.json():[]).then(rows=>{setCompetitors(rows||[]);if(rows?.length)setScrapeForm(f=>({...f,listingId:f.listingId||String(rows[0].id)}));}).catch(()=>{});},[]);
const [posInfoOpen,setPosInfoOpen]=React.useState(false);
const activeProperty=selected&&!selected.startsWith('group:')?listings.find(l=>l.name===selected):null;
const [propertySettingsLoading,setPropertySettingsLoading]=React.useState(false);
const propFor=(name)=>propertyData[name]||{enabled:true,method:'median',manualBase:'',positioning:'1',minComp:'',useUrgency:'global',urgencyOpen:false,rules:[{f:0,t:3,d:-0.3},{f:4,t:7,d:-0.2},{f:8,t:14,d:-0.1},{f:15,t:30,d:-0.05}],minIDR:'',maxIDR:'',step:''};
React.useEffect(()=>{if(!activeProperty?.id){setPropertySettingsLoading(false);return;}setPropertySettingsLoading(true);fetch('/api/settings/pricing/effective/'+activeProperty.id).then(r=>r.ok?r.json():null).then(data=>{if(!data)return;const v=Object.fromEntries(Object.entries(data).map(([key,value])=>[key,effectiveSetting(value)]));setPropertyData(d=>({...d,[activeProperty.name]:{...propFor(activeProperty.name),enabled:v.suggest_prices!==false,method:v.base_price_mode==='manual'?'manual':'median',manualBase:v.manual_base_price?String(v.manual_base_price):'',positioning:String(v.market_positioning_factor),minComp:String(v.minimum_competitor_count),useUrgency:v.urgency_adjustment_enabled?'on':'off',rules:normalizeUrgencyRules(v.urgency_adjustments).map(r=>({f:r.minimum_days,t:r.maximum_days,d:r.adjustment})),minIDR:String((v.minimum_price??activeProperty.min_price)||''),maxIDR:String((v.maximum_price??activeProperty.max_price)||''),step:String((v.rounding_increment??activeProperty.rounding_increment)||'')}}));}).catch(()=>{}).finally(()=>setPropertySettingsLoading(false));},[activeProperty?.id]);
const setPropField=(name,field,val)=>setPropertyData(d=>({...d,[name]:{...propFor(name),[field]:val}}));
const setPropRules=(name,updater)=>setPropertyData(d=>{const cur=propFor(name);const rules=typeof updater==='function'?updater(cur.rules):updater;return {...d,[name]:{...cur,rules}};});
const saveProperty=(name)=>{
 const pd=propFor(name); const item=listings.find(l=>l.name===name); const min=Number(String(pd.minIDR).replace(/,/g,'')); const max=Number(String(pd.maxIDR).replace(/,/g,''));
 if(pd.minIDR&&pd.maxIDR&&min>max){setToast('Minimum price cannot exceed maximum price.');return;}
 const selectedGroup=pricingGroups.find(g=>g.name===(groupOverrides[name]||item.group));
 const payload={pricing_group_id:selectedGroup?.id||item.groupId,min_price:min,max_price:max,rounding_increment:Number(String(pd.step||'').replace(/,/g,'')),pricing_settings:{suggest_prices:pd.enabled,base_price_mode:pd.method==='median'?'market_median':'manual',manual_base_price:pd.manualBase?Number(String(pd.manualBase).replace(/,/g,'')):null,market_positioning_factor:Number(pd.positioning),minimum_competitor_count:Number(pd.minComp),urgency_adjustment_enabled:pd.useUrgency==='on',urgency_adjustments:pd.rules.map(r=>({minimum_days:r.f,maximum_days:r.t,adjustment:Number(r.d)}))}};
 fetch('/api/properties/'+item.id,{method:'PATCH',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify(payload)}).then(async r=>{if(!r.ok)throw new Error((await r.json()).detail||'Could not save property');setToast('Property settings saved.');setSelected(null);return initialLoad();}).catch(e=>setToast(e.message));
};
const [groupData,setGroupData]=React.useState({});
const defaultGroupUrls=(gname)=>Array.from({length:9},(_,i)=>`https://www.airbnb.com/rooms/${1500000000000+Math.abs(Math.round(Math.sin(gname.length+i*3.1)*99999999999))}`).join('\n');
const activeGroupName=selected&&selected.startsWith('group:')?selected.slice(6):null;
const groupFor=(gname)=>groupData[gname]||{name:gname,minComp:'',urls:''};
const setGroupField=(gname,field,val)=>setGroupData(d=>({...d,[gname]:{...groupFor(gname),[field]:val}}));
const saveGroup=async(gname)=>{
  const localGroup=pricingGroups.find(g=>g.name===gname);
  const mappedProperty=listings.find(item=>item.group===gname);
  const groupId=localGroup?.id||mappedProperty?.groupId;
  if(!groupId){setToast('Could not identify pricing group.');return;}
  try{
    const currentGroup=localGroup||await fetch('/api/pricing-groups').then(async response=>response.ok?response.json():[]).then(items=>items.find(item=>item.id===groupId||item.name===gname));
    if(!currentGroup){setToast('Could not load pricing group.');return;}
    const hasLocalData=Object.prototype.hasOwnProperty.call(groupData,gname);
    const gd=groupFor(gname);
    const urls=hasLocalData?gd.urls.split('\n').map(u=>u.trim()).filter(Boolean):(currentGroup.competitor_urls||[]);
    const response=await fetch('/api/pricing-groups/'+groupId,{method:'PATCH',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify({name:gd.name.trim()||gname,competitor_urls:urls,pricing_settings:gd.minComp?{minimum_competitor_count:Number(gd.minComp)}:{}})});
    if(!response.ok)throw new Error((await response.json()).detail||'Could not save pricing group');
    setToast('Pricing group saved.');setSelected(null);
    const groups=await fetch('/api/pricing-groups',{cache:'no-store'}).then(x=>x.json());setPricingGroups(groups);return initialLoad();
  }catch(error){setToast(error.message);}
};
const scrollRef=React.useRef(null);
// Keep the navigation affordances visible during the first layout pass. The
// scroll measurement updates their enabled state after the calendar mounts,
// without making the controls appear/disappear during data hydration.
const [canLeft,setCanLeft]=React.useState(true);
const [canRight,setCanRight]=React.useState(true);
const suppressInitialLeftPrefetch=React.useRef(false);
const [currentMonth,setCurrentMonth]=React.useState(0);
const colWidth=96;
const labelColWidth=280;
const months=[];
days.forEach((d,i)=>{if(i===0||d.getUTCDate()===1)months.push({label:monthLabel(d),start:i});});
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
const loadMoreDates=(direction)=>{
  const el=scrollRef.current;
  if(!el||loadingRangeRef.current||!calendarRangeRef.current.start||!calendarRangeRef.current.end)return;
  const start=calendarDate(calendarRangeRef.current.start);
  const end=calendarDate(calendarRangeRef.current.end);
  const rangeStart=direction==='right'?shiftDate(end,1):shiftDate(start,-30);
  const rangeEnd=direction==='right'?shiftDate(end,30):shiftDate(start,-1);
  const requestedDates=Array.from({length:31},(_,index)=>dateString(shiftDate(rangeStart,index))).filter(value=>value<=dateString(rangeEnd));
  loadingDatesRef.current=new Set([...loadingDatesRef.current,...requestedDates]);
  setLoadingDates(Array.from(loadingDatesRef.current));
  if(direction==='left')pendingLeftCompensationRef.current+=requestedDates.length*colWidth;
  setDays(previous=>[...new Set([...previous.map(dateString),...requestedDates])].sort().map(calendarDate));
  const request=loadCalendarRange(rangeStart,rangeEnd);
  request.finally(()=>{requestedDates.forEach(value=>loadingDatesRef.current.delete(value));setLoadingDates(Array.from(loadingDatesRef.current));});
};
const updateScrollState=()=>{
const el=scrollRef.current;if(!el)return;
updateHoverFromPointer(lastPointer.current.x,lastPointer.current.y);
setCanLeft(el.scrollLeft>4);
setCanRight(el.scrollLeft<el.scrollWidth-el.clientWidth-4);
 const prefetchThreshold=colWidth*3;
 if(el.scrollLeft<prefetchThreshold&&!suppressInitialLeftPrefetch.current)loadMoreDates('left');
 if(el.scrollLeft>el.scrollWidth-el.clientWidth-prefetchThreshold)loadMoreDates('right');
const visibleCol=Math.round((el.scrollLeft)/colWidth);
let mi=0;
months.forEach((m,idx)=>{if(visibleCol>=m.start)mi=idx;});
setCurrentMonth(mi);
};
React.useEffect(()=>{updateScrollState();},[]);
React.useLayoutEffect(()=>{
  if(!pendingLeftCompensationRef.current||!scrollRef.current)return;
  scrollRef.current.scrollLeft+=pendingLeftCompensationRef.current;
  pendingLeftCompensationRef.current=0;
},[days.length]);
const scrollBy=(dir)=>{const el=scrollRef.current;if(!el)return;el.scrollBy({left:dir*colWidth*4,behavior:'smooth'});setTimeout(updateScrollState,300)};
const scrollToCol=(colIdx)=>{const el=scrollRef.current;if(!el)return;el.scrollTo({left:colIdx*colWidth,behavior:'smooth'});setTimeout(updateScrollState,350)};
const alignToday=(behavior='smooth')=>{
const el=scrollRef.current;if(!el)return false;
const todayHeader=el.querySelector(`[data-calendar-date="${dateString(new Date())}"]`);if(!todayHeader)return false;
const containerRect=el.getBoundingClientRect();
const headerRect=todayHeader.getBoundingClientRect();
const targetLeft=Math.max(0,el.scrollLeft+headerRect.left-(containerRect.left+labelColWidth));
el.scrollTo({left:targetLeft,behavior});
return true;
};
const scrollToToday=()=>{
if(!alignToday('smooth'))return;
setTimeout(updateScrollState,350);
};
const initialTodayScrollDone=React.useRef(false);
React.useEffect(()=>{
if(calendarLoading||!days.length||initialTodayScrollDone.current)return;
initialTodayScrollDone.current=true;
suppressInitialLeftPrefetch.current=true;
requestAnimationFrame(()=>{
if(!alignToday('auto'))return;
updateScrollState();
setTimeout(()=>{suppressInitialLeftPrefetch.current=false;},600);
});
},[calendarLoading,days.length]);
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
if(key==='comp'){setScrapeOpen(true);return;}
setBusy(key);
const paths={fetch:'/api/imports/hostex/booking-site',generate:'/api/pricing/run',apply:'/api/pricing/publish'};
const path=paths[key];
if(!path){setTimeout(()=>{setBusy(null);setToast(label);},500);return;}
fetch(path,{method:'POST',headers:{'X-CSRF-Token':csrfToken()}}).then(async response=>{const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.detail||label+' failed');setBusy(null);setToast(label);if(key==='fetch')setLastSync(s=>({...s,fetch:'Just now'}));if(key==='generate')setLastSync(s=>({...s,generate:'Just now'}));if(key==='apply')setLastSync(s=>({...s,apply:'Just now'}));return initialLoad();}).then(()=>setTimeout(()=>setToast(null),2600)).catch(error=>{setBusy(null);setToast(error.message);});
};
const launchScrape=()=>{const start=new Date(scrapeForm.start),end=new Date(scrapeForm.end);if(!scrapeForm.listingId||Number.isNaN(start.valueOf())||Number.isNaN(end.valueOf())||end<start){setToast('Choose a listing and a valid date range.');return;}setBusy('comp');fetch('/api/competitor-scrapes',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify({competitor_listing_id:Number(scrapeForm.listingId),start_date:scrapeForm.start,end_date:scrapeForm.end,force_refresh:scrapeForm.force})}).then(async r=>{const body=await r.json().catch(()=>({}));if(!r.ok)throw new Error(body.detail||'Competitor scrape failed');setScrapeOpen(false);setToast(`Scrape run ${body.run_id} started.`);}).catch(e=>setToast(e.message)).finally(()=>setBusy(null));};
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
const saveAssignmentEdit=async()=>{if(!assignmentEditor)return;const price=Number(String(assignmentEditor.price).replace(/[^0-9]/g,''));if(!price||price<=0){setToast('Enter a price greater than zero.');return;}const response=await fetch(`/api/price-assignments/${assignmentEditor.id}`,{method:'PATCH',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify({property_id:assignmentEditor.propertyId,start_date:assignmentEditor.date,end_date:assignmentEditor.date,price,suggest_prices:assignmentEditor.suggestPrices,reason:assignmentEditor.reason||'Calendar price assignment'})});const body=await response.json().catch(()=>({}));if(!response.ok){setToast(body.detail||'Could not update assignment.');return;}setAssignmentEditor(null);setToast('Assignment updated.');initialLoad();};
const deleteAssignment=async()=>{if(!assignmentEditor)return;const response=await fetch(`/api/price-assignments/${assignmentEditor.id}`,{method:'DELETE',headers:{'X-CSRF-Token':csrfToken()}});if(!response.ok){setToast('Could not delete assignment.');return;}setAssignmentEditor(null);setToast('Assignment removed.');initialLoad();};
const saveRangePrice=()=>{
const val=Number(String(rangePriceInput).replace(/[^0-9]/g,''));
if(!val||!rangeSelection)return;
const selectedListings=[];
listings.forEach(l=>{
if(l.propIndex<rangeSelection.minProp||l.propIndex>rangeSelection.maxProp)return;
selectedListings.push(l);
});
const nDates=(rangeSelection.maxDay-rangeSelection.minDay+1)*(rangeSelection.maxProp-rangeSelection.minProp+1);
const start=days[rangeSelection.minDay].toISOString().slice(0,10); const end=days[rangeSelection.maxDay].toISOString().slice(0,10);
const availableDates=selectedListings.flatMap(l=>days.slice(rangeSelection.minDay,rangeSelection.maxDay+1).filter(d=>{const record=calendarRecords[`${l.id}:${dateString(d)}`];return record?.available!==false;}).map(d=>({property_id:l.id,date:dateString(d)})));
if(!availableDates.length){setToast('No available dates in the selected range.');return;}
Promise.all(selectedListings.map(l=>fetch('/api/price-assignments',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrfToken()},body:JSON.stringify({property_id:l.id,start_date:start,end_date:end,price:val,suggest_prices:rangeSuggestPrices,reason:rangeSuggestPrices?'Calendar manual base price':'Calendar fixed price'})}))).then(async responses=>{const failed=responses.find(r=>!r.ok);if(failed)throw new Error((await failed.json()).detail||'Could not save calendar change');setToast(`${rangeSuggestPrices?'Suggested':'Fixed'} price saved for ${availableDates.length} available date${availableDates.length===1?'':'s'}.`);clearRange();return initialLoad();}).catch(e=>setToast(e.message));
};
const dateLabel=d=>d.toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'});
const loadingDateSet=new Set(loadingDates);
const cols=`${labelColWidth}px repeat(${days.length},${colWidth}px)`;
return (
<div style={{flex:1,display:'flex',flexDirection:'column',minWidth:0,background:'var(--color-white)',position:'relative',zIndex:1}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',rowGap:12,padding:'20px 24px',borderBottom:'1px solid var(--border-default)'}}>
<div style={{display:'flex',alignItems:'center',gap:12}}>
<div style={{width:172,position:'relative',flexShrink:0}}>
<Select value={months.length?String(currentMonth):'loading'} pill onChange={e=>{const month=months[Number(e.target.value)];if(month)scrollToCol(month.start);}} options={months.length?months.map((m,idx)=>({label:m.label,value:String(idx)})):[{label:' ',value:'loading'}]} />
{!months.length&&<span className="calendar-skeleton calendar-skeleton-toolbar-month calendar-runtime-month-skeleton" aria-hidden="true" />}
</div>
<Button variant="secondary" size="sm" onClick={scrollToToday}>Today</Button>
</div>
<div style={{display:'flex',alignItems:'center',gap:8}}>
<Button variant="secondary" size="sm" onClick={()=>setGlobalOpen(true)}>Global settings</Button>
<Button variant="secondary" size="sm" onClick={()=>setActionsOpen(true)}>Actions</Button>
</div>
</div>
{toast&&<div style={{position:'absolute',top:20,right:24,zIndex:20}}><Toast tone="success" onClose={()=>setToast(null)}>{toast}</Toast></div>}
<div style={{flex:1,position:'relative',minHeight:0,minWidth:0}}>
{calendarLoading&&<CalendarLoadingSkeleton bodyOnly />}
<div ref={scrollRef} onScroll={updateScrollState} onMouseMove={e=>{lastPointer.current={x:e.clientX,y:e.clientY};updateHoverFromPointer(e.clientX,e.clientY);}} onMouseLeave={()=>{setHoverCellKey(null);setTooltipData(null);}} style={{height:'100%',overflow:'auto'}}>
<div style={{display:'grid',gridTemplateColumns:cols,minWidth:'fit-content'}}>
<div style={{gridColumn:'1',gridRow:1,position:'sticky',left:0,top:0,zIndex:4,background:'var(--color-white)',padding:'20px 20px 12px',height:48,boxSizing:'border-box',display:'flex',alignItems:'center'}}>
<h3 style={{fontFamily:'var(--font-display)',fontSize:'var(--text-lg)',fontWeight:600,margin:0}}>{listings.length} Properties</h3>
</div>
{months.map((m,idx)=>(
<div key={m.label} style={{gridColumn:`${m.start+2} / ${idx+1<months.length?months[idx+1].start+2:days.length+2}`,gridRow:1,position:'sticky',top:0,height:48,boxSizing:'border-box',zIndex:2,background:'var(--color-white)',padding:'14px 16px',fontFamily:'var(--font-display)',fontWeight:600,fontSize:15,width:'fit-content',maxWidth:'100%',whiteSpace:'nowrap'}}>{m.label}</div>
))}
<div style={{gridColumn:'1',gridRow:2,position:'sticky',left:0,top:48,zIndex:4,background:'var(--color-white)',borderBottom:'1px solid var(--border-default)',padding:'0 20px 12px'}}>
<Input placeholder="Search listings..." value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} />
</div>
{days.map((d,i)=>(
<div key={i} data-calendar-date={dateString(d)} aria-busy={loadingDateSet.has(dateString(d))} style={{gridColumn:i+2,gridRow:2,position:'sticky',top:48,zIndex:2,background:'var(--color-white)',textAlign:'center',padding:'10px 4px',fontSize:12,color:'var(--text-secondary)',borderTop:'1px solid var(--border-default)',borderBottom:'1px solid var(--border-default)'}}>
{loadingDateSet.has(dateString(d))?<div className="calendar-skeleton-date" aria-label="Loading date"><span className="calendar-skeleton calendar-skeleton-weekday" /><span className="calendar-skeleton calendar-skeleton-day" /></div>:<><div>{d.toLocaleDateString('en-US',{weekday:'narrow',timeZone:'UTC'})}</div>
<div style={{fontWeight:600,color:'var(--text-primary)',marginTop:2}}>{d.getUTCDate()}</div></>}
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
<div style={{width:44,height:44,borderRadius:'var(--radius-md)',background:l.c,flexShrink:0,overflow:'hidden'}}>{l.thumbnailUrl&&<img src={l.thumbnailUrl} alt="" loading="lazy" style={{width:'100%',height:'100%',objectFit:'cover',display:'block'}} />}</div>
<div>
<div style={{fontWeight:600,fontSize:14,color:'var(--text-primary)'}}>{l.name}</div>
<div style={{fontSize:12,color:'var(--text-secondary)'}}>IDR (Rp)</div>
</div>
</div>
{days.map((d,i)=>{
const isLoadingDate=loadingDateSet.has(dateString(d));
const record=calendarRecords[`${l.id}:${days[i]?.toISOString().slice(0,10)}`];
const cur=priceOverrides[l.name+'-'+i]??(record?.current_price??l.prices?.[days[i]?.toISOString().slice(0,10)]??price(l.base,i));
const hasCurrentPrice=record?.current_price!=null||l.prices?.[days[i]?.toISOString().slice(0,10)]!=null;
const isAvailable=record?.available===true;
const rec=record?.recommended_price??cur;
const explanation=record?.explanation;
const breakdown=explanation&&Object.keys(explanation).length?{source:explanation.price_source||explanation.anchor_source,guestMedian:explanation.airbnb_guest_market_median,availableComp:explanation.available_competitor_count,requiredComp:explanation.minimum_competitor_count,guestToHostFactor:explanation.guest_to_host_price_factor,hostMedian:explanation.estimated_host_price_median,positioningFactor:explanation.market_positioning_factor,basePrice:explanation.base_price,daysUntilStay:explanation.days_until_stay,urgencyPct:explanation.urgency_adjustment!=null?explanation.urgency_adjustment*100:null,raw:explanation.raw_price,rounded:explanation.rounded_price,final:explanation.final_price||record.recommended_price,dateOverride:explanation.price_source==='manual_override'}:null;
const diff=rec-cur;
const cellKey=l.name+'-'+i;
const isHover=hoverCellKey===cellKey;
const inRange=rangeSelection&&l.propIndex>=rangeSelection.minProp&&l.propIndex<=rangeSelection.maxProp&&i>=rangeSelection.minDay&&i<=rangeSelection.maxDay;
const isAnchor=rangeAnchor&&rangeAnchor.propIndex===l.propIndex&&rangeAnchor.dayIndex===i;
const edgeTop=(isAnchor||inRange)&&l.propIndex===(rangeSelection?rangeSelection.minProp:l.propIndex);
const edgeBottom=(isAnchor||inRange)&&l.propIndex===(rangeSelection?rangeSelection.maxProp:l.propIndex);
const edgeLeft=(isAnchor||inRange)&&i===(rangeSelection?rangeSelection.minDay:i);
const edgeRight=(isAnchor||inRange)&&i===(rangeSelection?rangeSelection.maxDay:i);
const cellBg=isAnchor?'var(--action-accent-soft)':inRange?'var(--action-accent-soft)':isHover?'rgba(11,12,14,0.04)':selected===l.name?'var(--surface-sunken)':'var(--color-white)';
return (
<div key={i} onClick={()=>!isLoadingDate&&handleCellClick(l.propIndex,i)} onDoubleClick={()=>{if(record?.assignment)setAssignmentEditor({id:record.assignment.id,propertyId:l.id,date:dateString(d),price:String(record.assignment.price),suggestPrices:record.assignment.suggest_prices,reason:record.assignment.reason||''});}} data-cell-key={cellKey} data-diff={isLoadingDate?0:diff} data-cur={cur} data-breakdown={isLoadingDate?'':breakdown?JSON.stringify(breakdown):''} aria-busy={isLoadingDate} style={{gridColumn:i+2,gridRow:l.row,position:'relative',padding:'14px 8px',textAlign:'right',fontFamily:'var(--font-sans)',fontVariantNumeric:'tabular-nums',fontSize:12.5,color:'var(--text-primary)',background:isLoadingDate?'var(--surface-sunken)':cellBg,borderTop:edgeTop?'1.5px solid var(--color-accent-500)':'none',borderBottom:edgeBottom?'1.5px solid var(--color-accent-500)':'1px solid var(--border-default)',borderLeft:edgeLeft?'1.5px solid var(--color-accent-500)':(d.getUTCDate()===1?'1px solid var(--border-default)':'none'),borderRight:edgeRight?'1.5px solid var(--color-accent-500)':'none',cursor:isLoadingDate?'default':'pointer',transition:'background var(--duration-fast) var(--ease-standard)'}}>
{isLoadingDate?<div className="calendar-skeleton calendar-skeleton-price" aria-label="Loading price" />:!hasCurrentPrice?<div aria-label="No data">—</div>:!isAvailable?<div aria-label="Unavailable">—</div>:<><div>{cur.toLocaleString('en-US')}</div>{record?.assignment&&<div title={record.assignment.suggest_prices?'Suggested pricing assignment':'Fixed price assignment'} style={{width:6,height:6,borderRadius:'50%',background:record.assignment.suggest_prices?'var(--color-accent-500)':'var(--text-primary)',display:'inline-block',marginLeft:4}} />}
{diff!==0&&<div style={{marginTop:2,fontSize:11,fontWeight:600,color:diff>0?'var(--status-success)':'var(--status-danger)'}}>{rec.toLocaleString('en-US')}</div>}</>}
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
<div style={{position:'absolute',left:labelColWidth+8,top:76,transform:'translateY(-50%)',zIndex:6,opacity:canLeft?1:0,pointerEvents:canLeft?'auto':'none',transition:'opacity var(--duration-standard) var(--ease-standard)'}}><IconButton label="Scroll earlier" onClick={()=>scrollBy(-1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-left.svg" style={{width:16,height:16}} />} /></div>
<div style={{position:'absolute',right:8,top:76,transform:'translateY(-50%)',zIndex:6,opacity:canRight?1:0,pointerEvents:canRight?'auto':'none',transition:'opacity var(--duration-standard) var(--ease-standard)'}}><IconButton label="Scroll later" onClick={()=>scrollBy(1)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/chevron-right.svg" style={{width:16,height:16}} />} /></div>
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
<div onClick={()=>setScrapeOpen(false)} style={{position:'fixed',inset:0,background:'rgba(11,12,14,0.28)',backdropFilter:'blur(2px)',opacity:scrapeOpen?1:0,pointerEvents:scrapeOpen?'auto':'none',zIndex:209}}>
<div onClick={e=>e.stopPropagation()} style={{position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',width:420,maxWidth:'calc(100vw - 32px)',background:'var(--color-white)',borderRadius:'var(--radius-lg)',boxShadow:'var(--shadow-lg)',padding:24}}>
<div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:18}}><h3 style={{margin:0,fontFamily:'var(--font-display)'}}>Refresh competitor data</h3><IconButton label="Close" onClick={()=>setScrapeOpen(false)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} /></div>
<div style={{display:'flex',flexDirection:'column',gap:14}}>
<Select label="Competitor listing" value={scrapeForm.listingId} onChange={e=>setScrapeForm(f=>({...f,listingId:e.target.value}))} options={competitors.length?competitors.map(c=>({label:`${c.external_listing_id||c.canonical_url} · ${c.pricing_group_name}`,value:String(c.id)})):[{label:'No competitor listings',value:''}]} />
<Input label="Start date" type="date" value={scrapeForm.start} onChange={e=>setScrapeForm(f=>({...f,start:e.target.value}))} />
<Input label="End date" type="date" value={scrapeForm.end} onChange={e=>setScrapeForm(f=>({...f,end:e.target.value}))} />
<Switch label="Force refresh" checked={scrapeForm.force} onChange={v=>setScrapeForm(f=>({...f,force:v}))} />
<div style={{fontSize:12,color:'var(--text-muted)'}}>Fresh successful observations from the last 24 hours are skipped unless force refresh is enabled.</div>
<Button variant="accent" size="sm" onClick={launchScrape} disabled={busy==='comp'}>{busy==='comp'?'Starting…':'Start scrape'}</Button>
</div></div></div>, document.body)}
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
<Input label="Nightly price" prefix="Rp" numeric min={1} placeholder="e.g. 4,500,000" value={rangePriceInput} onChange={e=>setRangePriceInput(e.target.value)} />
<Switch label="Suggest pricing" checked={rangeSuggestPrices} onChange={setRangeSuggestPrices} />
<div style={{fontSize:11.5,color:'var(--text-muted)',marginTop:6}}>On keeps urgency, rounding and bounds. Off locks the entered price.</div>
<Button variant="accent" size="sm" style={{width:'100%',marginTop:16}} onClick={saveRangePrice} disabled={!rangePriceInput||Number(String(rangePriceInput).replace(/[^0-9]/g,''))<=0}>Save assignment</Button>
</div>, document.body)}
{ReactDOM.createPortal(
<div style={{position:'fixed',top:0,right:0,height:'100vh',width:360,background:'var(--color-white)',boxShadow:assignmentEditor?'var(--shadow-lg)':'none',borderLeft:'1px solid var(--border-default)',transform:`translateX(${assignmentEditor?'0':'100%'})`,transition:'transform var(--duration-standard) var(--ease-standard)',zIndex:204,display:'flex',flexDirection:'column',padding:24,boxSizing:'border-box'}}>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:24}}><div><h3 style={{fontFamily:'var(--font-display)',fontSize:'var(--text-lg)',margin:0}}>Edit price assignment</h3><div style={{fontSize:12,color:'var(--text-secondary)',marginTop:4}}>{assignmentEditor?.date}</div></div><IconButton label="Close" onClick={()=>setAssignmentEditor(null)} icon={<img src="https://unpkg.com/lucide-static@latest/icons/x.svg" style={{width:16,height:16}} />} /></div>
{assignmentEditor&&<div style={{display:'flex',flexDirection:'column',gap:16}}><Input label="Nightly price" prefix="Rp" numeric min={1} value={assignmentEditor.price} onChange={e=>setAssignmentEditor(a=>({...a,price:e.target.value}))} /><div style={{fontSize:12,color:'var(--text-secondary)'}}>Suggest prices</div><Select value={assignmentEditor.suggestPrices?'on':'off'} onChange={e=>setAssignmentEditor(a=>({...a,suggestPrices:e.target.value==='on'}))} options={[{label:'On · apply recommendations',value:'on'},{label:'Off · fixed price',value:'off'}]} /><Input label="Reason" value={assignmentEditor.reason} onChange={e=>setAssignmentEditor(a=>({...a,reason:e.target.value}))} /><Button variant="accent" size="sm" onClick={saveAssignmentEdit}>Save changes</Button><Button variant="secondary" size="sm" onClick={deleteAssignment}>Delete assignment</Button></div>}
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
<Input label="Guest-to-host factor" numeric min={0.01} max={1} value={globalSettings.guestToHost} onChange={e=>setGlobalField('guestToHost',e.target.value)} />
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
{globalSettings.method==='manual'&&<Input label="Manual base price" prefix="Rp" numeric min={1} placeholder="Example: 4,500,000" value={globalSettings.manualBase} onChange={e=>setGlobalField('manualBase',e.target.value)} />}
{globalSettings.method==='median'&&<React.Fragment>
<Input label="Market positioning factor" numeric min={0.1} max={3} value={globalSettings.positioning} onChange={e=>setGlobalField('positioning',e.target.value)} />
<Input label="Minimum competitor count" numeric integer min={1} max={30} value={globalSettings.minComp} onChange={e=>setGlobalField('minComp',e.target.value)} />
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
<Input label="Minimum price" prefix="Rp" numeric min={1} value={globalSettings.minIDR} onChange={e=>setGlobalField('minIDR',e.target.value)} />
<Input label="Maximum price" prefix="Rp" numeric min={1} value={globalSettings.maxIDR} onChange={e=>setGlobalField('maxIDR',e.target.value)} />
</div>
<Input label="Round to nearest" prefix="Rp" numeric min={1} value={globalSettings.step} onChange={e=>setGlobalField('step',e.target.value)} />
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
<Switch label="Suggest pricing" loading={propertySettingsLoading} checked={pd.enabled} onChange={v=>setPropField(l.name,'enabled',v)} />
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Base price</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'flex',gap:0,background:'var(--surface-sunken)',borderRadius:'var(--radius-md)',padding:3}}>
{[{label:'Market median',value:'median'},{label:'Manual',value:'manual'}].map(o=>(
<div key={o.value} onClick={()=>setPropField(l.name,'method',o.value)} style={{flex:1,textAlign:'center',padding:'7px 0',borderRadius:'var(--radius-sm)',fontSize:12.5,fontWeight:600,cursor:'pointer',background:pd.method===o.value?'var(--color-white)':'transparent',color:pd.method===o.value?'var(--text-primary)':'var(--text-secondary)',boxShadow:pd.method===o.value?'var(--shadow-sm)':'none',transition:'background var(--duration-fast) var(--ease-standard)'}}>{o.label}</div>
))}
</div>
{pd.method==='manual'&&<Input loading={propertySettingsLoading} label="Manual base price" prefix="Rp" numeric min={1} placeholder="Example: 4,500,000" value={pd.manualBase} onChange={e=>setPropField(l.name,'manualBase',e.target.value)} />}
{pd.method==='median'&&<React.Fragment>
<div>
<div style={{display:'flex',alignItems:'center',gap:6,marginBottom:6,position:'relative'}}>
<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>Market positioning factor</span>
<img src={`https://unpkg.com/lucide-static@latest/icons/${posInfoOpen?'x':'info'}.svg`} onClick={()=>setPosInfoOpen(o=>!o)} style={{width:13,height:13,opacity:0.45,cursor:'pointer'}} />
{posInfoOpen&&<div style={{position:'absolute',top:'calc(100% + 8px)',left:0,zIndex:10,width:260,background:'var(--color-white)',color:'var(--text-secondary)',border:'1px solid var(--border-default)',fontSize:12,lineHeight:1.5,padding:'10px 12px',borderRadius:'var(--radius-md)',boxShadow:'var(--shadow-lg)'}}>Positioning of this property's price relative to the market median.<br/>Example:<br/>1.1 = 10% above market<br/>0.9 = 10% below market</div>}
</div>
<Input loading={propertySettingsLoading} numeric min={0.1} max={3} value={pd.positioning} onChange={e=>setPropField(l.name,'positioning',e.target.value)} />
</div>
<InputWithSelectField loading={propertySettingsLoading} label="Minimum competitor count" value={pd.minComp} onChange={v=>setPropField(l.name,'minComp',v)} options={[{label:'Global: '+globalSettings.minComp,value:'',linked:true}]} />
</React.Fragment>}
</div>
</div>
<div>
<div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:14}}>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)'}}>Discounts by days left until stay</div>
<Switch loading={propertySettingsLoading} checked={pd.useUrgency!=='off'} onChange={v=>setPropField(l.name,'useUrgency',v?'on':'off')} />
</div>
{pd.useUrgency!=='off'&&<UrgencyRulesEditor loading={propertySettingsLoading} rules={pd.rules} setRules={u=>setPropRules(l.name,u)} />}
</div>
<div>
<div style={{fontWeight:700,fontSize:13,color:'var(--text-primary)',marginBottom:12}}>Bounds and rounding</div>
<div style={{display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
<InputWithSelectField loading={propertySettingsLoading} label="Minimum price" currency value={pd.minIDR} onChange={v=>setPropField(l.name,'minIDR',v)} options={[{label:'Global: '+globalSettings.minIDR,value:'',linked:true}]} />
<InputWithSelectField loading={propertySettingsLoading} label="Maximum price" currency value={pd.maxIDR} onChange={v=>setPropField(l.name,'maxIDR',v)} options={[{label:'Global: '+globalSettings.maxIDR,value:'',linked:true}]} />
</div>
<InputWithSelectField loading={propertySettingsLoading} label="Round to nearest" currency value={pd.step} onChange={v=>setPropField(l.name,'step',v)} options={[{label:'Global: '+globalSettings.step,value:'',linked:true}]} />
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
