# Reverse-Design: скриншот → DESIGN_SYSTEM.md

> **Когда использовать:** Когда у тебя есть визуальный референс (Stripe, Linear, Apple, Mobbin) и ты хочешь не «описывать стиль словами», а получить машиночитаемую спецификацию дизайн-системы для своего проекта.
> **Inputs:** один или несколько скриншотов UI (paste в чат или attach-файл).
> **Output:** готовый `DESIGN_SYSTEM.md` в формате shadcn/ui + Tailwind CSS 4 + CSS variables — 7 разделов, copy-paste в корень репо.

## Промпт

```
[Attach: screenshot of Stripe / Linear / Apple / your reference]

You are a senior product designer. Analyze this screenshot in detail.
Create a DESIGN_SYSTEM.md file documenting:

1. Color palette (with hex/oklch values, semantic roles: bg, fg, primary,
   muted, accent, destructive, border, ring)
2. Typography (font family, weights, scale with pixel values, line-height,
   tracking)
3. Spacing scale (only multiples of 8px: 8/16/24/32/48/64)
4. Border radius scale
5. Elevation/shadow approach (or no-shadows philosophy)
6. Component patterns visible (cards, buttons, inputs)
7. Interactive states approach (hover/focus/active/loading/empty)

Format as shadcn/ui + Tailwind CSS 4 with CSS variables.
Provide actionable documentation that enables exact visual replication.
```

## Объяснение

Словесное описание стиля — «минималистичный», «премиальный», «как у Apple» — размыто по определению. У модели нет единственной правильной интерпретации этих слов, она будет угадывать, и угадает «по среднему» своих обучающих данных: Inter, синие кнопки, серые карточки. Скриншот даёт точную визуальную информацию: конкретные соотношения пространства, конкретный spacing, конкретный feel — то, что человек не смог бы сформулировать текстом даже при желании.

Промежуточный артефакт `DESIGN_SYSTEM.md` критичен. Он фиксирует стиль в машиночитаемом формате — и все последующие промпты работают с конкретными значениями. Ты пишешь «primary=#6366f1» один раз, а дальше в каждом промпте ссылаешься на `var(--primary)`. Правишь один токен — весь проект меняется. Это двухшаговый паттерн: сначала «понять стиль», потом «применить стиль». Делать оба шага в одном промпте («сделай как на картинке») резко снижает качество обоих.

Файл кладётся в корень репо рядом с `CLAUDE.md`. В `CLAUDE.md` добавляется одна строка: `## Design rules: see ./DESIGN_SYSTEM.md` — и теперь любой агент, читающий ваш проект, знает дизайн-систему до первого промпта. Так же как `CLAUDE.md` даёт агенту правила для логики кода, `DESIGN_SYSTEM.md` даёт ему правила для визуала.

## Вариации

**Вариация A — luxury / premium (serif-based):**

```
[Attach: screenshot of a luxury product — Bang & Olufsen, Loro Piana, Rolex web]

You are a senior product designer for a luxury brand.
Analyze this screenshot and create DESIGN_SYSTEM.md for a premium experience.

Visual direction: luxury / sophisticated / premium
Typography: favor serif or display fonts (Playfair Display, Fraunces, Cormorant)
           paired with clean sans-serif for body
Colors: muted, sophisticated palette — no bright saturated primaries
Spacing: generous, never cramped — whitespace IS the design
Shadows: layered, soft depth — not flat, not harsh
Borders: thin (0.5-1px), subtle — or none

Document all patterns with implementation-ready specifics.
Format: shadcn/ui + Tailwind CSS 4 + CSS variables.
```

**Вариация B — minimal-tech (SaaS dashboard style):**

```
[Attach: screenshot of Linear / Vercel / Raycast / Clerk]

Analyze this minimal tech design and extract DESIGN_SYSTEM.md.

Visual direction: minimal / functional / high-density data
Font: Geist or Manrope — no decorative elements, no Inter
Colors: dark background preferred, single accent color, semantic tokens only
Shadows: none — depth from background contrast only (3-level elevation)
Spacing: tight but intentional — 8px base unit
Border radius: minimal (4-8px), or sharp edges for brutalist variants

Every section must include both dark and light mode variants.
Format: shadcn/ui + Tailwind CSS 4 + CSS variables.
```

**Вариация C — editorial / brutalist:**

```
[Attach: screenshot of editorial or brutalist UI]

Extract DESIGN_SYSTEM.md for an editorial brutalist interface.

Visual direction: brutalist / editorial / raw
Typography: monospace or bold display — typography IS the design
Colors: high contrast — black/white + 1 bold accent maximum
Borders: thick, prominent (2-4px) — intentional, not generic
Shadows: none OR harsh offset drop-shadows (intentional brutalist style)
Spacing: irregular but intentional — sometimes asymmetric

Document as shadcn/ui + Tailwind CSS 4 + CSS variables.
Capture the intentional irregularities, not just the averages.
```

## Контекст

Двухшаговый паттерн извлечения дизайн-системы из скриншота — повторяющийся приём в практике vibe-coding 2026: сначала reverse-design prompt → DESIGN_SYSTEM.md, потом генерация UI с этим файлом в контексте.

## Связь с курсом

Блок M4 F7 — «DESIGN.md как 2026-стандарт». Этот промпт — практическая реализация паттерна Writing-типа из M2 (Kung Fu Context): ты статически кодируешь дизайн-правила в файл, который агент видит в каждом сеансе работы с UI.
