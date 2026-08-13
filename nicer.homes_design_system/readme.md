# nicer.homes Design System

**nicer.homes** is a boutique hospitality company operating design-led vacation homes in Bali — combining property management, guest experience, and data-driven pricing for owners. Two audiences, one brand: guests booking a stay, and owners entrusting a property to nicer.

**Sources provided:** one logo file, `uploads/Nicer Logo Variations-selection.png` (wordmark only — no codebase, Figma, or existing site was attached; no real property photography was supplied). This system was built from that logo plus the brand brief; everything else (palette, type pairing, copy voice, screens) was designed from scratch per the user's direction. See "Caveats" below.

## Content fundamentals

- **Voice:** warm but restrained — never exclamatory, never salesy. Short declarative sentences. Respectful of the reader's time.
- **Person:** speaks as "we" (the operator) to "you" (guest or owner) — never third-person about the brand.
- **Casing:** sentence case everywhere, including headlines and nav labels. No all-caps except small mono labels (e.g. "NIGHTLY RATE") used as data annotations, not headlines.
- **Numbers:** prices in Indonesian Rupiah with comma thousand-separators (`Rp 4,850,000`); percentages and times set in mono for scannability.
- **Emoji:** none.
- **Example lines:** "A quieter kind of luxury." · "Every home, looked after." · "This can't be undone."

## Visual foundations

- **Color:** white-first — a white/mist/ink neutral scale plus a single vivid emerald accent (`--color-accent-500`) used for the primary action, positive states, and glow effects. A plain red covers danger/error states. No gold, no metallics, no multi-color palettes.
- **Type:** Inter (sans) is used throughout the interface — headlines and body alike. Lora (serif) is reserved for the logo/wordmark only, never set as live text in UI. Roboto Mono for prices/data/timestamps.
- **Backgrounds:** white pages with soft, blurred accent "glow blobs" placed behind hero/header areas — the source for the glass effect below. No photographic treatments (none were supplied), no patterns/textures.
- **Glass:** the signature surface treatment — `Card` and key panels use a translucent white fill + backdrop-blur (`.glass` / `--glass-bg`, `--glass-blur`) over a glow blob, giving a frosted, modern-fintech feel. Use it where a panel sits over a glow; drop to `glass={false}` (opaque) over busy/plain backgrounds.
- **Spacing:** 4px base scale (4/8/12/16/24/32/48/64/96/128), generous whitespace, airy card padding (24px+).
- **Radii:** soft — 6px (inputs/small), 10px (buttons), 18–26px (cards, larger panels, modals). Avatars/tags/switches use full-round.
- **Shadow:** soft and low-opacity for elevation (modals, dropdowns); the accent variant additionally gets a colored `--glow-accent` shadow to read as "lit up".
- **Borders:** 1px hairlines in `--border-default`; glass surfaces use a brighter `--glass-border` for a lit edge.
- **Motion:** minimal — 120–220ms ease-standard transitions on hover/press only (background/border-color/glow). No bounce, no parallax.
- **Hover/press states:** hover darkens filled buttons one step and adds a sunken neutral background to ghost/icon buttons; the accent button's glow intensifies slightly on hover.
- **Transparency/blur:** central to this system now — glass cards, glow blobs, and a dark scrim behind modals.
- **Imagery mood (once supplied):** should read bright, clean, minimal color grading. Placeholder blocks use the accent/mist/ink palette until real photos land.

## Iconography

No icon set or icon font was supplied. The UI kits use plain glyphs (○, ×, checkmarks) and color blocks in place of icons/photos — deliberately minimal rather than inventing an icon style. **Recommendation:** adopt a single-weight line icon set such as Lucide (CDN: `unpkg.com/lucide`) if/when icons are needed — its restrained stroke weight fits the brand; flag this as a substitution when used.

## Font substitution — please read

No webfont files were provided. The logo's serif (flat, lightly bracketed serifs, separated dot on the "i", moderate contrast) doesn't match any font in-house; **Lora** stands in wherever the actual wordmark is shown, but is not used as a live UI typeface — the interface is sans-only (Inter). **If you have the real brand typefaces, please share the font files (or names) and we'll swap them in.**

## Components

Standard primitive set (no component source was attached, so this is an intentional, from-scratch set sized to the brand):

- **Core:** Button, IconButton, Card, Badge, Tag — `components/core/`
- **Forms:** Input, Select, Checkbox, Radio, Switch, InputWithSelectField, LinkedValue — `components/forms/`
- **Feedback:** Dialog, Toast, Tooltip — `components/feedback/`
- **Navigation:** Tabs — `components/navigation/`

## UI kits

- `ui_kits/marketing-site/` — Property Detail page (guest-facing).
- `ui_kits/host-dashboard/` — Portfolio overview, Pricing & calendar, Guest messaging (owner-facing), navigable via the sidebar in `index.html`.

## Index

- `styles.css` — root stylesheet, imports everything under `tokens/`.
- `tokens/` — colors, typography, spacing, effects (radii/shadow/motion), fonts.
- `guidelines/` — foundation specimen cards (Colors, Type, Spacing, Brand groups) for the Design System tab.
- `assets/logo/` — the one provided wordmark, light and dark use.
- `components/` — see above.
- `ui_kits/` — see above.
- `SKILL.md` — portable skill file for use in Claude Code.

## Caveats — please help us iterate

- **No real product source.** Nothing was attached beyond the logo — every screen, color, and font pairing here is a first-pass invented direction, not a recreation of anything existing. Treat this as a strong starting proposal, not ground truth.
- **No real photography.** All imagery is flat color blocks. The system leans harder on type/color/space as a result — real villa photography would change a lot of layouts (especially the marketing site hero/gallery).
- **Font substitution.** Lora + Inter are stand-ins for an unknown real typeface — see above.
- **No icon set.** Adopted plain glyphs for now; happy to wire in a real icon library on your word.

**Ask:** tell us what's off — palette too cool/too warm, type pairing not quite "nicer", dashboard missing a key screen — and we'll tighten this into a system you'd actually ship against.
