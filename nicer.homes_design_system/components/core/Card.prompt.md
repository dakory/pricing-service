General-purpose surface container — frosted glass (translucent + blur + lit border) by default; this is the only card style used across the system, on white or glow backgrounds alike.

```jsx
<Card elevated><PropertySummary/></Card>
```

Set `elevated` for cards that float above the page (modals, dropdown panels) — adds a deeper shadow. Pass `glass={false}` only when a card must sit over busy/patterned content and needs full opacity — it drops the border entirely and relies on shadow alone (never a flat gray outline).
