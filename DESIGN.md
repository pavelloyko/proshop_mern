# DESIGN.md — ProShop Design System

> Design system: Minimal Tech (dark-first)
> Aesthetic: dark, functional, generous whitespace, restrained palette
> Stack: React 16 + React-Bootstrap 1 + CSS custom properties (variables)
> Last updated: 2026-05-15
> Reference aesthetic: Linear, Vercel dashboard, Raycast

---

## 1. Color Palette

Semantic roles — use CSS variable names in code, never raw hex.

| Role               | Dark mode (default) | Light mode          | Hex (dark)   |
|---------------------|---------------------|---------------------|--------------|
| `--bg`              | Page background     | Page background     | `#0f172a`    |
| `--fg`              | Primary text        | Primary text        | `#f8fafc`    |
| `--card`            | Card surface        | Card surface        | `#1e293b`    |
| `--card-alt`        | Elevated card       | Elevated card       | `#263348`    |
| `--primary`         | Primary action      | Primary action      | `#818cf8`    |
| `--primary-fg`      | Text on primary bg  | Text on primary bg  | `#ffffff`    |
| `--muted`           | Muted text, hints   | Muted text, hints   | `#94a3b8`    |
| `--accent`          | Cyan highlight      | Cyan highlight      | `#22d3ee`    |
| `--destructive`     | Error, danger       | Error, danger       | `#fca5a5`    |
| `--success`         | Enabled / OK        | Enabled / OK        | `#6ee7b7`    |
| `--warning`         | Testing / caution   | Testing / caution   | `#fcd34d`    |
| `--border`          | Borders, dividers   | Borders, dividers   | `#334155`    |
| `--ring`            | Focus ring          | Focus ring          | `#a5b4fc`    |

Light mode variant:
- `--bg`: `#f8fafc` / `--fg`: `#0f172a` / `--card`: `#ffffff`
- `--card-alt`: `#f1f5f9` / `--primary`: `#6366f1` / `--muted`: `#94a3b8`
- `--border`: `#e2e8f0`

Dark mode strategy: CSS variables on `:root`. Light mode via `[data-theme="light"]` or `.light` class.
NEVER use inline `dark:bg-gray-900` or hardcoded color values.

---

## 2. Typography

Font family: **Manrope** (NOT Inter)
Fallback: `system-ui, -apple-system, sans-serif`
Import: `@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap')`

Mono font: **JetBrains Mono** — for code, data values, timestamps
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

---

## 3. Spacing Scale

Strict multiples of 8px only. No arbitrary values.

```
4px  — micro (icon + label gap)
8px  — xs  (tight padding)
16px — sm  (component inner padding)
24px — md  (card padding, section gaps)
32px — lg  (section padding)
48px — xl  (between major sections)
64px — 2xl (page-level spacing)
96px — 3xl (hero sections)
```

NEVER use padding/margin with values like 14px, 18px, 22px.

---

## 4. Border Radius Scale

```
none: 0px     — tables, data grids
sm:   4px     — badges, chips, code blocks
md:   8px     — buttons, inputs (default)
lg:   12px    — cards (default)
xl:   16px    — modals, popovers
full: 9999px  — pills, avatars, toggle switches
```

---

## 5. Elevation / Shadow Approach

**Philosophy: NO box shadows by default. Depth from background contrast.**

3-level elevation system:
- **Level 0 (page):** `--bg` (`#0f172a`)
- **Level 1 (card):** `--card` (`#1e293b`) — subtle lift via background color
- **Level 2 (card-alt / floating):** `--card-alt` (`#263348`) — modals, dropdowns

Exception — shadows only for dropdown menus and tooltips:
```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.35), 0 1px 2px rgba(0,0,0,0.25);
--shadow-md: 0 4px 6px -1px rgba(0,0,0,0.35), 0 2px 4px -1px rgba(0,0,0,0.25);
```

NEVER use `shadow-lg` reflexively.
NEVER use thick borders (2px+) for visual separation.

---

## 6. Component Patterns

Adapted for React-Bootstrap 1 + CSS variables. Override Bootstrap defaults via CSS.

### Cards
```
Background:    var(--card)
Padding:       24px
Border radius: 12px
Border:        1px solid var(--border)
Hover:         border-color → var(--primary), transition 150ms ease
```

