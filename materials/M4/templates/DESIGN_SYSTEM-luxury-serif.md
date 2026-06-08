# DESIGN_SYSTEM.md

> Design system: luxury-serif
> Aesthetic: premium, editorial, generous whitespace, sophisticated palette
> Format: shadcn/ui + Tailwind CSS 4 + CSS variables
> Last updated: 2026-05-03

---

## 1. Color Palette

Semantic roles (используй эти имена в коде, не сырой hex):

| Role             | Light mode            | Dark mode (optional)  | Hex (light)  | Notes                          |
|------------------|-----------------------|-----------------------|--------------|--------------------------------|
| `--background`   | Warm off-white        | Deep charcoal         | `#fafaf7`    | Not pure white — intentional warmth |
| `--foreground`   | Deep charcoal         | Warm off-white        | `#1c1917`    | Stone-900 tone, not pure black |
| `--card`         | Pure white            | Dark surface          | `#ffffff`    | Slight lift from warm bg       |
| `--card-alt`     | Light warm gray       | Elevated surface      | `#f5f4f0`    | Nested sections, alt bg        |
| `--primary`      | Deep navy             | Warm gold             | `#1a1a2e`    | Anchor color — confident, not playful |
| `--primary-fg`   | Warm white            | Deep navy             | `#fafaf7`    | Text on primary bg             |
| `--muted`        | Warm gray             | Muted surface text    | `#78716c`    | Stone-500 — not cool-gray     |
| `--accent`       | Antique gold          | Antique gold          | `#d4af37`    | Sparingly — CTA highlights, prices, marks |
| `--accent-fg`    | Deep charcoal         | Deep charcoal         | `#1c1917`    | Text on gold backgrounds       |
| `--destructive`  | Muted crimson         | Muted crimson         | `#b91c1c`    | Restrained, not neon red       |
| `--border`       | Warm hairline         | Subtle border         | `#e7e5e0`    | 0.5-1px, barely visible        |
| `--ring`         | Deep navy             | Warm gold             | `#1a1a2e`    | Focus ring matches primary     |

Dark mode strategy: optional — luxury products often ship light-only.
If dark mode needed: shift to deep `#1a1005` (warm dark brown) as background,
not cold slate. Warmth must persist across modes.

Gold accent rationale: gold (`#d4af37`) used SPARINGLY — price callouts, premium
badges, featured section markers. Not as a primary action color.

---

## 2. Typography

Font family (display): **Playfair Display** — editorial serif for headings
Font family (body): **Inter** — neutral sans-serif for body text at small sizes only
Alternative pairing: **Cormorant Garamond** (display) + **Lato** (body)

<!-- Typography is the primary differentiator in luxury UI.
     The serif headings do the heavy lifting; body font stays neutral and readable. -->

Imports:
```
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&display=swap')
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap')
```

Mono font: **IBM Plex Mono** — for product codes, SKUs, references

Scale:

| Step    | Size  | Font         | Line-height | Letter-spacing | Weight | Usage                  |
|---------|-------|--------------|-------------|----------------|--------|------------------------|
| Display | 80px  | Playfair     | 1.05        | -0.01em        | 700    | Hero, campaign headline|
| H1      | 60px  | Playfair     | 1.1         | 0em            | 700    | Page title             |
| H2      | 48px  | Playfair     | 1.15        | 0.01em         | 600    | Section header         |
| H3      | 36px  | Playfair     | 1.25        | 0.01em         | 600    | Card header, sub-hero  |
| H4      | 24px  | Playfair     | 1.3         | 0.01em         | 500    | Feature title          |
| Body    | 18px  | Inter        | 1.7         | 0              | 300    | Main content — generous|
| Small   | 15px  | Inter        | 1.6         | 0              | 400    | Secondary text         |
| Caption | 12px  | Inter        | 1.4         | 0.08em         | 400    | Labels, metadata — spaced out |
| Mono    | 13px  | IBM Plex     | 1.6         | 0              | 400    | Product codes, refs    |

Tracking rationale: slight positive tracking (+0.01em) on display headings creates
"openness" and breathing room characteristic of luxury print design.
Caption text also spaced out (0.08em) — classic premium typographic treatment.

Body size is 18px (not 16px) — luxury products prioritize readability and spaciousness
over information density.

---

## 3. Spacing Scale

Luxury design uses generous spacing — whitespace IS the design.

