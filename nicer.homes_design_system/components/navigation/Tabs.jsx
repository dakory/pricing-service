import React from 'react';
export function Tabs({items=[],value,onChange}){
return React.createElement('div',{style:{display:'flex',gap:24,borderBottom:'1px solid var(--border-default)',fontFamily:'var(--font-sans)'}},
items.map(it=>{
const active=it.value===value;
return React.createElement('button',{key:it.value,onClick:()=>onChange&&onChange(it.value),style:{border:'none',background:'none',cursor:'pointer',padding:'10px 0',fontSize:14,fontWeight:500,color:active?'var(--text-primary)':'var(--text-secondary)',borderBottom:'2px solid '+(active?'var(--action-accent)':'transparent'),marginBottom:-1}},it.label);
}));
}