### Buttons
```
Primary:   bg var(--primary), text var(--primary-fg), radius 8px
           px 16px py 8px
           Hover: brightness(1.15), transition 150ms
Secondary: bg transparent, border 1px var(--border), text var(--fg)
           Hover: bg var(--card), transition 150ms
Danger:    bg var(--destructive), text white
Ghost:     bg transparent, no border, text var(--muted)
           Hover: text var(--fg), bg var(--card)
Disabled:  opacity 0.4, cursor not-allowed
```

### Inputs
```
Background:    var(--bg)
Border:        1px solid var(--border)
Border radius: 8px
Padding:       8px 16px
Focus:         border-color var(--ring), box-shadow 0 0 0 2px rgba(129,140,248,0.2)
Placeholder:   var(--muted)
```

### Badges / Status Chips
```
Padding:       4px 12px
Border radius: 9999px (full)
Font:          12px, weight 500
Enabled:       bg var(--success)/15%, text var(--success)
Testing:       bg var(--warning)/15%, text var(--warning)
Disabled:      bg var(--muted)/15%, text var(--muted)
```

### Data Tables
```
Border radius: 0 (none) — sharp, data-dense feel
Row hover:     bg var(--card-alt)
Header:        bg var(--card), text var(--muted), font Caption (12px, 500)
Border:        1px solid var(--border) between rows
```

### Toggle Switch
```
Width:         48px, Height: 24px
Track:         var(--muted) off, var(--primary) on
Thumb:         white, radius full, translateX on toggle
Transition:    200ms ease
```

### Slider (Traffic %)
```
Track:         var(--card-alt), height 8px, radius 4px
Fill:          var(--primary)
Thumb:         white, 20px circle, border 2px var(--primary)
Focus:         ring 2px var(--ring)
```

---

## 7. Interactive States

**EVERY interactive element MUST have ALL of these states (5 mandatory):**

| Element  | Default | Hover                    | Focus                   | Active       | Loading              | Empty / Disabled       | Success               |
|----------|---------|--------------------------|-------------------------|--------------|----------------------|------------------------|-----------------------|
| Button   | normal  | brightness + scale(1.02) | ring 2px var(--ring)    | scale(0.98)  | spinner + opacity .7 | opacity .5, no-ptr     | checkmark flash 600ms |
| Input    | normal  | border brighter          | ring 2px, border ring   | —            | —                    | bg muted, read-only    | border success 600ms  |
| Card     | normal  | border-color primary     | outline ring            | —            | skeleton shimmer     | empty state + CTA      | border flash success  |
| Link     | normal  | underline + color primary| outline ring            | color accent | —                    | opacity .5             | —                     |
| Row      | normal  | bg var(--card-alt)       | outline ring            | bg card-alt  | skeleton row         | opacity .5             | bg success/5% flash   |
| Toggle   | normal  | brightness(1.1)          | ring 2px var(--ring)    | scale(0.95)  | —                    | opacity .5             | track pulse 300ms     |
| Slider   | normal  | thumb scale(1.1)         | ring 2px var(--ring)    | thumb scale(1.15) | —                | opacity .5             | fill pulse 300ms      |

**Success state** — brief visual confirmation after an action (toggle, slider, save). Duration: 300-600ms. Use `var(--success)` color flash on the element, then return to default. Example: toggle → track briefly pulses green, then settles to primary color.

**Disabled state contrast** — opacity minimum 0.5 (not 0.4). Disabled must be obvious but still readable. Never use low-contrast disabled states that become invisible on dark backgrounds.

**Micro-interactions (tap/press feedback):**
- Buttons: `active { transform: scale(0.98) }` — physical press feel
- Toggles: `active { transform: scale(0.95) }` on the thumb
- Cards: subtle background shift on active
- All transitions: GPU-accelerated properties only (`transform`, `opacity`)

Empty states: every list/table MUST have a designed empty state (icon + message + optional CTA).
Loading states: use skeleton shimmer, NOT spinner unless action-triggered (form submit).
Container with async content: add `aria-busy="true"` while loading, `aria-busy="false"` when done.

**Touch targets**: ALL interactive elements minimum 44×44px visible/clickable area.
For small visual elements (toggle thumb, slider thumb): pad the hit area with invisible padding
to reach 44×44px minimum while keeping the visual size small.

---

## 8. Animation / Transitions

