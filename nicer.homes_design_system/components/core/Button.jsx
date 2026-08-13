import React from 'react';
const sizeMap={sm:{padding:'0 16px',fontSize:'13px',height:'38px'},md:{padding:'0 20px',fontSize:'14px',height:'44px'},lg:{padding:'0 26px',fontSize:'15px',height:'52px'}};
export function Button({variant='primary',size='md',disabled=false,children,onClick,type='button',style:styleProp}){
const base={fontFamily:'var(--font-sans)',fontWeight:600,borderRadius:'var(--radius-full)',border:'1px solid transparent',boxSizing:'border-box',cursor:disabled?'default':'pointer',transition:'background var(--duration-fast) var(--ease-standard), color var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)',opacity:disabled?0.45:1,display:'inline-flex',alignItems:'center',justifyContent:'center',gap:'8px',...sizeMap[size]};
const variants={
primary:{background:'var(--action-primary)',color:'var(--text-inverse)'},
accent:{background:'var(--action-accent)',color:'var(--action-accent-ink)',boxShadow:'var(--glow-accent)'},
secondary:{background:'var(--action-secondary)',color:'var(--text-primary)',borderColor:'var(--border-strong)'},
ghost:{background:'transparent',color:'var(--text-primary)'},
};
const [hover,setHover]=React.useState(false);
const hoverBg={primary:'var(--action-primary-hover)',accent:'var(--action-accent-hover)',secondary:'var(--action-secondary-hover)',ghost:'var(--surface-sunken)'};
const style={...base,...variants[variant],...styleProp};
if(hover&&!disabled)style.background=hoverBg[variant];
return React.createElement('button',{type,disabled,style,onClick,onMouseEnter:()=>setHover(true),onMouseLeave:()=>setHover(false)},children);
}
