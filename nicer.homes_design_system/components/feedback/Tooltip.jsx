import React from 'react';
export function Tooltip({label,children}){
const [show,setShow]=React.useState(false);
return React.createElement('span',{style:{position:'relative',display:'inline-flex'},onMouseEnter:()=>setShow(true),onMouseLeave:()=>setShow(false)},
children,
show&&React.createElement('span',{style:{position:'absolute',bottom:'calc(100% + 8px)',left:'50%',transform:'translateX(-50%)',background:'var(--color-ink-600)',color:'#fff',fontSize:12,padding:'5px 9px',borderRadius:'var(--radius-sm)',whiteSpace:'nowrap',fontFamily:'var(--font-sans)',zIndex:50,boxShadow:'var(--shadow-md)'}},label));
}