```
8px  — micro (icon + label, badge inner)
16px — xs   (tight inline gaps only)
24px — sm   (component inner padding, minimal)
48px — md   (card padding, standard sections)
72px — lg   (between sections — generous)
96px — xl   (major section breaks)
128px — 2xl (hero sections, full-bleed areas)
192px — 3xl (grand reveal sections, luxury editorial)
```

Tailwind config (tailwind.config.ts):
```js
spacing: {
  '0.5': '8px',
  '1':   '16px',
  '2':   '24px',
  '3':   '48px',
  '4':   '72px',
  '6':   '96px',
  '8':   '128px',
  '12':  '192px',
}
```

NEVER cramped padding. If a section feels "full" — add more whitespace.
Whitespace communicates confidence and exclusivity.

---

## 4. Border Radius Scale

Luxury uses slightly larger radii — soft, approachable, not utilitarian.

```
none: 0px     — editorial tables, structured data only
sm:   4px     — small tags, fine details
md:   8px     — metadata badges
lg:   16px    — inputs, secondary buttons
xl:   24px    — cards (default)
2xl:  32px    — modals, feature panels
full: 9999px  — primary CTA buttons, avatars, pills
```

Full-radius primary buttons are a luxury convention — they signal confidence
and distinguish primary actions clearly from secondary.

---

## 5. Elevation / Shadow Approach

**Philosophy: Subtle layered shadows are permitted — luxury context allows depth.**

Shadows in luxury design should feel like soft light, not hard edges.
Layer multiple soft shadows for realistic depth.

```css
--shadow-xs: 0 1px 2px rgba(28,25,23,0.04);
--shadow-sm: 0 2px 8px rgba(28,25,23,0.06), 0 1px 3px rgba(28,25,23,0.04);
--shadow-md: 0 8px 24px rgba(28,25,23,0.08), 0 2px 8px rgba(28,25,23,0.05);
--shadow-lg: 0 24px 48px rgba(28,25,23,0.10), 0 8px 16px rgba(28,25,23,0.06);
```

Elevation mapping:
- **Page (`--background`):** no shadow
- **Card (`--card`):** `--shadow-sm` — gentle lift
- **Modals / drawers:** `--shadow-lg` — full depth, center of attention
- **Floating tooltips:** `--shadow-md`

NEVER use pure black (`rgba(0,0,0,...)`) for shadows on warm-toned designs.
Use the foreground color with low opacity (`rgba(28,25,23,...)`) to keep warmth.

---

## 6. Component Patterns

### Cards
```
Background:    var(--card)
Padding:       48px (md in luxury scale)
Border radius: 24px (xl)
Border:        1px solid var(--border) — hairline, barely visible
Shadow:        var(--shadow-sm)
Hover:         shadow transitions to --shadow-md, 200ms ease
```

### Buttons
```
Primary:   bg var(--primary), text var(--primary-fg), radius 9999px (full)
           px 32px, py 14px, font-size 15px, letter-spacing 0.04em, weight 500
           Hover: bg shift to navy/80%, transition 200ms ease
           Use: sparingly — 1 primary CTA per screen
Secondary: bg transparent, border 1px var(--border), text var(--foreground)
           radius 9999px (full), px 28px
           Hover: bg var(--card-alt), border-color var(--primary), transition 200ms
Accent:    bg var(--accent), text var(--accent-fg), radius 9999px
           Use: price CTA, featured product
Ghost:     bg transparent, no border, text var(--muted), underline on hover
Disabled:  opacity 0.35, cursor not-allowed
```

### Inputs
```
Background:    transparent
Border-bottom: 1px solid var(--border) — underline style only, no box
Border radius: 0
Padding:       12px 0
Focus:         border-bottom-color var(--primary), transition 200ms
Placeholder:   var(--muted), font-style italic
Label:         above input, Caption size (12px, 0.08em tracking), var(--muted)
```

### Badges / Tags
```
Style:         outlined, not filled — more refined
Padding:       4px 12px
Border radius: 9999px (full)
Border:        1px solid var(--border)
Font:          11px, weight 400, letter-spacing 0.06em, UPPERCASE
Color:         var(--muted)
Gold variant:  border var(--accent), text var(--accent) — for "Premium", "Featured"
```

### Modals / Drawers
```
Background:    var(--card)
Border radius: 32px (top corners for bottom sheet, or all for center modal)
Padding:       48px
Shadow:        var(--shadow-lg)
Backdrop:      rgba(28,25,23,0.4) — warm, not cold black
```

---

## 7. Interactive States

**EVERY interactive element MUST have ALL of these states defined:**

