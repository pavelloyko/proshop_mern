# DESIGN.md как стандарт 2026: дизайн-система как правила для AI

Этот гайд объясняет, что такое DESIGN.md, почему он стал открытым стандартом в апреле 2026 и как он соотносится с тем, что уже изучали в M2. Если CLAUDE.md — это правила для AI по коду и архитектуре, то DESIGN.md — это правила для AI по дизайну. Одна механика, разные домены.

---

## TL;DR

- DESIGN.md = CLAUDE.md для дизайна: статически закодированные правила, которые AI видит в каждом промпте.
- 21 апреля 2026 Google открыл спецификацию как open standard — любой инструмент теперь может импортировать и экспортировать DESIGN.md.
- Файл содержит 10 разделов: цвета, типографика, отступы, радиусы, тени, компоненты, интерактивные состояния, анимации, доступность, формат.
- Живёт в корне репо рядом с CLAUDE.md; CLAUDE.md ссылается на него.
- Быстрый путь без дизайнера: TweakCN за 15 минут или reverse-design prompt по скриншоту.

---

## Cross-ref M2: тип Writing из Kung Fu Context

В M2 разбирали 4 типа контекст-работы:

| Тип | Что это | Примеры |
|---|---|---|
| **Writing — статически кодировать** | Пишем вручную то, что агент знает всегда | `CLAUDE.md`, `AGENTS.md`, `.cursorrules` |
| Selection — динамически загружать | Агент тянет нужное в нужный момент | Skills, MCP, RAG, @file |
| Compression — сжимать | Когда контекст раздувается | `/compact`, `/clear` |
| Isolation — изолировать | Отделить чужой контекст | Subagents, worktrees |

`DESIGN.md` — это тип **Writing**. Та же механика: один файл в корне репо, агент видит его в каждом промпте, правила применяются автоматически без напоминаний. Правишь файл — меняется поведение агента во всём проекте.

```
Writing-тип в 2026:
  CLAUDE.md     ← правила для AI: логика, архитектура (M2)
  AGENTS.md     ← то же, cross-tool стандарт (M2)
  .cursorrules  ← правила для Cursor (M2)
  DESIGN.md     ← правила для дизайна (M4)  ← НОВОЕ
```

Ключевой инсайт: все дизайн-инструменты (Stitch, Pencil, Claude Design, Cursor Design Mode) начали читать этот файл — точно так же, как AI-IDE читают CLAUDE.md.

---

## DESIGN.md как открытый стандарт (21 апреля 2026)

До 21 апреля 2026 DESIGN.md был форматом, специфичным для Google Stitch. Инструмент экспортировал машиночитаемую спецификацию дизайна в Markdown, она работала только внутри экосистемы Google.

**21 апреля 2026 Google открыл спецификацию:**
`https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-design-md/`

Google официально назвал это «AGENTS.md for design»: любой инструмент теперь может импортировать и экспортировать DESIGN.md.

Что изменилось практически:
- **Было:** формат Stitch → читает только Stitch
- **Стало:** открытый стандарт → любой IDE, любой AI-агент, Pencil, Claude Design, Cursor

Один файл в корне репо — и любой инструмент из стека понимает дизайн-систему проекта. Переключился с Stitch на Pencil — DESIGN.md остаётся. Задача закрыта в Claude Code — тот же файл.

---

## Где DESIGN.md живёт в репо

```
project-root/
├── CLAUDE.md           ← правила для AI: логика и архитектура
├── AGENTS.md           ← симлинк или копия CLAUDE.md, cross-tool
├── DESIGN.md           ← правила для дизайна  ← этот файл
├── .cursorrules        ← правила для Cursor
└── src/
    ├── globals.css     ← CSS variables из токенов DESIGN.md
    └── components/
        └── ui/         ← shadcn компоненты (твой код)
```

**Как CLAUDE.md ссылается на DESIGN.md:**

```markdown
## Design rules: see ./DESIGN.md

When generating any UI component or modifying styles:
1. Read DESIGN.md before writing code
2. Use only colors defined as CSS variables — never raw hex
3. Follow spacing scale (multiples of 8px only)
4. Implement all interactive states: hover, focus, loading, empty
5. Font: Manrope (not Inter)
```

