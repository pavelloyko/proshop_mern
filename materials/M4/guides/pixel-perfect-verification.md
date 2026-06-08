# Pixel-Perfect верификация: от «кажется нормально» до closed-loop

Этот гайд описывает 6 уровней верификации UI — от простого скриншота в чат до полностью автономного цикла с Playwright. Важно: AI пишет код «вслепую» — без обратной связи от рендера. Даже идеальный shadcn компонент может выглядеть сломанным. Верификация замыкает этот цикл.

---

## TL;DR

- AI не видит что получилось. Верификация — это обратная связь от рендера к коду.
- 6 уровней: от «скриншот в чат» до «Playwright e2e без участия человека».
- Pixel-Perfect subagent: Browser MCP + Figma MCP + vision diff — production-grade.
- Browser MCP экономичнее Playwright MCP: подключается к уже открытой вкладке, не жрёт контекст.
- UI reviewer subagent: два режима — review (аудит) и enforce (рефактор под DESIGN.md).

---

## Зачем верификация?

AI-агент пишет код на основе промпта — он не «смотрит» на результат в браузере. Это означает:

- Компонент может быть написан правильно по коду, но в рендере выглядеть сломанным.
- DESIGN.md правила применялись в коде, но визуально — нарушены из-за CSS cascading.
- Responsive поведение не тестировалось — mobile viewport может ломать layout полностью.
- После рефакторинга агент «забыл» hover states, focus rings, пустые состояния.

Верификация — это замкнутый цикл: код → рендер → сравнение → правка → снова код.

---

## 6 уровней верификации

### Уровень 1: Screenshot + LLM eyes

Самый простой и дешёвый паттерн.

```
[Скриншот страницы]

Look at this screenshot of what I built.
Tell me what looks wrong visually: layout issues, spacing problems,
inconsistent colors, broken components, missing states.
```

Когда подходит: прототип, MVP, быстрая проверка до отправки дизайнеру. Стоимость: один запрос к модели.

Ограничения: AI видит только статичный скриншот. Не проверяет hover, focus, responsive, интерактивные состояния.

### Уровень 2: Pixel-Perfect subagent

Production-grade паттерн. Subagent сравнивает рендер с эталоном и исправляет код.

**Полный flow из 5 шагов:**

1. Subagent делает скриншот рендера через **Browser MCP** (подключается к открытой вкладке Chrome)
2. Тот же subagent тянет эталонный скриншот из макета через **Figma MCP**
3. Передаёт оба скриншота **vision-модели** (Opus или GPT-4o)
4. Vision-модель находит отличия: layout, цвета, отступы, размеры шрифтов, отсутствующие элементы
5. Если diff > threshold → subagent переписывает код, цикл повторяется с шага 1

```
Subagent loop:
  1. Browser MCP → screenshot(current_render)
  2. Figma MCP   → screenshot(design_reference)
  3. Vision diff:
       Layout: sections match? element positions?
       Colors: primary/accent/bg match tokens?
       Spacing: padding/margin consistent?
       Typography: font sizes, line-height?
  4. if diff_score > threshold:
         rewrite_code(diff_report)
         goto 1
  5. else: DONE
```

Полный шаблон subagent — в `M4/prompts/pixel-perfect-subagent.md`.

### Уровень 3: Browser MCP — экономия токенов

Browser MCP подключается к уже открытой вкладке Chrome. Не поднимает новый браузер, не генерирует DOM-snapshot — только нужные данные.

| | Playwright MCP | Browser MCP |
|---|---|---|
| Подключение | Поднимает отдельный браузер | Подключается к открытой вкладке |
| Токены | DOM-snapshots жрут контекст | Только нужные данные по запросу |
| Скорость | Медленнее (запуск браузера) | Быстрее (браузер уже открыт) |
| Экономия | Baseline | 20-40% контекстного окна |

Когда Browser MCP лучше: интерактивная разработка, когда нужна быстрая итерация. Когда Playwright MCP лучше: CI/CD, headless, e2e тесты без открытого браузера.

### Уровень 4: Responsive sweep

После функционального теста — прогон через три viewport.

```
Run a responsive sweep:
1. Set viewport to mobile (375px)   → screenshot → check layout
2. Set viewport to tablet (768px)   → screenshot → check layout
3. Set viewport to desktop (1440px) → screenshot → check layout
Report: broken layouts, overflowing content, wrong font sizes,
missing mobile optimizations.
```

