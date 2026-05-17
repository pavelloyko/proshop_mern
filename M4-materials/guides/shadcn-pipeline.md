# shadcn/ui Pipeline: от требований к production-коду

Этот гайд описывает трёхшаговый процесс работы с shadcn/ui через AI-агентов — от структурирования UX до генерации кода с актуальным API. Без этого процесса AI генерирует сломанные shadcn-компоненты: половина props в обучающих данных устарела.

---

## TL;DR

- Корень проблемы: AI знает shadcn, но не знает актуальный API — генерирует устаревший код.
- Решение: shadcn/ui MCP server (3 инструмента, 2 400 звёзд на GitHub) + трёхшаговый pipeline.
- Три шага: UX Structure Plan → Component Mapping → Implementation.
- shadcn — стандарт 2026 для AI-генерации: 5 причин, почему именно он.
- Экосистема регистров: Aceternity, Cult UI, Magic UI — анимированные компоненты без кастомного кода.

---

## Почему shadcn — стандарт 2026 для AI-генерации

### 1. Не библиотека, а копи-паст — компоненты в твоём репо

`npm install shadcn-ui` не существует. Каждый компонент копируется в `src/components/ui/` и становится твоим кодом. Можно менять что угодно без форка. AI-агент может напрямую читать и редактировать компоненты — нет «чёрного ящика» node_modules.

### 2. Tailwind + Radix UI: accessible primitives из коробки

Radix UI даёт WAI-ARIA, keyboard navigation, focus management для Dialog, Dropdown, Toast, Select. Разработчик не думает о доступности «потом» — она встроена в примитивы.

### 3. AI знает API по умолчанию

Lovable, v0.dev, Bolt.new, Claude Design — все четыре генерируют shadcn по умолчанию без явного указания. Это де-факто стандарт prompt-to-UI индустрии в 2026.

Проблема без MCP: API библиотеки обновляется, тренировочные данные моделей отстают. AI генерирует сломанный код с устаревшими props. Решение — shadcn MCP server (см. ниже).

### 4. MCP server: 2 400 звёзд на старте

shadcn/ui MCP server даёт агенту три инструмента:
- `get_component` — полная документация компонента с актуальным API
- `get_blocks` — готовые составные секции (dashboard blocks, form blocks, auth blocks)
- `list_components` — список всего доступного в библиотеке и регистрах

Без GitHub-токена: лимит 60 запросов/час. С токеном: 5 000 запросов/час.

### 5. Огромная экосистема регистров

shadcn открыл формат registry, и сообщество построило десятки совместимых библиотек. Добавляются в `components.json`, MCP автоматически их «видит».

---

## Трёхшаговый pipeline

> «Корень проблемы: AI генерит сломанные shadcn — нет знаний об актуальном API. Половина props устарела или отсутствует.»

### Шаг 1: UX Structure Plan

**Агент пишет только навигацию и иерархию страницы. Никакого кода.**

```
Analyze the requirements and create a UX Structure Plan:
- Main navigation sections
- Page hierarchy and content blocks
- Key user actions per section
- States required: empty / loading / error / success
Do NOT write any code yet.
```

Цель: зафиксировать UX-логику до того, как AI начнёт «творить» визуально. Если пропустить этот шаг — получишь generic 2-column layout или стандартный dashboard с карточками.

### Шаг 2: Component Mapping Plan

**Агент берёт план из шага 1 и привязывает каждую секцию к конкретным shadcn-компонентам через MCP.**

Ключевое правило: агент вызывает `list_components` и `search_items_in_registries` — берёт реальные имена из MCP, не выдумывает из головы.

```
Using the UX Structure Plan and shadcn MCP tools
(list_components, get_component), create a Component Mapping Plan:
- Which shadcn component handles which section
- Are blocks available for any section? (prefer blocks over individual components)
Verify each component name via MCP. Do NOT write code yet.
```

Пример маппинга:

```
Sidebar navigation   → Sheet (mobile) + NavigationMenu (desktop)
Data table           → DataTable block (не отдельный Table — берём готовый block)
User profile         → Avatar + DropdownMenu
Notifications        → Toast (transient) + Badge (counter)
Filters              → Command + Popover
Date picker          → Calendar + Popover
```

### Шаг 3: Финальная имплементация

**Явное правило в промпте: готовые blocks > отдельные components.**

```
Implement using the Component Mapping Plan.
RULE: Prioritize shadcn blocks over individual components.
Use exact component names from the MCP tools — never invent them.
```

`blocks` в shadcn — это готовые составные секции: login form с валидацией, dashboard layout, data table с сортировкой. Они тестированы, доступны, консистентны. Только если нужного block нет — собирается из компонентов.

---

## shadcn/ui MCP server: настройка

```bash
# Установка через npx
npx shadcn@latest mcp

# Или добавить в .mcp.json / cline_mcp_settings.json:
{
  "shadcn": {
    "command": "npx",
    "args": ["shadcn@latest", "mcp"]
  }
}
```

Для доступа к регистрам в `components.json`:

```json
{
  "registries": {
    "aceternity": "https://ui.aceternity.com/registry/{name}.json",
    "magicui":    "https://magicui.design/r/{name}.json",
    "cultui":     "https://www.cult-ui.com/r/{name}.json"
  }
}
```

После этого `get_project_registries` включает все добавленные регистры в поиск.

---

## Регистры shadcn: экосистема расширений

