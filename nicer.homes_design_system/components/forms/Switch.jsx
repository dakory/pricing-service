import React from 'react';
export function Switch({checked,onChange,label}){
return React.createElement('label',{style:{display:'inline-flex',alignItems:'center',gap:10,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-primary)',cursor:'pointer'}},
React.createElement('span',{onClick:()=>onChange&&onChange(!checked),style:{width:38,height:22,borderRadius:'var(--radius-full)',background:checked?'var(--action-accent)':'var(--border-strong)',position:'relative',transition:'background var(--duration-standard) var(--ease-standard)'}},
React.createElement('span',{style:{position:'absolute',top:2,left:checked?18:2,width:18,height:18,borderRadius:'var(--radius-full)',background:'#fff',transition:'left var(--duration-standard) var(--ease-standard)',boxShadow:'var(--shadow-sm)'}})),
label);
}