Механика: правишь токен в DESIGN.md → обновляешь globals.css → весь проект меняется. Один источник правды, один промпт агенту.

---

## Канонические 10 разделов DESIGN.md

Полный шаблон лежит в `M4/templates/DESIGN_SYSTEM.md`. Ниже — структура и ключевые решения по каждому разделу.

### 1. Color Palette

Семантические роли, а не hex-коды. Никогда `#6366f1` напрямую — только `var(--primary)`. CSS variables для light и dark mode.

Обязательные роли: `--background`, `--foreground`, `--card`, `--card-alt`, `--primary`, `--primary-fg`, `--muted`, `--accent`, `--destructive`, `--border`, `--ring`.

### 2. Typography

Явно указывать шрифт по имени: **Manrope, Geist, Space Grotesk — НЕ Inter** (Inter перенасыщен до невидимости). Полная шкала с pixel values, line-height, letter-spacing.

### 3. Spacing Scale

Только кратные 8px: 4 / 8 / 16 / 24 / 32 / 48 / 64 / 96. Никаких произвольных значений типа `14px` или `22px`.

### 4. Border Radius Scale

```
none:  0px      — таблицы, data grids
sm:    4px      — бейджи, чипы, code blocks
md:    8px      — кнопки, инпуты (default)
lg:    12px     — карточки (default)
xl:    16px     — модалки, поповеры
full:  9999px   — пилюли, аватары
```

### 5. Elevation / Shadow

Философия: **без box shadows по умолчанию**. Глубина через контраст фонов (3 уровня: page → card → card-alt). Box shadows только для dropdown и tooltip.

### 6. Component Patterns

Карточки, кнопки (primary / secondary / danger / ghost / disabled), инпуты, бейджи — каждый с конкретными значениями. Не «нейтральный цвет», а `var(--card)`, `padding: 24px`, `border-radius: 12px`.

### 7. Interactive States

**Каждый интерактивный элемент должен иметь все состояния:** hover, focus, active, loading, empty/disabled. AI по умолчанию этого не делает — нужно явно прописать в DESIGN.md.

### 8. Animation / Transitions

Целесообразная, не декоративная. Base transition: 150ms ease. Анимация появления элементов — последовательно (Apple-стиль), не «все сразу». Уважать `prefers-reduced-motion`.

### 9. Accessibility

Контрастность ≥4.5:1, keyboard navigation, ARIA labels на интерактивных элементах, skip-to-content link, focus ring 2px.

### 10. Format Declaration

```
Component library: shadcn/ui
CSS framework:     Tailwind CSS 4 + CSS variables
Icon set:          Lucide Icons
```

---

## Как извлечь DESIGN.md из референса (reverse-design)

Быстрее и точнее, чем описывать стиль словами. Принцип простой: словесное описание стиля («что такое Apple Style») — почти невозможно, а скриншот референса — однозначен.

**Промпт:**

```
[Скриншот референса: Stripe / Linear / Apple / ваш выбор]

You are a senior product designer. Analyze this screenshot in detail.
Create a DESIGN_SYSTEM.md file documenting:

1. Color palette (hex/oklch values, semantic roles)
2. Typography (font family, weights, scale, line-height, tracking)
3. Spacing scale (multiples of 8 only)
4. Border radius scale
5. Elevation approach (or no-shadows philosophy)
6. Component patterns visible
7. Interactive states approach
8. Accessibility (contrast, ARIA, focus)

Format as shadcn/ui + Tailwind CSS 4 with CSS variables.
Provide actionable documentation that enables exact visual replication.
```

Полный промпт с вариациями (luxury / minimal-tech / editorial) — в файле `M4/prompts/reverse-design-extract.md`.

---

## Реальный кейс: 21 экран за вечер

В одном из публичных кейсов разработчик собрал 21-screen SaaS dashboard за один вечер. Подход:

> «Prompts aren't instructions. They're build artifacts. When the tokens change, the prompt changes.»

Полный design system + product name шли в **каждый промпт verbatim** — дословно, целиком, без отсылок «смотри предыдущий файл».

**Почему это работает:** LLM не держит «предыдущий контекст» как человек. «Посмотри в файл X» — дополнительный hop, потеря точности. Весь design system в одном промпте = zero ambiguity.

Практическое следствие: DESIGN.md — не документация. Это **build artifact**, который идёт в каждый промпт целиком или через `@ref ./DESIGN.md` в CLAUDE.md (что даёт тот же эффект автоматически).

---

## Sub-agent enforcement

Главная проблема долгих проектов: LLM после крупных рефакторов «забывают» правила дизайн-системы. Называется context rot или design drift.

**Решение:** `.claude/agents/ui-expert.md` — выделенный UI reviewer subagent на Opus.

Два режима работы:

**Review mode (read-only):**
- Читает DESIGN.md
- Обходит все UI компоненты
- Составляет отчёт нарушений (critical / warning / info)
- Не меняет код

**Enforce mode (full tool access):**
- Читает DESIGN.md
- Находит нарушения
- Автоматически рефакторит код под дизайн-систему
- Создаёт git commit с описанием

Запуск через `/loop` (по крону, каждый час) или вручную после major refactor.

Полный шаблон subagent prompt — в файле `M4/prompts/pixel-perfect-subagent.md`.

---

## TweakCN: быстрая кастомизация без дизайнера

Если нет дизайнера и бюджета — TweakCN (визуальный редактор shadcn-тем) даёт брендовую тему за 15 минут:

1. Открыть TweakCN → выбрать preset близкий к бренду
2. Подкрутить токены: background, primary, muted, border-radius
3. Включить dark mode (получаешь двойной coverage бесплатно)
4. Export → промпт в Claude Code:

```
Replace my shadcn theme variables in globals.css with this theme.
Keep all custom variables that aren't part of shadcn theme.
Don't break existing components — only update :root and .dark CSS variable values.

[вставить экспорт из TweakCN]
```

shadcn/ui компоненты используют CSS variables из globals.css. Меняем только переменные — все компоненты подхватывают автоматически.

---

## Сводка / Cheat sheet

```
DESIGN.md в репо
  ├── Живёт: корень проекта рядом с CLAUDE.md
  ├── Тип: Writing (статически кодированные правила)
  ├── Читают: CC, Cursor, Stitch, Pencil, Claude Design
  └── Ссылка из CLAUDE.md: ## Design rules: see ./DESIGN.md

Как создать:
  Option A: reverse-design prompt по скриншоту референса
  Option B: TweakCN → экспорт CSS variables (15 минут)
  Option C: шаблон из M4/templates/DESIGN_SYSTEM.md

Anti-patterns в DESIGN.md (запрети явно):
  - Inter font (используй Manrope / Geist)
  - shadow-lg рефлекторно (глубина через bg contrast)
  - dark:bg-gray-900 (только CSS variables)
  - hex-коды без семантических ролей
  - Пропущенные interactive states

Kрземиенски-правило:
  DESIGN.md = build artifact, не документация
  → весь файл в каждый промпт (или @ref в CLAUDE.md)
```

---

## Cross-refs

- `guides/tools-landscape-2026.md` — какие инструменты читают DESIGN.md
- `guides/shadcn-pipeline.md` — как shadcn + DESIGN.md работают вместе
- `guides/component-vs-custom.md` — когда DESIGN.md критически важен
- `guides/pixel-perfect-verification.md` — sub-agent enforcement pattern
- `guides/milestone-clear-pattern.md` — защита DESIGN.md при длинных сессиях
- `M4/templates/DESIGN_SYSTEM.md` — полный canonical шаблон
- `M4/prompts/reverse-design-extract.md` — промпт извлечения DS из скриншота
- `M4/prompts/pixel-perfect-subagent.md` — pixel-perfect subagent шаблон

## Источники

- [Google Blog: DESIGN.md open standard](https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-design-md/) — 2026-04-21