Время: 1-2 минуты. Находит 80% responsive проблем автоматически. Запускать перед каждым milestone завершением.

### Уровень 5: UI reviewer subagent

Выделенный sub-agent на Opus — только для дизайн-системы, не трогает логику.

**Два режима:**

**Review mode (read-only):**
- Читает DESIGN.md
- Сканирует все UI компоненты
- Выдаёт structured report: violations by severity (critical / warning / info)
- Не меняет код — только аудит

**Enforce mode (full access):**
- Читает report из review mode
- Автоматически рефакторит нарушения в порядке critical → warning → info
- После каждого батча: `tsc --noEmit` проверка
- Commit с описанием правок

**Типичные нарушения, которые ищет:**
- Raw hex вместо CSS variables (`#6366f1` вместо `var(--primary)`)
- Произвольные spacing values (не кратные 8px)
- Неправильный шрифт (Inter вместо Manrope)
- Пропущенные hover / focus / loading / empty состояния
- `dark:bg-gray-900` вместо `var(--background)`
- `shadow-lg` где должна быть глубина через bg contrast
- Отсутствие ARIA labels

Запуск: `/ui-expert review` или `/ui-expert enforce`. Можно по крону через `/loop`.

Полный шаблон — в `M4/prompts/pixel-perfect-subagent.md`.

### Уровень 6: Замкнутый feedback loop

Полностью автономный цикл без участия человека:

```
ESLint (linter)
      ↓
TypeScript tsc --noEmit
      ↓
Unit tests (Vitest / Jest)
      ↓
Playwright e2e (visual screenshot diff)
      ↓
  [ошибки] → агент фиксит → возврат к ESLint
  [зелёный билд] → DONE
```

Директивы в CLAUDE.md для автономного режима:

```markdown
## Coding directives
- Do NOT stop until all tests pass
- After each change: run `tsc --noEmit` and fix errors before continuing
- After UI changes: run Playwright visual tests
- Never leave red type errors or lint warnings
```

---

## Closed-loop: style-guide → Playwright iteration

Паттерн для итеративного pixel-matching по референс-сайту:

1. Берёшь URL референса → вставляешь в чат Cursor
2. **Slash-команда** (большая, переиспользуемая):
   - Запустить Playwright → скриншот референса
   - Построить страницу по скриншоту
   - Скриншот своей страницы → сравнить с оригиналом
   - Внести правки → итерировать до отсутствия визуальных различий
3. Фокус через CSS-селектор для отдельных секций (не вся страница):

```
Focus on the section with class "changelog".
Take a screenshot of ONLY that section.
Compare with the reference screenshot.
Fix until they match.
```

После первой удачной страницы — сгенерировать `style-guide.md` как single source of truth для остальных страниц.

---

## Когда какой уровень использовать

| Контекст | Уровень | Время |
|---|---|---|
| Прототип, MVP за вечер | L1: Screenshot + LLM eyes | 1 мин |
| После каждого milestone | L4: Responsive sweep | 2 мин |
| Production компоненты | L2: Pixel-Perfect subagent | 10-20 мин |
| После major refactor | L5: UI reviewer enforce | 15-30 мин |
| Перед релизом | L6: Замкнутый loop | 30-60 мин |

---

## Сводка / Cheat sheet

```
6 уровней верификации:
  L1 Screenshot + LLM    → дёшево, для прототипа
  L2 Pixel-Perfect sub   → Browser MCP + Figma MCP + vision diff
  L3 Browser MCP         → подключается к Chrome, 20-40% экономия
  L4 Responsive sweep    → 3 viewport (375 / 768 / 1440px)
  L5 UI reviewer sub     → review mode + enforce mode
  L6 Linter → tsc → unit → e2e → авто-фикс

Browser MCP vs Playwright:
  Browser MCP  → подключается к открытой вкладке, дешевле
  Playwright   → headless, CI/CD, изолированный

UI reviewer subagent:
  Review:  DESIGN.md → scan → report (не трогает код)
  Enforce: report → рефактор → commit

Запускай responsive sweep перед каждым /clear
Запускай UI reviewer enforce перед каждым релизом
```

---

## Cross-refs

- `guides/design-md-as-2026-standard.md` — DESIGN.md как эталон для UI reviewer
- `guides/milestone-clear-pattern.md` — когда включать верификацию в milestone workflow
- `guides/shadcn-pipeline.md` — что верифицировать после shadcn Implementation
- `M4/prompts/pixel-perfect-subagent.md` — полный шаблон subagent для L2 и L5
