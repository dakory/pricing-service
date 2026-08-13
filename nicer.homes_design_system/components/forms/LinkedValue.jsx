import React from 'react';
export function LinkedValue({children}){
return React.createElement('span',{style:{fontSize:12.5,fontWeight:600,color:'var(--text-secondary)',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis',background:'var(--color-line)',borderRadius:'var(--radius-full)',padding:'4px 10px',display:'inline-block'}},children);
}