Philosophy: purposeful, not decorative. GPU-accelerated properties only (`transform`, `opacity`).
NEVER animate `width`, `height`, `top`, `left`, `margin`, `padding` — causes layout reflow.

```
Base transition: 150ms ease
Hover effects:   brightness(1.1) + scale(1.02) — buttons; border-color shift — cards
Fade in:         opacity 0 → 1, 200ms ease-out
Slide up:        translateY(8px) → 0, 200ms ease-out
Skeleton:        shimmer gradient 1.5s infinite linear
List stagger:    50ms delay between items
```

NEVER: random animations, decorative parallax, transitions > 300ms.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. Accessibility

**Semantic HTML first, ARIA second.** Use `<nav>`, `<main>`, `<section>`, `<article>` before adding ARIA roles.

Contrast requirements:
- Body text on background: >= 4.5:1 (WCAG AA)
- `--fg` on `--bg`: `#f1f5f9` on `#0f172a` = ~14:1 (exceeds AA)
- `--muted` on `--bg`: `#64748b` on `#0f172a` = ~5.5:1 (passes AA)
- UI components / graphical objects: >= 3:1
- Disabled state: minimum opacity 0.5 — must remain readable on dark backgrounds
- Check with: https://webaim.org/resources/contrastchecker/

**Color is NOT the only visual indicator.** Status badges, state changes, and data categories
MUST use at least TWO of: color + icon + text label + shape. Example: status badge has
both a colored background AND a text label inside (not just a colored dot).

Skip-to-content link:
- First element in `<body>`: `<a href="#main-content" class="skip-link">Skip to content</a>`
- Hidden visually, visible on focus (keyboard Tab press)
- `#main-content` target: `<main id="main-content" tabindex="-1">`

Keyboard navigation:
- ALL interactive elements reachable via Tab
- Logical tab order: top to bottom, left to right
- Focus ring: 2px solid var(--ring), offset 2px — always visible, NEVER removed
- No keyboard traps — every component escapable via Escape or Tab
- Arrow keys: for within-component navigation (radio groups, menus, sliders)

ARIA:
- Every `<input>` has an associated `<label htmlFor>` (not just placeholder or aria-label alone)
- Icons conveying meaning: `aria-label` or `aria-labelledby`
- Decorative icons: `aria-hidden="true"`
- Loading containers: `aria-busy="true"` while loading, `aria-busy="false"` when done
- Dynamic content changes (filter results, counts): `aria-live="polite"` on the container
- Error messages: associated with inputs via `aria-describedby`
- Modals: `role="dialog"`, `aria-modal="true"`, focus trap on open
- Icon-only buttons: `aria-label` describing the action (e.g., "Close dialog", not "X")
- Toggle switches: `role="switch"`, `aria-checked="true/false"`
- Current page in nav: `aria-current="page"`

Touch targets: minimum 44×44px on mobile. Pad small visual elements with invisible
clickable area to reach 44×44px while keeping visual size compact.

Text scaling: must be readable and functional at 200% zoom without horizontal scroll or
content overlap. Body text minimum 16px for main content.

---

## 10. Format Declaration

```
UI framework:     React 16
Component lib:    React-Bootstrap 1 (override via CSS variables)
CSS approach:     CSS custom properties on :root + component-level overrides
Module system:    ES Modules (.js extensions in imports)
Icon set:         Inline SVG or Bootstrap Icons (already in project)
```

CSS variables setup in `frontend/src/index.css` (or a dedicated `theme.css`):
```css
:root {
  --bg:            #0f172a;
  --fg:            #f1f5f9;
  --card:          #1e293b;
  --card-alt:      #263348;
  --primary:       #6366f1;
  --primary-fg:    #ffffff;
  --muted:         #64748b;
  --accent:        #22d3ee;
  --destructive:   #f87171;
  --success:       #34d399;
  --warning:       #fbbf24;
  --border:        #1e293b;
  --ring:          #818cf8;
  --radius-sm:     4px;
  --radius-md:     8px;
  --radius-lg:     12px;
  --radius-xl:     16px;
  --transition:    150ms ease;
  --font:          'Manrope', system-ui, -apple-system, sans-serif;
  --font-mono:     'JetBrains Mono', monospace;
}

[data-theme="light"] {
  --bg:            #f8fafc;
  --fg:            #0f172a;
  --card:          #ffffff;
  --card-alt:      #f1f5f9;
  --muted:         #94a3b8;
  --border:        #e2e8f0;
}
```

