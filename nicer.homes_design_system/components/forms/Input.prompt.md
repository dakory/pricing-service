Single-line text field with optional label, prefix (e.g. currency), and error state.

```jsx
<Input label="Nightly rate" prefix="Rp" value={rate} onChange={e=>setRate(e.target.value)} />
```

Focus ring uses the sage accent; `error` swaps the border to terracotta and shows a message below.
