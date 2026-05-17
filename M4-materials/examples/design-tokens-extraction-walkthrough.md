# Walkthrough: Извлечение DESIGN_SYSTEM.md из скриншота

> Пошаговый разбор — как взять скриншот референса (например, Stripe pricing) и за 5-10 минут получить готовый DESIGN_SYSTEM.md под shadcn/ui + Tailwind.

---

## Зачем это нужно

Базовая идея простая:

> «Описать словами, что такое Apple Style — почти невозможно. А заскриншотить — можно за две секунды.»

Это честное признание, которое работает как инструкция.

AI **плохо понимает** абстрактные описания дизайна: «сделай минималистично», «в стиле Stripe», «чисто и современно». У модели нет единственной правильной интерпретации этих слов — она угадывает по «среднему» в обучающих данных. Среднее — это Inter, синие кнопки, фиолетовые градиенты, серые карточки.

AI **отлично считывает визуальные референсы**. Скриншот даёт точную информацию: конкретные соотношения пространства, конкретный spacing, конкретный feel — то, что человек не смог бы сформулировать текстом даже при желании.

Промежуточный артефакт `DESIGN_SYSTEM.md` критичен. Он фиксирует стиль в машиночитаемом формате — и все последующие промпты работают с конкретными значениями, не с абстракциями. Это двухшаговый паттерн: сначала «понять стиль», потом «применить стиль». Делать оба шага в одном промпте («сделай как на картинке») резко снижает качество обоих.

---

## Шаг 1: Выбрать референс

Не любой скриншот одинаково полезен. Хорошие референсы — сайты, где дизайн сделан намеренно, а не по умолчанию.

**Хорошие источники:**

| Сайт | Стиль | Подходит для |
|------|-------|-------------|
| **stripe.com/pricing**, stripe.com/atlas | Minimal-tech, generous spacing, no shadows | SaaS-продукты, dashboard, dev-tools |
| **linear.app** | Premium-tech, sharp typography, dark mode | Productivity-инструменты, B2B |
| **vercel.com** | Modern dev tool, monospace accents, dark | Dev-tools, инфраструктурные сервисы |
| **apple.com** | Premium consumer, generous typography, sequence animations | Consumer-apps, hardware-лендинги |
| **notion.so** | Content-first, soft palette, generous whitespace | Note-taking, collaboration, content |
| **mobbin.com** | База скриншотов реальных приложений | Поиск референсов для мобильных UI |

**Антипаттерны при выборе:**
- НЕ AI-generated сайты — получишь generic AI-look обратно в извлечённом DS
- НЕ overly branded (Nike, Coca-Cola) — потеряешь полезные tokens за брендовыми эффектами
- НЕ сайты 2015-2018 — устаревшая типографика и spacing philosophy

---

## Шаг 2: Сделать скриншот

Качество скриншота напрямую влияет на качество извлечения.

**Правила хорошего скриншота:**
- Полная страница, а не вырезка (AI нужен контекст соотношений)
- Ширина 1440px+ — видно всю типографию и spacing
- Включи hover-state на CTA-кнопку, если важна интерактивность: наведи курсор, потом сделай скрин
- Если важна анимация — несколько скринов sequence (начало, середина, конец перехода)
- Для dark mode — отдельный скрин в dark (не один скрин с половиной light, половиной dark)

Stripe pricing page (stripe.com/pricing) — хороший стандартный выбор для первого раза: чистый, хорошо читаемый AI, с выраженным стилем.

---

## Шаг 3: Открыть LLM с vision

**Подходят:**
- Claude (claude.ai или Claude Code с image input)
- Cursor (с image attachment, Cmd+I → прикрепи файл)
- ChatGPT-4o

**Не работает:**
- LLaMA 11B Vision и аналогичные малые модели — не справятся с дизайн-spec
- Любая text-only LLM

---

## Шаг 4: Запустить промпт

Скопируй промпт из `../prompts/reverse-design-extract.md` и прикрепи скриншот:

```
[Прикрепи скриншот]

You are a senior product designer. Analyze this screenshot in detail.
Create a DESIGN_SYSTEM.md file documenting:

1. Color palette (hex/oklch, semantic roles: bg, fg, primary, muted, accent, destructive, border, ring)
2. Typography (font family, weights, scale with pixel values, line-height, tracking)
3. Spacing scale (only multiples of 8px: 8/16/24/32/48/64)
4. Border radius scale
5. Elevation/shadow approach (or no-shadows philosophy)
6. Component patterns visible (cards, buttons, inputs)
7. Interactive states approach (hover/focus/active/loading/empty)

Format as shadcn/ui + Tailwind CSS 4 with CSS variables.
Provide actionable documentation that enables exact visual replication.
```

Промпт на английском — намеренно. Технические спецификации дизайна (hex-коды, CSS-свойства, shadcn-токены) модели лучше генерируют на en. Язык промпта не влияет на язык интерфейса твоего продукта.

---

## Шаг 5: Получить результат (~30-60 секунд)

AI выдаст DESIGN_SYSTEM.md в 7 секциях. Пример реального вывода для **Stripe Atlas** (сокращённо):

