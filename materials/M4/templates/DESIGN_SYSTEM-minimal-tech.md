# DESIGN_SYSTEM.md

> Design system: minimal-tech
> Aesthetic: dark, functional, high-density data interface
> Format: shadcn/ui + Tailwind CSS 4 + CSS variables
> Last updated: 2026-05-03
> Reference aesthetic: Linear, Vercel dashboard, Raycast — generous spacing + restrained palette

---

## 1. Color Palette

Semantic roles (используй эти имена в коде, не сырой hex):

| Role             | Light mode          | Dark mode           | Hex (dark)   | OKLCH (dark)             |
|------------------|---------------------|---------------------|--------------|--------------------------|
| `--background`   | Page background     | Page background     | `#0f172a`    | `oklch(0.12 0.02 250)`   |
| `--foreground`   | Primary text        | Primary text        | `#f1f5f9`    | `oklch(0.95 0.01 248)`   |
| `--card`         | Card surface        | Card surface        | `#1e293b`    | `oklch(0.19 0.02 252)`   |
| `--card-alt`     | Elevated card       | Elevated card       | `#263348`    | `oklch(0.23 0.03 250)`   |
| `--primary`      | Primary action      | Primary action      | `#6366f1`    | `oklch(0.55 0.22 264)`   |
| `--primary-fg`   | Text on primary bg  | Text on primary bg  | `#ffffff`    | `oklch(1.0 0 0)`         |
| `--muted`        | Muted text, hints   | Muted text, hints   | `#64748b`    | `oklch(0.50 0.04 254)`   |
| `--accent`       | Cyan highlight      | Cyan highlight      | `#22d3ee`    | `oklch(0.83 0.18 197)`   |
| `--destructive`  | Error, danger       | Error, danger       | `#f87171`    | `oklch(0.70 0.17 22)`    |
| `--border`       | Borders, dividers   | Borders, dividers   | `#1e293b`    | `oklch(0.19 0.02 252)`   |
| `--ring`         | Focus ring          | Focus ring          | `#818cf8`    | `oklch(0.67 0.18 264)`   |

Light mode variant:
- `--background`: `#f8fafc` / `--foreground`: `#0f172a` / `--card`: `#ffffff`
- `--card-alt`: `#f1f5f9` / `--primary`: `#6366f1` / `--muted`: `#94a3b8`
- `--border`: `#e2e8f0`

Dark mode strategy: CSS variables only. **NEVER** use `dark:bg-gray-900` hardcoded.
All colors defined as CSS variables, swapped via `.dark` class on `<html>`.

---

## 2. Typography

Font family: **Manrope** (NOT Inter — overused to the point of invisibility)
Fallback: `system-ui, -apple-system, sans-serif`
Import: `@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap')`

Mono font: **JetBrains Mono** — for code blocks, data values, timestamps
Mono import: `@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap')`

Scale:

| Step    | Size  | Line-height | Letter-spacing | Weight | Usage             |
|---------|-------|-------------|----------------|--------|--------------------|
| Display | 64px  | 1.1         | -0.03em        | 700    | Hero headline      |
| H1      | 48px  | 1.15        | -0.02em        | 700    | Page title         |
| H2      | 36px  | 1.25        | -0.015em       | 600    | Section header     |
| H3      | 28px  | 1.35        | -0.01em        | 600    | Card header        |
| H4      | 20px  | 1.4         | -0.005em       | 600    | Subhead            |
| Body    | 16px  | 1.6         | 0              | 400    | Main content       |
| Small   | 14px  | 1.5         | 0              | 400    | Secondary text     |
| Caption | 12px  | 1.4         | 0.01em         | 500    | Labels, metadata   |
| Mono    | 14px  | 1.6         | 0              | 400    | Code, data         |

Tracking rationale: negative tracking (-0.02em) on headings tightens letterforms
at large sizes for a dense, technical feel (common in Linear, Vercel, Raycast).

---

## 3. Spacing Scale

Strict multiples of 8px only. No arbitrary values.

