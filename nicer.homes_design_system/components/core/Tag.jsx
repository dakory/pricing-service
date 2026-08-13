import React from 'react';
export function Tag({children,onRemove}){
return React.createElement('span',{style:{fontFamily:'var(--font-sans)',fontSize:'12px',color:'var(--text-primary)',border:'1px solid var(--border-default)',borderRadius:'var(--radius-full)',padding:'4px 8px 4px 12px',display:'inline-flex',alignItems:'center',gap:'6px'}},children,onRemove&&React.createElement('button',{type:'button',onClick:onRemove,style:{border:'none',background:'none',cursor:'pointer',color:'var(--text-muted)',fontSize:'14px',lineHeight:1,padding:0}},'\u00d7'));
}
