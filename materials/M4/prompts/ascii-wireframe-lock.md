# ASCII Wireframe Lock: структура до кода

> **Когда использовать:** До написания первой строки кода для любого нового экрана, секции или компонента. Особенно важно для dashboard-типов и landing-страниц — там AI чаще всего генерирует типовые шаблоны.
> **Inputs:** словесное описание фичи или экрана (1-2 предложения).
> **Output:** ASCII-схема структуры, согласованная с тобой — и только потом код. Один нестандартный layout-выбор от модели в подарок.

## Промпт

```
Before we start coding, let's align on the layout first.

Create an ASCII wireframe of [feature — e.g., "a dashboard for a SaaS analytics tool
showing daily active users, revenue chart, and recent events feed"].

Include all key elements and show structure clearly.
Use standard ASCII notation:
  [ ] = container / card
  --- = divider or separator
  ... = content placeholder
  [BTN] = button
  [IMG] = image / icon placeholder

Avoid AI-default layouts:
- NO 2-column "pros vs cons" comparison structure
- NO hero + 3 symmetric cards in a row (the "landing page grid")
- NO footer with 4 equal columns
- NO full-width hero that pushes CTA below the fold

After the wireframe, suggest ONE non-obvious layout choice that fits
the user journey better than the default grid. Explain why in 1 sentence.

Wait for my approval before writing any code.
```

## Объяснение

AI-модели при генерации UI без предварительной структуры воспроизводят наиболее частые layout-паттерны из обучающих данных. Для landing-страницы это почти всегда: hero на весь экран → три карточки с иконками → секция отзывов → footer с четырьмя колонками. Для dashboard: метрики сверху в ряд → таблица снизу. Эти структуры не плохи — они просто перестали быть отличительными. Пользователь видел их сотни раз.

ASCII wireframe до кода решает это одним шагом: как только структура зафиксирована в тексте и одобрена, модель больше не «угадывает» layout при генерации кода — она следует согласованной схеме. Это принципиально другой режим: сначала решение о структуре, потом имплементация. Без wireframe оба шага смешаны в одном промпте, и модель жертвует структурой ради скорости генерации кода.

Просьба «предложи один нестандартный выбор» — намеренная. Она переключает модель из режима «сделай стандартно» в режим «подумай, что подходит именно этому user journey». Один нестандартный элемент (асимметричный split, sticky sidebar вместо top nav, timeline вместо grid) может сделать интерфейс запоминаемым без дополнительных усилий на дизайн.

## Вариации

**Вариация A — для мобильного (вертикальный поток):**

```
Before coding, create an ASCII wireframe of [screen name] for mobile (375px wide).

Show the vertical scroll flow:
- What appears above the fold (first screen without scrolling)
- What requires scrolling to reach
- Where the primary CTA is positioned

Avoid default mobile patterns:
- NO bottom tab bar with 5 equal icons
- NO full-screen modal on first interaction
- NO hamburger menu hiding all navigation

Suggest ONE layout choice that reduces scroll depth for the primary action.
Wait for my approval before writing any code.
```

**Вариация B — для повторяющегося компонента (список, таблица, карточки):**

```
Before coding [component name — e.g., "a list of user transactions"], create
an ASCII wireframe showing:

1. Single item structure (what's in one row/card)
2. Empty state (when the list has 0 items)
3. Loading state (skeleton placeholder)
4. Error state (failed to load)

Avoid default list patterns:
- NO full-width dividers between every row
- NO icon + title + chevron on the right (generic mobile list)

Suggest ONE layout choice that makes the data more scannable.
After approval, build ALL 4 states together, not just the happy path.
```

**Вариация C — plan mode combo (для крупных milestone):**

```
We're starting a new milestone: [milestone name].

Step 1 — wireframe:
Create ASCII wireframes for all [N] screens in this milestone.
Show structure, not style. Label each screen.
Avoid AI-default layouts (symmetric grids, 2-column comparisons).

Step 2 — after I approve the wireframes:
List all components we'll need to build (name each one).
Group them: shared components / page-specific components.

Step 3 — after I approve the component list:
Start building the first component only. Tell me when it's done.

Do not start Step 2 until I say "approved".
```

## Контекст

ASCII wireframe перед кодом — паттерн из сообщества vibe-coding практиков 2026. Сочетание с запретом типовых структур (2-col comparison и т.п.) убирает дефолтные «AI-look» решения. Plan Mode combo — см. [docs.lovable.dev](https://docs.lovable.dev).

## Связь с курсом

Блок M4 F8 (best practices #2 Plan Mode, #3 Build by component) и F9 (anti-AI guards — запрет 2-col comparison). ASCII wireframe — это реализация принципа «изолировать решение о структуре от решения о коде» (паттерн Isolation из M2 Kung Fu Context, примени к дизайну).
