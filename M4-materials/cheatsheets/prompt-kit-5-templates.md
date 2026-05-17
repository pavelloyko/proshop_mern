# Cheatsheet: 5 готовых промптов

> Все 5 шаблонов в одном файле для быстрого copy-paste.
> Полные версии каждого (с объяснением и вариантами) — в `../prompts/`.

---

## 1. Reverse-design styleguide extraction

> Извлечь `DESIGN_SYSTEM.md` из скриншота референса (Stripe / Linear / Apple).
> Двухшаговый паттерн: сначала «понять стиль», потом «применить».
> Никогда «сделай как на картинке» напрямую — качество резко падает.

```
[Скриншот референса: Stripe / Linear / Apple продукт]

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

Полная версия + варианты: `../prompts/reverse-design-extract.md`

---

## 2. Anti-AI guard-rails (блок в CLAUDE.md / системный промпт)

> Вставляй в `CLAUDE.md` проекта или как первый системный блок.
> Работает потому что называет запрещённые паттерны по имени.

```markdown
## Design Principles (always apply)

- Generous spacing — plenty of whitespace, never cramped
- Cards — subtle elevation, consistent padding, NEVER heavy borders
- Typography — clean, intentional scale jumps with tracking-tight on headings
- NO box shadows by default — depth from background contrast (3 levels: page/card/card-alt)
- Interactive states — every interactive element has hover, focus, loading, empty states
- Visual hierarchy — clear structure with proper heading levels
- Spacing units — only 8px, 16px, 24px, 32px (no arbitrary values)
- NEVER generate generic AI patterns: 2-col comparison blocks, cringe gradients,
  default Inter, dark:bg-gray-900 as dark mode, "click here" buttons
- Be a human designer so it doesn't look like AI. With design taste.
```

Полная версия с токенами: `../prompts/anti-ai-slop-guards.md`

---

## 3. Lovable bring-your-vibe

> Стартовый промпт под Lovable. Определяет стиль ДО функциональности.
> Ключевое: один visual direction + реальный контент + component-by-component.

```
Build [feature description].

Visual direction: [premium / minimal / cinematic / brutalist / playful — pick ONE].

Style baseline:
- Reference screenshot: [paste OR link to inspiration]
- Font: [specific name — NOT default Inter]
- Color palette: [3-5 hex values OR OKLCH]
- Spacing scale: 8/16/24/32 only
- Border radius: [exact rem]
- Animations: [subtle scale on hover, fade-in sequence — Apple-style]

User journey:
1. [What user sees first]
2. [What builds trust]
3. [Primary CTA]

Build component-by-component, not full pages. Start with hero only.
```

Полная версия + buzzword-слайдеры: `../prompts/lovable-bring-your-vibe.md`

---

## 4. Screenshot fix-loop (итерация через скриншот)

> Используй когда нужно исправить конкретные визуальные проблемы.
> Правило: только видимые проблемы, без касания логики.

```
[Paste screenshot of current UI]

The current UI has these issues vs DESIGN.md:
- [issue 1: конкретно что не так и где]
- [issue 2: конкретно что не так и где]

Fix only the visible problems in the screenshot. Don't touch logic.
Follow DESIGN.md spec for spacing/typography/colors.
```

Полная версия + паттерн «I am frustrated»: `../prompts/screenshot-fix-loop.md`

---

## 5. Pre-code ASCII wireframe lock

> Запускай ПЕРЕД кодом, чтобы зафиксировать layout.
> Предотвращает AI-default структуры: hero+3-card, 2-col comparison, 4-col footer.

```
Before we start coding, let's align on the layout first. Create an ASCII
wireframe of [feature]. Include all key elements and show structure.

Avoid AI-default layouts (2-col comparison, hero+3-card grid, footer with 4 columns).
Suggest ONE non-obvious layout choice that fits the user journey.
```

Полная версия + примеры ASCII: `../prompts/ascii-wireframe-lock.md`

---

## Сводная таблица: когда использовать

| Промпт | Когда | Результат |
|--------|-------|-----------|
| #1 Reverse-design | Есть референс, нужен Style Guide | `DESIGN_SYSTEM.md` |
| #2 Guard-rails | Старт любого проекта | Блок в `CLAUDE.md` |
| #3 Lovable vibe | Новый проект в Lovable/Bolt | Стартовый UI с нужным стилем |
| #4 Screenshot fix | UI не то после итерации | Точечные исправления без регрессий |
| #5 Wireframe lock | Перед генерацией любой страницы | ASCII-каркас как договорённость |

---

## Источники

- [docs.lovable.dev](https://docs.lovable.dev) + [lovable-prompts.com](https://lovable-prompts.com) — Plan Mode и каталог промптов
