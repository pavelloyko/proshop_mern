# CLAUDE.md

> Project: [название проекта]
> Stack: Next.js 15, shadcn/ui, Tailwind CSS 4, TypeScript
> Last updated: [YYYY-MM-DD]

---

## Design rules: see ./DESIGN_SYSTEM.md

When generating any UI component, modifying styles, or touching anything visual:

1. **Read `./DESIGN_SYSTEM.md` before writing code** — every time, not from memory.
2. Use only colors defined as CSS variables — **never raw hex** (`var(--primary)`, not `#6366f1`).
3. Follow spacing scale from §3 — **multiples of 8px only**, no arbitrary values.
4. Implement all interactive states from §7 — hover, focus, loading, empty — for every element.
5. Font: **Manrope** (§2) — never Inter, never system-ui as primary.
6. Elevation: **no box shadows** by default — depth from background contrast only (§5).
7. Dark mode via CSS variables and `.dark` class — **never `dark:bg-gray-900`** hardcoded.

---

## shadcn pipeline: see ./docs/shadcn-pipeline.md

When adding or modifying shadcn/ui components:

1. Check `./docs/shadcn-pipeline.md` for the project's component conventions.
2. Use shadcn add `<component>` — do not copy-paste from the internet.
3. After adding: verify the component uses CSS variables, not hardcoded Tailwind classes.
4. Components live in `src/components/ui/` — owned by the project, modify freely.

---

## UI reviewer subagent: see .claude/agents/ui-expert.md

For auditing and enforcing design system compliance:

- **Review mode** (read-only): call when you want a list of violations without changing code.
- **Enforce mode** (auto-fix): call after major refactors or before releases.
- Trigger: `/loop` on schedule, or manually: "run ui-expert in review mode".
- The subagent checks against `./DESIGN_SYSTEM.md` — keep that file current.

Common violations it catches:
- Raw hex colors instead of CSS variables
- Arbitrary spacing (not multiples of 8px)
- Wrong font (Inter instead of Manrope)
- Missing hover / focus / loading / empty states
- `shadow-lg` where elevation should be bg contrast only
- Missing ARIA labels on interactive elements

---

## Anti-AI-slop guards

<!-- Cross-ref M2 (Kung Fu Context — Writing type):
     This section is the "rules-as-context" layer for design generation.
     Full guard catalog: ./prompts/anti-ai-slop-guards.md -->

**Hard bans — never generate these:**
- Inter as the project font — use Manrope
- Purple/teal gradients as hero backgrounds — use solid `--background`
- `shadow-lg` on cards without explicit reason — use bg contrast elevation
- Two-column "Feature A vs Feature B" comparison blocks — use custom layouts
- Generic "Get started today" CTA copy — write specific, purposeful labels
- `dark:bg-gray-900` as dark mode — use CSS variables only
- `text-blue-600` as an accent — use `var(--primary)` or `var(--accent)`

**Required for every component:**
- All interactive states (hover, focus, active, loading, empty)
- Minimum 44×44px touch targets on mobile
- `aria-label` on all icon-only buttons
- `aria-hidden="true"` on decorative icons

**Voice for UI copy:**
- Direct and functional — no exclamation marks in labels
- No "Click here" links — every link describes its destination
- Empty states: specific helpful message + one clear action

> Be a human designer so it doesn't look like AI. With design taste.

---

## Context reference: M2 Kung Fu Context (Writing type)

This `CLAUDE.md` is a **Writing-type** context artifact (M2 framework).
`DESIGN_SYSTEM.md` is also Writing-type — design rules statically encoded for every prompt.

Both files belong to the same context engineering pattern:
```
CLAUDE.md          ← rules for AI behavior (M2)
AGENTS.md          ← symlink to CLAUDE.md, cross-tool
.cursorrules       ← rules for Cursor (M2)
DESIGN_SYSTEM.md   ← rules for design (M4) — this project
```

When context gets large: `/compact focus:ui-implementation` before major UI tasks.
When starting a new component: open a sub-agent session to isolate context.

---

## Project structure

```
project-root/
├── CLAUDE.md                  ← this file
├── AGENTS.md                  ← symlink to CLAUDE.md
├── DESIGN_SYSTEM.md           ← design rules (read before any UI work)
├── src/
│   ├── app/                   ← Next.js App Router
│   ├── components/
│   │   └── ui/                ← shadcn/ui components (owned, modify freely)
│   └── globals.css            ← CSS variables from DESIGN_SYSTEM.md tokens
├── docs/
│   └── shadcn-pipeline.md     ← component conventions
└── .claude/
    └── agents/
        └── ui-expert.md       ← UI reviewer / enforcer subagent
```

---

## What NOT to do

- Do not start writing code before reading `DESIGN_SYSTEM.md`.
- Do not use `npx create-shadcn-ui@latest` to add multiple components at once — add one at a time.
- Do not run `npm run dev` as part of code generation — the user handles local dev.
- Do not create new CSS utility classes — use Tailwind + CSS variables only.
- Do not commit media files (.mov, .mp4, .mp3) — they are in .gitignore.
