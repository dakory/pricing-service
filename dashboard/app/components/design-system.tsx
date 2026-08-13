// @ts-nocheck
"use client";
import React from "react";

export function IconButton({icon,label,size=36,active=false,onClick}) {
  const [hover,setHover]=React.useState(false);
  const style={width:size,height:size,borderRadius:'var(--radius-full)',border:'none',background:active?'var(--surface-sunken)':hover?'var(--surface-sunken)':'transparent',color:'var(--text-primary)',display:'inline-flex',alignItems:'center',justifyContent:'center',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'};
  return <button type="button" aria-label={label} title={label} style={style} onClick={onClick} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>{icon}</button>;
}

export function Button({variant='primary',size='md',disabled=false,children,onClick,type='button',style:styleProp}) {
  const sizeMap={sm:{padding:'0 16px',fontSize:'13px',height:'38px'},md:{padding:'0 20px',fontSize:'14px',height:'44px'},lg:{padding:'0 26px',fontSize:'15px',height:'52px'}};
  const base={fontFamily:'var(--font-sans)',fontWeight:600,borderRadius:'var(--radius-full)',border:'1px solid transparent',boxSizing:'border-box',cursor:disabled?'default':'pointer',transition:'background var(--duration-fast) var(--ease-standard), color var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)',opacity:disabled?0.45:1,display:'inline-flex',alignItems:'center',justifyContent:'center',gap:'8px',...sizeMap[size]};
  const variants={primary:{background:'var(--action-primary)',color:'var(--text-inverse)'},accent:{background:'var(--action-accent)',color:'var(--action-accent-ink)',boxShadow:'var(--glow-accent)'},secondary:{background:'var(--action-secondary)',color:'var(--text-primary)',borderColor:'var(--border-strong)'},ghost:{background:'transparent',color:'var(--text-primary)'}};
  const [hover,setHover]=React.useState(false);
  const hoverBg={primary:'var(--action-primary-hover)',accent:'var(--action-accent-hover)',secondary:'var(--action-secondary-hover)',ghost:'var(--surface-sunken)'};
  const style={...base,...variants[variant],...styleProp};
  if(hover&&!disabled)style.background=hoverBg[variant];
  return <button type={type} disabled={disabled} style={style} onClick={onClick} onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>{children}</button>;
}

export function Input({label,type='text',placeholder,value,onChange,error,prefix,numeric=false,min,max,integer=false}) {
  const [focus,setFocus]=React.useState(false);
  const [localError,setLocalError]=React.useState('');
  const border = error||localError ? 'var(--status-danger)' : focus ? 'var(--focus-ring)' : 'var(--border-default)';
  const formatCurrency = raw => String(raw ?? '').replace(/\D/g,'').replace(/\B(?=(\d{3})+(?!\d))/g,',');
  const handleChange = event => {
    let next=event.target.value;
    if(numeric) next=prefix==='Rp'?formatCurrency(next):next.replace(/[^0-9.\-]/g,'');
    setLocalError('');
    onChange?.({...event,target:{...event.target,value:next}});
  };
  const handleBlur = event => {
    setFocus(false);
    if(!numeric||event.target.value==='') return;
    const parsed=Number(String(event.target.value).replace(/,/g,''));
    const invalid=!Number.isFinite(parsed)||(integer&&!Number.isInteger(parsed))||(min!=null&&parsed<min)||(max!=null&&parsed>max);
    setLocalError(invalid?`Enter a value${min!=null?` from ${min.toLocaleString()}`:''}${max!=null?` to ${max.toLocaleString()}`:''}.`:'');
  };
  return <label style={{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}}>
    {label&&<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>{label}</span>}
    <div style={{display:'flex',alignItems:'center',gap:8,height:38,boxSizing:'border-box',border:`1px solid ${border}`,borderRadius:'var(--radius-full)',padding:'0 20px',background:'var(--surface-card)',transition:'border-color var(--duration-fast) var(--ease-standard)'}}>
      {prefix&&<span style={{color:'var(--text-muted)',fontSize:14}}>{prefix}</span>}
      <input type={type} inputMode={numeric?'decimal':undefined} placeholder={placeholder} value={value} onChange={handleChange} onFocus={()=>setFocus(true)} onBlur={handleBlur} style={{border:'none',outline:'none',fontSize:14,fontFamily:'var(--font-sans)',color:'var(--text-primary)',width:'100%',background:'transparent'}}/>
    </div>
    {(error||localError)&&<span style={{fontSize:12,color:'var(--status-danger)'}}>{error||localError}</span>}
  </label>;
}

export function Select({label,options=[],value,onChange,pill=true}) {
  const selectStyle = {
    border: '1px solid var(--border-default)', borderRadius: 'var(--radius-full)',
    height: 38, boxSizing: 'border-box', padding: '0 36px 0 20px',
    fontSize: 14, fontWeight: pill ? 600 : 400, fontFamily: 'var(--font-sans)',
    color: 'var(--text-primary)', background: 'var(--surface-card)', appearance: 'none',
    WebkitAppearance: 'none', backgroundImage: 'url("https://unpkg.com/lucide-static@latest/icons/chevron-down.svg")',
    backgroundRepeat: 'no-repeat', backgroundPosition: 'right 14px center', backgroundSize: 14, cursor: 'pointer'
  };
  return (
    <label style={{display:'flex', flexDirection:'column', gap:6, fontFamily:'var(--font-sans)'}}>
      {label && <span style={{fontSize:12, fontWeight:600, color:'var(--text-secondary)'}}>{label}</span>}
      <select value={value} onChange={onChange} style={selectStyle}>
        {options.map(o => <option key={o.value || o} value={o.value || o}>{o.label || o}</option>)}
      </select>
    </label>
  );
}

export function Switch({checked,onChange,label}) {
  return <label style={{display:'inline-flex',alignItems:'center',gap:10,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-primary)',cursor:'pointer'}}><span onClick={()=>onChange&&onChange(!checked)} style={{width:38,height:22,borderRadius:'var(--radius-full)',background:checked?'var(--action-accent)':'var(--border-strong)',position:'relative',transition:'background var(--duration-standard) var(--ease-standard)'}}><span style={{position:'absolute',top:2,left:checked?18:2,width:18,height:18,borderRadius:'var(--radius-full)',background:'#fff',transition:'left var(--duration-standard) var(--ease-standard)',boxShadow:'var(--shadow-sm)'}}/></span>{label}</label>;
}

export function Toast({tone='neutral',children,onClose}) {
  const tones={neutral:'var(--color-ink-600)',success:'var(--color-success-700)',danger:'var(--color-danger)'};
  return <div style={{background:tones[tone],color:'#fff',borderRadius:'var(--radius-md)',padding:'12px 16px',display:'flex',alignItems:'center',gap:12,fontFamily:'var(--font-sans)',fontSize:13,boxShadow:'var(--shadow-md)',maxWidth:340}}><span style={{flex:1}}>{children}</span>{onClose&&<button onClick={onClose} style={{border:'none',background:'none',color:'rgba(255,255,255,0.7)',cursor:'pointer',fontSize:14}}>×</button>}</div>;
}

function LinkedValue({children}) { return <span style={{display:'inline-flex',alignItems:'center',height:24,padding:'0 10px',borderRadius:'var(--radius-full)',background:'var(--surface-sunken)',color:'var(--text-secondary)',fontSize:12,fontWeight:600,whiteSpace:'nowrap'}}>{children}</span>; }

export function InputWithSelectField({label,options=[],value,onChange,placeholder='Enter a value',currency=false}) {
  const [focused,setFocused]=React.useState(false); const [activeIdx,setActiveIdx]=React.useState(-1); const ref=React.useRef(null);
  const isMatchedOption=options.some(o=>o.value===value); const isCustom=value!=null&&value!==''&&!isMatchedOption; const selectedOpt=options.find(o=>o.value===value);
  React.useEffect(()=>{if(!focused)return;const onDoc=e=>{if(ref.current&&!ref.current.contains(e.target))setFocused(false)};document.addEventListener('mousedown',onDoc);return()=>document.removeEventListener('mousedown',onDoc)},[focused]);
  React.useEffect(()=>{if(focused)setActiveIdx(-1)},[focused]);
  const displayLabel=opt=>opt.linked?<LinkedValue>{opt.label}</LinkedValue>:<span style={{fontSize:14,fontWeight:400,color:'var(--text-secondary)',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{opt.label}</span>;
  const formatCurrency = raw => String(raw ?? '').replace(/\D/g,'').replace(/\B(?=(\d{3})+(?!\d))/g,',');
  const normalize = raw => currency ? formatCurrency(raw) : raw;
  const selectOption=opt=>{onChange&&onChange(normalize(opt.value));setFocused(false)};
  const onKeyDown=e=>{if(e.key==='ArrowDown'){e.preventDefault();setActiveIdx(i=>Math.min(i+1,options.length-1))}else if(e.key==='ArrowUp'){e.preventDefault();setActiveIdx(i=>Math.max(i-1,-1))}else if(e.key==='Enter'&&activeIdx>=0){e.preventDefault();selectOption(options[activeIdx])}else if(e.key==='Escape')setFocused(false)};
  const rowStyle=(selected,active)=>({display:'flex',alignItems:'center',justifyContent:'space-between',height:38,padding:'0 20px',flexShrink:0,background:selected?'#F5F5F5':active?'var(--color-mist)':'transparent',cursor:'pointer'});
  return <label style={{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}}>{label?<span style={{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}}>{label}</span>:null}<div ref={ref} style={{position:'relative',height:38}}><div style={{position:focused?'absolute':'static',top:0,left:0,right:0,border:'1px solid '+(focused?'var(--focus-ring)':'var(--border-default)'),borderRadius:19,overflow:'hidden',transition:'border-color var(--duration-fast) var(--ease-standard)',background:'var(--color-white)',boxShadow:focused?'var(--shadow-lg)':'none',zIndex:10}}>{!focused?<div onClick={()=>setFocused(true)} style={{height:38,display:'flex',alignItems:'center',padding:'0 20px',cursor:'text'}}>{isCustom?<span style={{fontSize:14,color:'var(--text-primary)'}}>{value}</span>:selectedOpt?displayLabel(selectedOpt):<span style={{fontSize:14,color:'var(--text-muted)'}}>{placeholder}</span>}</div>:<div style={rowStyle(isCustom,activeIdx===-1)} onMouseEnter={()=>setActiveIdx(-1)}><input autoFocus value={isCustom?value:''} onChange={e=>onChange&&onChange(normalize(e.target.value))} onFocus={()=>setFocused(true)} onKeyDown={onKeyDown} placeholder={placeholder} inputMode={currency?'numeric':undefined} style={{border:'none',outline:'none',background:'transparent',fontSize:14,fontWeight:400,fontFamily:'var(--font-sans)',color:'var(--text-primary)',width:'100%',padding:0,margin:0}}/>{isCustom?<img src="https://unpkg.com/lucide-static@latest/icons/check.svg" style={{width:14,height:14,opacity:0.5,flexShrink:0}}/>:null}</div>}{focused&&options.length>0?<div style={{maxHeight:38*4,overflowY:'auto'}}>{options.map((opt,i)=>{const selected=opt.value===value;return <div key={opt.value} onMouseDown={e=>{e.preventDefault();selectOption(opt)}} onMouseEnter={()=>setActiveIdx(i)} style={rowStyle(selected,activeIdx===i)}>{displayLabel(opt)}{selected?<img src="https://unpkg.com/lucide-static@latest/icons/check.svg" style={{width:14,height:14,opacity:0.5,flexShrink:0}}/>:null}</div>})}</div>:null}</div></div></label>;
}
