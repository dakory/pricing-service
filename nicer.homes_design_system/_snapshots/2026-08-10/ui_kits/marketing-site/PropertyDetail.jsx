const {Button,Tag,Badge,IconButton}=window.NicerHomesDesignSystem_ea7f10;
function Header(){
return (
<header style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'20px 48px',borderBottom:'1px solid var(--border-default)'}}>
<img src="../../assets/logo/nicer-wordmark.png" style={{height:22}} />
<nav style={{display:'flex',gap:32,fontFamily:'var(--font-sans)',fontSize:14,color:'var(--text-secondary)'}}>
<span>Stay</span><span>Host with us</span><span>Journal</span>
</nav>
<Button variant="secondary" size="sm">Enquire</Button>
</header>);
}
function Gallery(){
const cells=[{big:true,c:'var(--color-accent-300)'},{c:'var(--color-mist)'},{c:'var(--color-ink-200)'},{c:'var(--color-accent-500)'},{c:'var(--color-mist)'}];
return (
<div style={{display:'grid',gridTemplateColumns:'2fr 1fr 1fr',gridTemplateRows:'1fr 1fr',gap:6,height:420,padding:'0 48px',marginTop:24}}>
<div style={{gridRow:'1 / 3',background:cells[0].c,borderRadius:'var(--radius-lg)'}} />
<div style={{background:cells[1].c,borderRadius:'var(--radius-lg)'}} />
<div style={{background:cells[2].c,borderRadius:'var(--radius-lg)'}} />
<div style={{background:cells[3].c,borderRadius:'var(--radius-lg)'}} />
<div style={{background:cells[4].c,borderRadius:'var(--radius-lg)'}} />
</div>);
}
function PropertyDetail(){
const amenities=['Private pool','Ocean view','Full staff','Rice-field access','Open-air living','Chef on request'];
return (
<div style={{fontFamily:'var(--font-sans)',background:'var(--surface-page)',minHeight:'100vh',position:'relative'}}>
<div className="glow-blob" style={{width:480,height:480,background:'var(--color-accent-300)',top:-160,right:-120,opacity:0.4}} />
<Header/>
<div style={{padding:'32px 48px 0',position:'relative',zIndex:1}}>
<div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
<div>
<div style={{fontFamily:'var(--font-sans)',fontSize:12,letterSpacing:'var(--tracking-wide)',textTransform:'uppercase',color:'var(--text-secondary)',marginBottom:8}}>Uluwatu, Bali</div>
<h1 style={{fontFamily:'var(--font-display)',fontWeight:400,fontSize:'var(--text-4xl)',margin:0,color:'var(--text-primary)',letterSpacing:'var(--tracking-tight)'}}>Villa Kayu</h1>
</div>
<div style={{textAlign:'right'}}>
<div style={{fontFamily:'var(--font-mono)',fontSize:'var(--text-2xl)',color:'var(--text-primary)'}}>Rp 4,850,000</div>
<div style={{fontSize:13,color:'var(--text-secondary)'}}>per night</div>
</div>
</div>
</div>
<Gallery/>
<div style={{display:'grid',gridTemplateColumns:'1fr 340px',gap:48,padding:'40px 48px 80px',maxWidth:1200,position:'relative',zIndex:1}}>
<div>
<p style={{fontSize:'var(--text-lg)',fontWeight:400,lineHeight:'var(--leading-relaxed)',color:'var(--text-primary)',fontFamily:'var(--font-display)',maxWidth:640}}>A four-bedroom home set above the rice terraces, ten minutes from Uluwatu's reef breaks. Designed for slow mornings and long dinners, with a resident team looking after every detail.</p>
<div style={{display:'flex',flexWrap:'wrap',gap:8,marginTop:24}}>
{amenities.map(a=><Tag key={a}>{a}</Tag>)}
</div>
</div>
<div className="glass" style={{borderRadius:'var(--radius-lg)',padding:'var(--space-6)',height:'fit-content',position:'sticky',top:24,boxShadow:'var(--shadow-lg)'}}>
<Badge tone="accent">3 nights minimum</Badge>
<div style={{marginTop:16,display:'flex',flexDirection:'column',gap:12}}>
<div style={{display:'flex',justifyContent:'space-between',fontSize:14,color:'var(--text-secondary)'}}><span>Check-in</span><span style={{color:'var(--text-primary)'}}>14:00</span></div>
<div style={{display:'flex',justifyContent:'space-between',fontSize:14,color:'var(--text-secondary)'}}><span>Check-out</span><span style={{color:'var(--text-primary)'}}>11:00</span></div>
</div>
<Button variant="accent" size="lg" style={{width:'100%',marginTop:28}}>Check availability</Button>
</div>
</div>
</div>);
}
window.PropertyDetail=PropertyDetail;
