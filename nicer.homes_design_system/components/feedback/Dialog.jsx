import React from 'react';
export function Dialog({open,title,children,onClose,footer}){
if(!open)return null;
return React.createElement('div',{style:{position:'fixed',inset:0,background:'rgba(11,12,14,0.4)',display:'flex',alignItems:'center',justifyContent:'center',zIndex:100}},
React.createElement('div',{style:{background:'var(--surface-card-solid)',border:'1px solid var(--glass-border)',backdropFilter:'blur(var(--glass-blur))',WebkitBackdropFilter:'blur(var(--glass-blur))',borderRadius:'var(--radius-lg)',boxShadow:'var(--shadow-lg)',padding:'var(--space-6)',width:380,maxWidth:'90vw'}},
React.createElement('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}},
React.createElement('h3',{style:{fontFamily:'var(--font-display)',fontSize:20,margin:0,color:'var(--text-primary)'}},title),
React.createElement('button',{onClick:onClose,style:{border:'none',background:'none',cursor:'pointer',fontSize:18,color:'var(--text-muted)'}},'\u00d7')),
React.createElement('div',{style:{color:'var(--text-secondary)',fontSize:14,lineHeight:'var(--leading-relaxed)'}},children),
footer&&React.createElement('div',{style:{marginTop:24,display:'flex',gap:10,justifyContent:'flex-end'}},footer)));
}
