import React from 'react';
export function Input({label,type='text',placeholder,value,onChange,error,prefix}){
const [focus,setFocus]=React.useState(false);
return React.createElement('label',{style:{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}},
label&&React.createElement('span',{style:{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}},label),
React.createElement('div',{style:{display:'flex',alignItems:'center',gap:8,height:38,boxSizing:'border-box',border:'1px solid '+(error?'var(--status-danger)':focus?'var(--focus-ring)':'var(--border-default)'),borderRadius:'var(--radius-full)',padding:'0 20px',background:'var(--surface-card)',transition:'border-color var(--duration-fast) var(--ease-standard)'}},
prefix&&React.createElement('span',{style:{color:'var(--text-muted)',fontSize:14}},prefix),
React.createElement('input',{type,placeholder,value,onChange,onFocus:()=>setFocus(true),onBlur:()=>setFocus(false),style:{border:'none',outline:'none',fontSize:14,fontFamily:'var(--font-sans)',color:'var(--text-primary)',width:'100%',background:'transparent'}})),
error&&React.createElement('span',{style:{fontSize:12,color:'var(--status-danger)'}},error));
}
