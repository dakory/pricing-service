import React from 'react';
export function Select({label,options=[],value,onChange,pill=false}){
return React.createElement('label',{style:{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}},
label&&React.createElement('span',{style:{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}},label),
React.createElement('select',{value,onChange,style:{border:'1px solid var(--border-default)',borderRadius:pill?'var(--radius-full)':'var(--radius-md)',height:pill?38:undefined,boxSizing:'border-box',padding:pill?'0 36px 0 18px':'10px 32px 10px 12px',fontSize:14,fontWeight:pill?600:400,fontFamily:'var(--font-sans)',color:'var(--text-primary)',background:'var(--surface-card)',appearance:'none',WebkitAppearance:'none',backgroundImage:'url("https://unpkg.com/lucide-static@latest/icons/chevron-down.svg")',backgroundRepeat:'no-repeat',backgroundPosition:'right 12px center',backgroundSize:'14px',cursor:'pointer'}},
options.map(o=>React.createElement('option',{key:o.value||o,value:o.value||o},o.label||o))));
}
