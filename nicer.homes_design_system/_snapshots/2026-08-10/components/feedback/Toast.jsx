import React from 'react';
export function Toast({tone='neutral',children,onClose}){
const tones={neutral:'var(--color-ink-600)',success:'var(--color-success-700)',danger:'var(--color-danger)'};
return React.createElement('div',{style:{background:tones[tone],color:'#fff',borderRadius:'var(--radius-md)',padding:'12px 16px',display:'flex',alignItems:'center',gap:12,fontFamily:'var(--font-sans)',fontSize:13,boxShadow:'var(--shadow-md)',maxWidth:340}},
React.createElement('span',{style:{flex:1}},children),
onClose&&React.createElement('button',{onClick:onClose,style:{border:'none',background:'none',color:'rgba(255,255,255,0.7)',cursor:'pointer',fontSize:14}},'\u00d7'));
}