| Element  | Default   | Hover                        | Focus                         | Active            | Loading              | Empty / Disabled      |
|----------|-----------|------------------------------|-------------------------------|-------------------|----------------------|-----------------------|
| Button   | normal    | bg shift, 200ms              | ring 2px var(--ring), offset 3px | opacity .85, 100ms | spinner, opacity .6 | opacity .35, no-ptr   |
| Input    | underline | border-color brightens       | border-color var(--primary)   | —                 | —                    | opacity .4, read-only |
| Card     | shadow-sm | shadow-md transition         | outline 2px var(--ring)       | shadow-xs         | content skeleton     | empty + invite text   |
| Link     | normal    | underline, color var(--primary) | outline 2px var(--ring)    | opacity .75       | —                    | opacity .35           |

Empty states: use elegant editorial copy + single subtle illustration or icon.
No "No data found" — write as if a human copywriter wrote it: «Your collection awaits.»

Loading states: skeleton with warm gradient shimmer (not cold gray).
Skeleton shimmer colors: `#f5f4f0` → `#e7e5e0` → `#f5f4f0` — matches warm palette.

---

## 8. Animation / Transitions

Philosophy: smooth and unhurried. Luxury does not rush.

```
Base transition: 200ms ease
Hover effects:   shadow lift (cards), bg tint shift (buttons), underline (links)
Fade in:         opacity 0 → 1, 300ms ease-out — slower than tech aesthetic
Slide up:        translateY(16px) → 0, 350ms cubic-bezier(0.16,1,0.3,1) (spring feel)
Modals:          scale(0.96) + opacity 0 → scale(1) + opacity 1, 300ms ease-out
Page transitions: fade 250ms (if using Next.js App Router transitions)
Skeleton shimmer: 2s infinite (slower than tech — relaxed cadence)
```

NEVER: snap transitions, aggressive scaling, anything that feels energetic or rushed.
The pace of animation reflects the pace of the brand.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; }
}
```

---

## 9. Accessibility

Contrast requirements:
- Body text (`--foreground` on `--background`): `#1c1917` on `#fafaf7` → ~17:1 (far exceeds AA)
- Muted text (`--muted` on `--background`): `#78716c` on `#fafaf7` → verify ≥ 4.5:1
- Gold accent (`--accent` on `--card`): `#d4af37` on `#ffffff` → may fail AA at small sizes
  → Use gold only for decorative or large text (≥18px), not small body copy
- Check with: https://webaim.org/resources/contrastchecker/

Keyboard navigation:
- ALL interactive elements reachable via Tab
- Focus ring: 2px solid var(--ring) offset 3px — slightly generous for the aesthetic
- Skip-to-content link as first element in `<body>`
- Underline-style inputs must show a clear focus state (color change + possibly outline)

ARIA:
- Decorative serif ornaments / dividers: `aria-hidden="true"`
- Image-heavy product cards: meaningful `alt` text, not "product image"
- Gold "Premium" badges: ensure they add context via `aria-label` if conveying info
- Modals: `role="dialog"`, `aria-modal="true"`, focus trap on open, return focus on close

Touch targets: minimum 44×44px. Full-radius pill buttons naturally satisfy this.

---

## 10. Format Declaration

```
Component library: shadcn/ui (copy-paste, owned by the project)
CSS framework:     Tailwind CSS 4 (CSS variables, warm custom palette)
Token system:      CSS custom properties on :root (light-mode primary)
Icon set:          Lucide Icons (use sparingly — luxury uses minimal iconography)
```

CSS variables setup in `src/globals.css`:
```css
:root {
  --background:        250 250 247;   /* #fafaf7 — warm off-white */
  --foreground:        28 25 23;      /* #1c1917 — stone-900 */
  --card:              255 255 255;   /* #ffffff */
  --card-alt:          245 244 240;   /* #f5f4f0 */
  --primary:           26 26 46;      /* #1a1a2e — deep navy */
  --primary-foreground: 250 250 247;  /* warm white */
  --muted:             120 113 108;   /* #78716c — stone-500 */
  --accent:            212 175 55;    /* #d4af37 — antique gold */
  --accent-foreground: 28 25 23;      /* dark on gold */
  --destructive:       185 28 28;     /* #b91c1c — muted crimson */
  --border:            231 229 224;   /* #e7e5e0 — warm hairline */
  --ring:              26 26 46;      /* #1a1a2e — matches primary */
}
```

---

> Be a human designer so it doesn't look like AI. With design taste.
