Two normal buttons — `primary` (solid black) and `secondary` (solid white, hairline border) — cover most actions. Reserve `accent` (vibrant lime, dark text, glow) for the single CTA / main action on a screen. `ghost` is text-only for the lowest-emphasis case.

```jsx
<Button variant="primary" size="md" onClick={save}>Save changes</Button>
<Button variant="accent" size="lg" onClick={book}>Check availability</Button>
```

Sizes: `sm`, `md`, `lg`. `disabled` dims to 45% opacity.
