Combined free-text input + select. The top row is always editable custom text; any number of fixed options render below (scrollable past 4). Mark an option `linked:true` to render it as a LinkedValue pill (e.g. an inherited Global default) instead of plain text. Opening never shifts surrounding layout — it overlays.

```jsx
<InputWithSelectField label="Minimum competitor count" value={v} onChange={setV}
  options={[{label:'Global: 3', value:'', linked:true}]} />
```
