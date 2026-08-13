import React from 'react';
import { LinkedValue } from './LinkedValue.jsx';
export function InputWithSelectField({label,options=[],value,onChange,placeholder='Enter a value'}){
const [focused,setFocused]=React.useState(false);
const [activeIdx,setActiveIdx]=React.useState(-1);
const ref=React.useRef(null);
const isMatchedOption=options.some(o=>o.value===value);
const isCustom=value!=null&&value!==''&&!isMatchedOption;
const selectedOpt=options.find(o=>o.value===value);
React.useEffect(()=>{
if(!focused)return;
const onDoc=(e)=>{if(ref.current&&!ref.current.contains(e.target))setFocused(false);};
document.addEventListener('mousedown',onDoc);
return ()=>document.removeEventListener('mousedown',onDoc);
},[focused]);
React.useEffect(()=>{if(focused)setActiveIdx(-1);},[focused]);
const displayLabel=(opt)=>opt.linked
?React.createElement(LinkedValue,{key:opt.value},opt.label)
:React.createElement('span',{style:{fontSize:14,fontWeight:400,color:'var(--text-secondary)',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}},opt.label);
const selectOption=(opt)=>{onChange&&onChange(opt.value);setFocused(false);};
const onKeyDown=(e)=>{
if(e.key==='ArrowDown'){e.preventDefault();setActiveIdx((i)=>Math.min(i+1,options.length-1));}
else if(e.key==='ArrowUp'){e.preventDefault();setActiveIdx((i)=>Math.max(i-1,-1));}
else if(e.key==='Enter'&&activeIdx>=0){e.preventDefault();selectOption(options[activeIdx]);}
else if(e.key==='Escape'){setFocused(false);}
};
const rowStyle=(selected,active)=>({display:'flex',alignItems:'center',justifyContent:'space-between',height:38,padding:'0 20px',flexShrink:0,background:selected?'#F5F5F5':active?'var(--color-mist)':'transparent',cursor:'pointer'});
return React.createElement('label',{style:{display:'flex',flexDirection:'column',gap:6,fontFamily:'var(--font-sans)'}},
label?React.createElement('span',{style:{fontSize:12,fontWeight:600,color:'var(--text-secondary)'}},label):null,
React.createElement('div',{ref:ref,style:{position:'relative',height:38}},
React.createElement('div',{style:{position:focused?'absolute':'static',top:0,left:0,right:0,border:'1px solid '+(focused?'var(--focus-ring)':'var(--border-default)'),borderRadius:19,overflow:'hidden',transition:'border-color var(--duration-fast) var(--ease-standard)',background:'var(--color-white)',boxShadow:focused?'var(--shadow-lg)':'none',zIndex:10}},
!focused
?React.createElement('div',{onClick:()=>setFocused(true),style:{height:38,display:'flex',alignItems:'center',padding:'0 20px',cursor:'text'}},
isCustom?React.createElement('span',{style:{fontSize:14,color:'var(--text-primary)'}},value):selectedOpt?displayLabel(selectedOpt):React.createElement('span',{style:{fontSize:14,color:'var(--text-muted)'}},placeholder))
:React.createElement('div',{style:rowStyle(isCustom,activeIdx===-1),onMouseEnter:()=>setActiveIdx(-1)},
React.createElement('input',{autoFocus:true,value:isCustom?value:'',onChange:(e)=>onChange&&onChange(e.target.value),onFocus:()=>setFocused(true),onKeyDown,placeholder,style:{border:'none',outline:'none',background:'transparent',fontSize:14,fontWeight:400,fontFamily:'var(--font-sans)',color:'var(--text-primary)',width:'100%',padding:0,margin:0}}),
isCustom?React.createElement('img',{src:'https://unpkg.com/lucide-static@latest/icons/check.svg',style:{width:14,height:14,opacity:0.5,flexShrink:0}}):null),
focused&&options.length>0?React.createElement('div',{style:{maxHeight:38*4,overflowY:'auto'}},
options.map((opt,i)=>{
const selected=opt.value===value;
return React.createElement('div',{key:opt.value,onMouseDown:(e)=>{e.preventDefault();selectOption(opt);},onMouseEnter:()=>setActiveIdx(i),style:rowStyle(selected,activeIdx===i)},
displayLabel(opt),
selected?React.createElement('img',{src:'https://unpkg.com/lucide-static@latest/icons/check.svg',style:{width:14,height:14,opacity:0.5,flexShrink:0}}):null);
})
):null
)
)
);
}
