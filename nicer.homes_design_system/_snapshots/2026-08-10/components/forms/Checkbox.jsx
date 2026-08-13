import React from 'react';
export function Checkbox({label,checked,onChange}){
return React.createElement('label',{style:{display:'inline-flex',alignItems:'center',gap:8,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-primary)',cursor:'pointer'}},
React.createElement('span',{onClick:()=>onChange&&onChange(!checked),style:{width:18,height:18,borderRadius:'var(--radius-sm)',border:'1px solid '+(checked?'var(--action-accent)':'var(--border-strong)'),background:checked?'var(--action-accent)':'var(--surface-card)',display:'inline-flex',alignItems:'center',justifyContent:'center',transition:'background var(--duration-fast) var(--ease-standard)'}},
checked&&React.createElement('span',{style:{color:'#fff',fontSize:11}},'\u2713')),
label);
}
