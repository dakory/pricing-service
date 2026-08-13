import React from 'react';
export function Card({children,padding='var(--space-5)',elevated=false,glass=true,style}){
return React.createElement('div',{style:{background:glass?'var(--surface-card)':'var(--surface-card-solid)',backdropFilter:glass?'blur(var(--glass-blur))':'none',WebkitBackdropFilter:glass?'blur(var(--glass-blur))':'none',border:glass?'1px solid var(--glass-border)':'none',borderRadius:'var(--radius-lg)',boxShadow:elevated?'var(--shadow-lg)':'var(--shadow-md)',padding,...style}},children);
}