```markdown
# Design System — Stripe Atlas Style

## 1. Color Palette

| Role             | Value           | Usage                        |
|------------------|-----------------|------------------------------|
| --background     | #F6F9FC         | Page background (light)      |
| --background-dark| #0A2540         | Page background (dark)       |
| --foreground     | #0A2540         | Primary text                 |
| --foreground-muted| #425466        | Body text, secondary         |
| --primary        | #635BFF         | CTA buttons, links, accents  |
| --primary-fg     | #FFFFFF         | Text on primary              |
| --accent         | #00D4FF         | Highlight, progress, badges  |
| --border         | #E3E8EE         | Borders, dividers            |
| --muted          | #8898AA         | Placeholder, metadata        |
| --card           | #FFFFFF         | Card surface                 |
| --ring           | #635BFF         | Focus ring                   |

Dark mode: CSS variables swap on .dark class. NEVER hardcode dark:bg-* prefixes.

## 2. Typography

Font: **Camphor** (Stripe's custom) → nearest open source substitute: **Manrope**
Fallback: system-ui, -apple-system, sans-serif

Scale:
- Display:  56px, weight 700, tracking -0.03em — hero headline
- H1:       48px, weight 700, tracking -0.02em — page title
- H2:       36px, weight 600, tracking -0.015em — section header
- H3:       24px, weight 600, tracking -0.01em — card header
- Body:     18px, weight 400, line-height 1.6 — main content
- Small:    14px, weight 400, line-height 1.5 — secondary text
- Caption:  12px, weight 500, tracking 0.01em — labels, badges
- Mono:     14px, IBM Plex Mono — code snippets, amounts

## 3. Spacing Scale

8px base unit. Stripe philosophy: generous spacing, never cramped.

- 8px   — micro (icon + label gaps)
- 16px  — tight padding inside components
- 24px  — card inner padding (default)
- 32px  — between cards in a row
- 48px  — between sections
- 64px  — major section separation
- 96px  — hero-level spacing

NEVER: 12px, 14px, 18px, 22px — arbitrary values outside the scale.

## 4. Border Radius

- 4px   — badges, chips
- 6px   — inputs
- 8px   — buttons (default)
- 12px  — cards (default)
- 16px  — modals, floating panels
- 9999px — pill tags, toggle switches

## 5. Elevation / Shadow Approach

Stripe uses **subtle shadows**, not flat or heavy.

Cards: box-shadow: 0 2px 8px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)
Dropdowns/tooltips: box-shadow: 0 4px 16px rgba(0,0,0,0.08)
Modals: box-shadow: 0 8px 32px rgba(0,0,0,0.12)

NEVER: shadow-lg reflexively. Shadow should indicate elevation, not decoration.

## 6. Component Patterns

### Cards
- Background: var(--card) — white
- Padding: 24px (md)
- Border radius: 12px
- Border: 1px solid var(--border) — #E3E8EE, subtle
- Shadow: 0 2px 8px rgba(0,0,0,0.04)
- Hover: border-color → var(--primary) #635BFF, transition 200ms ease

### Buttons — Primary
- Background: var(--primary) — #635BFF
- Text: var(--primary-fg) — #FFFFFF
- Padding: 12px 24px
- Border radius: 8px
- Hover: brightness(1.08) + scale(1.01), transition 150ms ease
- Focus: ring 2px var(--ring) + offset 2px

### Buttons — Secondary
- Background: transparent
- Border: 1px solid var(--border)
- Text: var(--foreground)
- Hover: background var(--card-alt), border-color var(--primary)

### Inputs
- Border: 1px solid var(--border) — #E3E8EE
- Border radius: 6px
- Padding: 10px 14px
- Focus: border-color var(--primary), box-shadow 0 0 0 3px var(--primary)/15%
- Placeholder: var(--muted) — #8898AA

## 7. Interactive States

Every interactive element requires ALL states defined:

| Element  | Hover                    | Focus                      | Active        | Loading              | Empty                   |
|----------|--------------------------|----------------------------|---------------|----------------------|-------------------------|
| Button   | scale(1.01)+brightness   | ring 2px primary           | scale(0.98)   | spinner + opacity .7 | disabled: opacity .4    |
| Input    | border brighter          | ring 3px primary/15%       | —             | —                    | read-only, bg muted     |
| Card     | border → primary         | outline ring               | —             | skeleton shimmer     | icon + text + CTA       |
| Link     | underline                | outline ring               | color primary | —                    | —                       |
```

---

## Шаг 6: Верификация

Перед тем как положить файл в репо — прогони по чек-листу. AI иногда выдаёт приблизительный DS с несколькими характерными ошибками.

**Чек-лист:**