```
4px  — micro (icon + label gap, badge inner)
8px  — xs  (tight padding, table cells)
16px — sm  (component inner padding, form fields)
24px — md  (card padding, sidebar items)
32px — lg  (section padding, between card groups)
48px — xl  (between major sections)
64px — 2xl (page-level vertical rhythm)
96px — 3xl (hero sections, splash screens)
```

NEVER use: px, py, pt with values like `14px`, `18px`, `22px`.
Tailwind config (tailwind.config.ts):
```js
spacing: {
  '0.5': '4px',
  '1':   '8px',
  '2':   '16px',
  '3':   '24px',
  '4':   '32px',
  '6':   '48px',
  '8':   '64px',
  '12':  '96px',
}
```

---

## 4. Border Radius Scale

```
none: 0px     — tables, data grids, sharp-edge elements
sm:   4px     — badges, chips, code blocks, small tags
md:   8px     — buttons, inputs (default)
lg:   12px    — cards (default)
xl:   16px    — modals, popovers, command palettes
full: 9999px  — pills, avatars, toggle switches
```

Tailwind mapping: `rounded-none` / `rounded-sm` (4px) / `rounded-md` (8px) /
`rounded-lg` (12px) / `rounded-xl` (16px) / `rounded-full`.

---

## 5. Elevation / Shadow Approach

**Philosophy: NO box shadows by default. Depth from background contrast.**

This creates a layered, architectural feel without visual noise — characteristic
of Linear, Vercel dashboard, and Raycast. Rule: «NO shadows — depth from background contrast only».

3-level elevation system:
- **Level 0 (page):** `--background` (`#0f172a`) — the base canvas
- **Level 1 (card):** `--card` (`#1e293b`) — subtle lift via bg color
- **Level 2 (card-alt / floating):** `--card-alt` (`#263348`) — modals, dropdowns, tooltips

Exception — when shadows are required (dropdown menus, context menus, tooltips):
```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.25);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.35), 0 2px 4px -1px rgba(0,0,0,0.25);
```

NEVER use `shadow-lg` reflexively.
NEVER use thick borders for visual separation.

---

## 6. Component Patterns

### Cards
```
Background:    var(--card)
Padding:       24px (md)
Border radius: 12px (lg)
Border:        1px solid var(--border) — subtle, not heavy
Hover:         border-color → var(--primary), transition 150ms ease
```

### Buttons
```
Primary:   bg var(--primary), text var(--primary-fg), radius 8px (md)
           px 16px, py 8px
           Hover: scale(1.02), brightness(1.05), transition 150ms
Secondary: bg transparent, border 1px var(--border), text var(--foreground)
           Hover: bg var(--card), transition 150ms
Danger:    bg var(--destructive), text white
Ghost:     bg transparent, no border, text var(--muted)
           Hover: text var(--foreground), bg var(--card)
Disabled:  opacity 0.4, cursor not-allowed
```

### Inputs
```
Background:    var(--background)
Border:        1px solid var(--border)
Border radius: 8px (md)
Padding:       8px 12px
Focus:         border-color var(--ring), box-shadow 0 0 0 2px oklch(from var(--ring) l c h / 0.2)
Placeholder:   color var(--muted)
```

### Badges / Chips
```
Padding:       2px 8px
Border radius: 9999px (full)
Font:          12px, weight 500
Background:    var(--primary) at 15% opacity, text var(--primary)
Accent badge:  var(--accent) at 15% opacity, text var(--accent)
```

### Data tables
```
Border radius: 0 (none) — sharp, data-dense feel
Row hover:     bg var(--card-alt)
Header:        bg var(--card), text var(--muted), font Caption (12px, 500)
Border:        1px solid var(--border) between rows, not around cells
```

---

## 7. Interactive States

**EVERY interactive element MUST have ALL of these states defined:**

