import React from 'react';
export function Badge({tone='neutral',children}){
const tones={
neutral:{background:'var(--surface-sunken)',color:'var(--text-secondary)'},
accent:{background:'var(--action-accent-soft)',color:'var(--color-ink-900)'},
success:{background:'var(--status-success-soft)',color:'var(--status-success)'},
danger:{background:'var(--status-danger-soft)',color:'var(--status-danger)'},
inverse:{background:'var(--color-ink-900)',color:'var(--text-inverse)'},
};
return React.createElement('span',{style:{...tones[tone],fontFamily:'var(--font-sans)',fontSize:'12px',fontWeight:600,padding:'3px 10px',borderRadius:'var(--radius-full)',display:'inline-flex',alignItems:'center'}},children);
}