- [ ] **Цвета имеют semantic roles** — не просто `#635BFF`, а `--primary: #635BFF` с описанием использования
- [ ] **Шрифт указан явно** — не `«default»` или `«Inter unless specified»` (Inter — признак AI-default)
- [ ] **Spacing кратно 8** — если AI выдал значения 5/10/15/18 — замени на ближайшие из шкалы
- [ ] **Component patterns конкретны** — не `«modern cards»`, а `«cards: 24px padding, 12px radius, 1px border var(--border)»`
- [ ] **Interactive states описаны** — hover, focus, loading, empty — все четыре, для каждого компонента
- [ ] **Нет `dark:bg-gray-900`** — dark mode только через CSS variables
- [ ] **Нет `shadow-lg` по умолчанию** — если Stripe использует тени, они точечные и с конкретными значениями

Если находишь проблему — правь руками прямо в файле. Это займёт 2-3 минуты.

---

## Шаг 7: Применение

Положи `DESIGN_SYSTEM.md` в корень проекта рядом с `CLAUDE.md`. В `CLAUDE.md` добавь:

```markdown
## Design rules

See ./DESIGN_SYSTEM.md for full design system specification.

When generating any UI component or modifying styles:
1. Read DESIGN_SYSTEM.md before writing code
2. Use only colors defined as CSS variables — never raw hex
3. Follow spacing scale (multiples of 8px only: 8/16/24/32/48/64)
4. Implement all interactive states: hover, focus, loading, empty
5. Font: Manrope (NOT Inter)
```

Теперь любая AI-генерация UI в этом проекте будет использовать дизайн-систему автоматически — агент читает `CLAUDE.md` при каждом запуске.

**Структура файлов проекта:**

```
project-root/
├── CLAUDE.md            ← правила для AI + ссылка на DESIGN_SYSTEM.md
├── AGENTS.md            ← симлинк на CLAUDE.md (cross-tool)
├── DESIGN_SYSTEM.md     ← твоя извлечённая дизайн-система
└── src/
    ├── globals.css      ← CSS variables из токенов DESIGN_SYSTEM.md
    └── components/ui/   ← shadcn компоненты
```

---

## Шаг 8: Итерация

Первый extract — хорошая база, но редко идеальный финал. Итерируй точечно:

```
Refine the DESIGN_SYSTEM.md:
- Add dark mode color palette (mirror existing semantic roles to dark values)
- Add animation/transition tokens (base: 150ms ease, hover: scale 1.02, 
  skeleton shimmer 1.5s infinite, sequence stagger 50ms between items)
- Add accessibility section (contrast 4.5:1 requirement, ARIA labels policy,
  focus ring specification, touch targets 44×44px minimum)
```

Не переписывай весь DS заново — это потеря контекста. Уточняй конкретные секции.

---

## Сравнение: до и после

**До (без DESIGN_SYSTEM.md):**
- AI генерирует Inter, серые карточки, фиолетовые градиенты — каждый раз
- Каждый компонент в своём стиле: hero с одним spacing, footer с другим
- После рефакторинга функциональности — весь стиль ломается

**После (с DESIGN_SYSTEM.md из Stripe reference):**
- Узнаваемый стиль: Camphor/Manrope, subtle shadows, generous spacing
- Consistent spacing/typography по всем компонентам
- AI следует токенам (`var(--primary)`) вместо угадывания
- После функционального рефакторинга — стиль не трогается (он в tokens)

В одном из публичных кейсов разработчик собрал 21-screen SaaS dashboard за один вечер именно потому, что **весь design system шёл в каждый промпт verbatim**. Вывод:

> «Prompts aren't instructions. They're build artifacts. When the tokens change, the prompt changes.»

---

## Универсальность паттерна

Этот workflow обобщается на любой тип UI — меняется только источник скриншота:

| Что строишь | Откуда скриншот | Вариация промпта |
|-------------|----------------|-----------------|
| SaaS dashboard | Linear, Vercel | Вариация B — minimal-tech (из `../prompts/reverse-design-extract.md`) |
| Marketing landing | Stripe Atlas | Базовый промпт |
| Mobile app | Mobbin.com, Apple Music | Добавить `«Mobile-first: safe areas, touch targets 44px, bottom nav»` |
| Luxury / premium | Bang & Olufsen, Loro Piana | Вариация A — luxury/serif |
| Email templates | Mailchimp campaign | Добавить `«Email constraints: inline CSS, 600px max-width, no flexbox»` |
| Editorial / медиа | The Browser Company, Arc | Вариация C — editorial/brutalist |

---

## Контекст паттерна

Двухшаговое извлечение style guide из скриншота — повторяющийся приём в практике vibe-coding 2026: сначала «понять стиль» (reverse-design prompt по скриншоту), потом «применить стиль» (генерация UI с DESIGN_SYSTEM.md в контексте). Делать оба шага в одном промпте резко снижает качество обоих.

---

## Cross-refs

- Промпт: `../prompts/reverse-design-extract.md`
- Шаблон DESIGN_SYSTEM.md: `../templates/DESIGN_SYSTEM.md`
- Заполненные примеры: `../templates/DESIGN_SYSTEM-minimal-tech.md`, `../templates/DESIGN_SYSTEM-luxury-serif.md`
- Anti-AI-slop cheatsheet: `../cheatsheets/12-signs-of-ai-look.md`
- Anti-AI guard-rails в промпт: `../prompts/anti-ai-slop-guards.md`
