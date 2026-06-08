# Anti-AI-slop guards: блок Design Principles для CLAUDE.md

> **Когда использовать:** Вставить в `CLAUDE.md` или `DESIGN_SYSTEM.md` один раз — и ИИ перестаёт генерировать «дефолтный shadcn» в каждом новом компоненте. Работает в Claude Code, Cursor, Lovable, Bolt.
> **Inputs:** ничего, это системный промпт-блок. Paste в файл, не в чат.
> **Output:** стабильные guard-rails на весь проект: Inter исчезает, фиолетовые градиенты исчезают, двухколоночные шаблоны исчезают.

## Промпт

```
## Design Principles (always apply)

Be a human designer so it doesn't look like AI. With design taste.

- Generous spacing — plenty of whitespace, never cramped.
  Use only 8/16/24/32/48/64px. NEVER arbitrary values like 14px or 18px.
- Cards — subtle elevation via background contrast, consistent padding (24px),
  NEVER heavy 2px borders. Border: 1px solid at 10% opacity max.
- Typography — clean, intentional scale jumps with tracking-tight on headings.
  Font: [YOUR CHOICE — Manrope / Geist / Space Grotesk / Playfair Display].
  NOT default Inter — overused to the point of invisibility.
- NO box shadows by default. Depth from background contrast:
  3 levels only — page bg / card bg / card-alt bg.
- Interactive states — EVERY interactive element MUST have:
  hover, focus, active, loading, empty, error states.
  List them explicitly, do not skip.
- Visual hierarchy — clear structure with proper heading levels.
  H1 → H2 → H3 → body — never skip levels, never use bold as heading substitute.
- Spacing units — only 8px, 16px, 24px, 32px (no arbitrary values).
- Dark mode — CSS variables only: --bg, --fg, --card, --border.
  NEVER Tailwind dark: prefixes (dark:bg-gray-900 is not dark mode, it's a hack).
- Colors — semantic tokens only: var(--primary), var(--accent), var(--muted).
  NEVER raw hex or Tailwind color utilities (text-blue-600) as brand color.
- Animations — purposeful only: hover states, page transitions, skeleton loaders.
  NO decorative fade-in on static content. NO random all-at-once animations.
  Elements arrive in sequence with 50-100ms stagger (Apple-style).
- Layout — no AI-default structures:
  no 2-column "before/after" comparison blocks,
  no hero + 3 symmetric card grid as default,
  no footer with 4 equal columns,
  no cringe gradients (linear-gradient purple/violet on hero).
- Buttons — purposeful labels only. NO "Click here", NO "Learn more".
  Every button label describes the action: "Start free trial", "Export CSV".
```

## Объяснение

AI-модели при генерации UI смещаются к «среднему» по обучающим данным — наиболее частым паттернам из тысяч GitHub-репо и туториалов. Это и есть «AI slop»: Inter (дефолт shadcn/ui), синяя или фиолетовая кнопка (`text-blue-600`), толстые границы на каждой карточке, два симметричных блока «было/стало», `shadow-lg` рефлекторно, dark mode через `dark:bg-gray-900`. Модель не делает это намеренно — она делает то, что встречала чаще всего.

Механика guard-rails: чем точнее описал что нельзя, тем меньше остаётся места для «усреднённой» выдачи. Фраза «Be a human designer so it doesn't look like AI» — не поэзия, а семантический якорь. Слово «human» в контексте дизайна контрастирует с AI-клише в обучающих данных: модель получает сигнал искать примеры с высоким рейтингом качества, а не просто частотные. «With design taste» усиливает это смещение.

Блок рассчитан на вставку в `CLAUDE.md` один раз — он будет работать для всех последующих промптов автоматически через механизм Writing-типа (M2). Не нужно вставлять его в каждый чат-промпт. Агент видит его как часть системного контекста проекта.

## Вариации

**Вариация A — минимальная версия (quick-start, 5 строк):**

```
## Design Principles

Be a human designer so it doesn't look like AI. With design taste.
Font: Manrope (NOT Inter). Spacing: 8/16/24/32px only. No box shadows.
Dark mode via CSS variables only. Every interactive element has hover+focus+loading states.
No 2-column comparison layouts. No cringe gradients. No generic shadcn out-of-box.
```

**Вариация B — только запреты (для Lovable, paste в первый промпт):**

```
Design constraints (hard rules, never violate):
- NO Inter font. Use Manrope or Geist.
- NO linear-gradient purple/violet on hero sections.
- NO 2-column "pros vs cons" or "before/after" comparison blocks.
- NO shadow-lg on every card. Use background contrast for depth.
- NO dark:bg-gray-900. Use CSS variables for dark mode.
- NO "Click here" or "Learn more" button labels.
- NO all-elements-fade-in-at-once animations.
Be a human designer so it doesn't look like AI. With design taste.
```

**Вариация C — pre-flight checklist (paste перед каждым UI-промптом):**

```
Pre-flight UI check — verify before generating:
[ ] All colors use CSS variables (var(--primary), not #6366f1)
[ ] No box shadows — depth from bg contrast: page → card → card-alt
[ ] Typography scale explicitly stated with pixel values
[ ] Card pattern defined once, applied consistently
[ ] Mobile layout specified (breakpoints in the prompt)
[ ] Dark mode via CSS variables, not dark: prefixes
[ ] No "click here" — every button has purposeful label
[ ] All interactive states listed: hover / focus / active / loading / empty
```

## Контекст

Каждое правило выше — это устранение конкретного паттерна generic «AI-look»: дефолтный Inter, фиолетовые градиенты, лишние shadow-lg, cringe-emoji вместо иконок и т.д. Принцип «be a human designer with design taste» работает только если в промпте явно перечислены guard-rails — иначе модель скатывается к среднему по обучающим данным.

## Связь с курсом

Блок M4 F9 — «12 признаков AI-look и как их устранить». Каждый из 12 guard-rails в промпте напрямую закрывает один паттерн из таблицы F9. Механика — Writing-тип из M2 (Kung Fu Context): правила записаны статически, агент видит их в каждом сеансе без повторного объяснения.
