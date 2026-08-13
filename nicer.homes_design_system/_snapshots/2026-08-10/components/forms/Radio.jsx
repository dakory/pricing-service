import React from 'react';
export function Radio({label,checked,onChange,name}){
return React.createElement('label',{style:{display:'inline-flex',alignItems:'center',gap:8,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-primary)',cursor:'pointer'}},
React.createElement('span',{onClick:()=>onChange&&onChange(),style:{width:18,height:18,borderRadius:'var(--radius-full)',border:'1px solid '+(checked?'var(--action-accent)':'var(--border-strong)'),display:'inline-flex',alignItems:'center',justifyContent:'center'}},
checked&&React.createElement('span',{style:{width:9,height:9,borderRadius:'var(--radius-full)',background:'var(--action-accent)'}})),
label);
}