---

## 11. Anti-AI-slop Guards (mandatory)

> This section covers ONLY rules NOT already enforced by sections 1-10.
> Sections 1-10 handle: font choice (#2), shadows (#5), dark mode (#1), animations (#8), interactive states (#7), semantic tokens (#1, #10). Do not duplicate those here.

### Magic phrase
> Be a human designer so it doesn't look like AI. With design taste.

### Layout & composition
- **NO 2-column comparison blocks.** Forbidden patterns: "Without us / With us", "Before / After", "Old way / New way" side-by-side. Use single-column storytelling or 3-card grid. If comparison is unavoidable — use a table, not two columns.
- **NO cookie-cutter layouts.** Avoid reflex patterns: hero + 3 symmetric card grid as default, footer with 4 equal columns. Layout serves content, not template.
- **ASCII wireframe first.** Before generating UI code: produce ASCII wireframe of the page layout (HERO / sections / cards / footer). Then generate code that matches the wireframe EXACTLY. Do not invent additional sections.
- **Generous spacing between sections.** Padding between major sections: minimum 48px on desktop, 32px on mobile. Section internal padding: minimum 24px. Never 12-16px between sections.
- **Mobile breakpoints explicitly stated.** Mobile <640px: stack to 1 column, 14px base. Tablet 640-1024: 2 columns. Desktop >1024: full layout.

### Visual style
- **NO gradients on backgrounds, buttons, or hero blocks.** Use solid colors only — from DESIGN.md tokens. Forbidden: `linear-gradient(135deg, #6366f1, #a855f7)` and similar. Single exception: skeleton loader shimmer animation.
- **Cards: subtle elevation, NEVER heavy borders.** Use `1px solid var(--border)` or `border: 1px solid color-mix(in srgb, var(--border) 10%, transparent)` or no border with background contrast. Forbidden: `border: 2px+`, `border: 3px solid black`, double borders.
- **React-Bootstrap MUST be customized.** Do not ship default Bootstrap theme (Bootstrap blue/gray/white). Override all colors with CSS variables from Section 10. Use Section 12 as the override reference.
- **Buttons — purposeful labels ONLY.** NO "Click here", NO "Learn more", NO "Submit". Every button describes the action: "Add to Cart", "Export CSV", "Toggle Feature".

### UX-first thinking
- **User journey before visual style.** Before generating any page — answer: (1) Who is on this page? (2) What are they trying to do? (3) Where is the primary CTA? (4) What is the next logical step? Visual decisions follow user journey, not the other way around.
- **Primary CTA must be above the fold.** Hero with full-screen height pushing content below fold = anti-pattern. Hero takes max 60vh, primary CTA visible without scroll on 1366x768 desktop.
- **Real content, no placeholders.** No Lorem ipsum — it hides UX problems. Real headings, real CTA text, real data from first iteration.

---

## 12. React-Bootstrap Override Strategy

Bootstrap components need dark-theme overrides. Apply globally in CSS:

```css
/* Body */
body { background: var(--bg); color: var(--fg); font-family: var(--font); }

/* Bootstrap Navbar */
.navbar { background: var(--card) !important; border-bottom: 1px solid var(--border); }
.navbar a { color: var(--fg) !important; }
.navbar a:hover { color: var(--primary) !important; }

/* Bootstrap Cards */
.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); color: var(--fg); }

/* Bootstrap Buttons */
.btn-primary { background: var(--primary); border-color: var(--primary); color: var(--primary-fg); border-radius: var(--radius-md); }
.btn-primary:hover { background: var(--primary); filter: brightness(1.15); }
.btn-secondary { background: transparent; border: 1px solid var(--border); color: var(--fg); border-radius: var(--radius-md); }
.btn-secondary:hover { background: var(--card); }

/* Bootstrap Tables */
.table { color: var(--fg); }
.table thead th { background: var(--card); color: var(--muted); border-color: var(--border); font-size: 12px; font-weight: 500; }
.table tbody tr:hover { background: var(--card-alt); }

/* Bootstrap Forms */
.form-control { background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: var(--radius-md); }
.form-control:focus { border-color: var(--ring); box-shadow: 0 0 0 2px rgba(129,140,248,0.2); background: var(--bg); color: var(--fg); }
.form-control::placeholder { color: var(--muted); }
```