| Element  | Default | Hover                       | Focus                    | Active       | Loading              | Empty / Disabled     |
|----------|---------|-----------------------------|--------------------------|--------------|----------------------|----------------------|
| Button   | normal  | scale(1.02) + brightness    | ring 2px var(--ring)     | scale(0.98)  | spinner + opacity .7 | opacity .4, no-ptr   |
| Input    | normal  | border var(--primary)/50%   | ring 2px, border primary | —            | —                    | bg muted, read-only  |
| Card     | normal  | border-color var(--primary) | outline 2px var(--ring)  | —            | skeleton shimmer     | empty state + CTA    |
| Link     | normal  | underline + color primary   | outline 2px var(--ring)  | color accent | —                    | opacity .4           |
| Row      | normal  | bg var(--card-alt)          | outline var(--ring)      | bg card-alt  | skeleton row         | opacity .5           |

Empty states: every list/table/feed MUST have a designed empty state (icon + message + CTA).
Loading states: use skeleton shimmer, NOT spinner unless action-triggered (e.g. form submit).

---

## 8. Animation / Transitions

Philosophy: purposeful, not decorative. Each animation explains state, not decorates.

```
Base transition: 150ms ease
Hover effects:   scale(1.02) + brightness(1.05) — buttons; border-color shift — cards
Fade in:         opacity 0 → 1, 200ms ease-out (page elements, panels)
Slide up:        translateY(8px) → 0, 200ms ease-out (modals, toasts, command palette)
Skeleton:        shimmer gradient 1.5s infinite linear (loading states)
List stagger:    50ms delay between items (not all-at-once)
```

NEVER: random animations, decorative parallax, transitions > 300ms on interactive elements.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; }
}
```

---

## 9. Accessibility

Contrast requirements:
- Body text (`--foreground` on `--background`): `#f1f5f9` on `#0f172a` → ~14:1 (far exceeds AA)
- Muted text (`--muted` on `--background`): `#64748b` on `#0f172a` → verify ≥ 4.5:1
- Primary action (`--primary-fg` on `--primary`): white on indigo → verify ≥ 4.5:1
- Check with: https://webaim.org/resources/contrastchecker/

Keyboard navigation:
- ALL interactive elements reachable via Tab
- Focus ring: 2px solid var(--ring), offset 2px — always visible on dark bg
- Skip-to-content link as first element in `<body>`

ARIA:
- All icons conveying meaning: `aria-label` or `aria-labelledby`
- Decorative icons: `aria-hidden="true"`
- Form inputs: explicit `<label>` or `aria-label`
- Dynamic content updates: `aria-live="polite"` or `"assertive"`
- Modals: `role="dialog"`, `aria-modal="true"`, focus trap on open

Touch targets: minimum 44×44px on mobile — pad small buttons, don't reduce them.

---

## 10. Format Declaration

```
Component library: shadcn/ui (copy-paste, owned by the project)
CSS framework:     Tailwind CSS 4 (CSS variables, NOT Tailwind v3 dark: prefixes)
Token system:      CSS custom properties on :root and .dark
Icon set:          Lucide Icons (tree-shakeable, consistent 1.5px stroke width)
```

CSS variables setup in `src/globals.css`:
```css
:root {
  --background:        248 250 252;   /* #f8fafc */
  --foreground:        15 23 42;      /* #0f172a */
  --card:              255 255 255;   /* #ffffff */
  --card-alt:          241 245 249;   /* #f1f5f9 */
  --primary:           99 102 241;    /* #6366f1 */
  --primary-foreground: 255 255 255;
  --muted:             148 163 184;   /* #94a3b8 */
  --accent:            34 211 238;    /* #22d3ee */
  --destructive:       239 68 68;     /* #ef4444 */
  --border:            226 232 240;   /* #e2e8f0 */
  --ring:              99 102 241;    /* #6366f1 */
}

.dark {
  --background:        15 23 42;      /* #0f172a */
  --foreground:        241 245 249;   /* #f1f5f9 */
  --card:              30 41 59;      /* #1e293b */
  --card-alt:          38 51 72;      /* #263348 */
  --primary:           129 140 248;   /* #818cf8 */
  --primary-foreground: 255 255 255;
  --muted:             100 116 139;   /* #64748b */
  --accent:            34 211 238;    /* #22d3ee */
  --destructive:       248 113 113;   /* #f87171 */
  --border:            30 41 59;      /* #1e293b */
  --ring:              129 140 248;   /* #818cf8 */
}
```

---

> Be a human designer so it doesn't look like AI. With design taste.