| Регистр | Фокус | URL |
|---|---|---|
| **registry.directory** | Каталог всех shadcn-совместимых реестров | registry.directory |
| **Aceternity UI** | Анимированные компоненты: Cards, Animated Beams, Spotlight | ui.aceternity.com |
| **Cult UI** | Современные паттерны: File Upload, Responsive Modal | cult-ui.com |
| **Magic UI** | Премиум эффекты: Shimmer Buttons, Particles, Confetti | magicui.design |
| **Origin UI** | Расширенные формы: 30+ вариантов input | originui.com |

Добавляешь регистр в `components.json` → shadcn MCP автоматически включает его компоненты в `list_components` и `search_items`.

---

## Контраст с Figma MCP

shadcn MCP — пример хорошо спроектированного MCP-сервера. Полезно понимать разницу:

| Критерий | shadcn MCP | Figma MCP (официальный) |
|---|---|---|
| Количество инструментов | 3 (чётких, узких) | Десятки |
| Domain | Один: UI-компоненты | Весь граф Figma-документа |
| Токены на запрос | Предсказуемые, малые | До 20% окна на 5-7 элементов |
| Бесплатный доступ | Да (с лимитом без токена) | Требует Full Seat |
| Rate limits | 60/час без токена, 5000 с токеном | 6 экспортов/месяц бесплатно |

Официальный Figma MCP выгружает все параметры всех узлов — тянет ненужные стили, скрытые слои, варианты компонентов. Работает стабильно только на простых макетах с настроенным auto-layout.

**Решения для Figma:**

- **Figmaline** — бесплатная альтернатива официальному Figma MCP без платного тарифа.
- **Figma Bridge MCP** — community-решение через WebSocket, обходит rate-limits. Архитектура: Figma Plugin (внутри Figma Desktop) + MCP-сервер в IDE, связь через WebSocket.

**Золотой паттерн для Figma:** если дизайн в Figma сделан из реальных shadcn-компонентов (shadcn UI Kit) — Figma MCP узнаёт имена компонентов → shadcn MCP ставит точные компоненты → 100% маппинг без галлюцинаций.

> Если Figma-дизайн сделан из shadcn — нейронка не угадывает имена компонентов, она их читает.

---

## TweakCN: быстрая кастомизация темы

shadcn out-of-box выглядит generic: neutral gray, zinc, slate. TweakCN — визуальный редактор тем без написания CSS.

**Workflow:**

1. Открыть TweakCN → выбрать preset близкий к бренду
2. Подкрутить токены: background, primary, muted, border-radius
3. Включить dark mode — бесплатный coverage без дополнительной работы
4. Export → в Claude Code:

```
Replace my shadcn theme variables with this theme.
Keep custom variables. Don't break existing components.

[экспорт из TweakCN]
```

shadcn компоненты используют CSS variables из globals.css — меняем переменные, все компоненты подхватывают автоматически.

Когда использовать TweakCN: нет дизайнера, нужно быстрое брендирование (до 15 минут), прототип для демо. Когда не использовать: продукт с серьёзными требованиями к бренду — делайте полный DESIGN.md.

---

## Двухшаговая slash-команда

Альтернативный подход через Cursor slash-commands для переиспользования workflow:

**Команда 1 — только план** (сохраняется как slash-команда, не пишет код):
1. Опиши приложение в Claude/ChatGPT
2. Попроси сгенерировать детальный markdown-промпт: overview, шаги, чеклист, «использовать MCP shadcn»
3. Сохранить как slash-команду в Cursor

**Команда 2 — исполнение** (читает план из команды 1):
- Строго по чеклисту строит приложение
- Активно использует shadcn MCP по плану

Переиспользуется на любом проекте — команды сохраняются в Cursor settings.

---

## Сводка / Cheat sheet

```
shadcn в 2026:
  - Не библиотека — копи-паст в твой репо
  - AI генерит его по умолчанию (Lovable, v0, Bolt, Claude Design)
  - Без MCP: устаревший API → сломанный код
  - С MCP: актуальный API → рабочий код

3 шага pipeline:
  1. UX Structure Plan    → навигация + иерархия, БЕЗ кода
  2. Component Mapping    → shadcn через MCP, БЕЗ кода
  3. Implementation       → blocks > components, конкретные имена

shadcn MCP (3 инструмента):
  get_component      → API компонента
  get_blocks         → готовые составные секции
  list_components    → что есть в проекте + регистрах

Регистры (в components.json):
  Aceternity UI  → анимированные компоненты
  Magic UI       → премиум эффекты
  Cult UI        → современные паттерны
  Origin UI      → расширенные формы

Кастомизация: TweakCN → CSS variables → экспорт → CC промпт
```

---

## Cross-refs

- `guides/tools-landscape-2026.md` — shadcn в контексте 5 категорий инструментов
- `guides/design-md-as-2026-standard.md` — DESIGN.md как дополнение к shadcn
- `guides/component-vs-custom.md` — когда shadcn, когда кастом
- `guides/pixel-perfect-verification.md` — верификация shadcn-результата
- `M4/agents/shadcn-requirements-analyzer/` — агент Requirements Analyzer
- `M4/agents/shadcn-component-researcher/` — агент Component Researcher
- `M4/agents/shadcn-implementation-builder/` — агент Implementation Builder
- `M4/prompts/shadcn-component-mapping.md` — шаблон Component Mapping Plan

## Источники

- [shadcn/ui MCP server](https://ui.shadcn.com/docs/mcp)
- [Aceternity UI](https://ui.aceternity.com), [Magic UI](https://magicui.design), [Cult UI](https://cult-ui.com), [Origin UI](https://originui.com)
- [TweakCN](https://tweakcn.com)
