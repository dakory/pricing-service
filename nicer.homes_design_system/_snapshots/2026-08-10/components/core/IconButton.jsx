import React from 'react';
export function IconButton({icon,label,size=36,active=false,onClick}){
const [hover,setHover]=React.useState(false);
const style={width:size,height:size,borderRadius:'var(--radius-full)',border:'none',background:active?'var(--surface-sunken)':hover?'var(--surface-sunken)':'transparent',color:'var(--text-primary)',display:'inline-flex',alignItems:'center',justifyContent:'center',cursor:'pointer',transition:'background var(--duration-fast) var(--ease-standard)'};
return React.createElement('button',{type:'button','aria-label':label,title:label,style,onClick,onMouseEnter:()=>setHover(true),onMouseLeave:()=>setHover(false)},icon);
}
