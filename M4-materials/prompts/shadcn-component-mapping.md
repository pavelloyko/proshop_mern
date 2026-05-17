# shadcn Pipeline — Step 2: Component Mapping

> **Когда использовать:** После того как UX Structure Plan (Step 1) утверждён. Перед написанием кода. Привязывает каждую секцию плана к реальным shadcn компонентам через MCP — не по памяти, не по угадке.
> **Inputs:** UX Structure Plan из Step 1 (или вставить текст плана прямо в промпт). Требуется shadcn MCP server подключённый в Claude Code / Cursor.
> **Output:** Таблица маппинга секций на компоненты с обоснованием. Список установочных команд. БЕЗ кода реализации.

## Промпт

```
You are a senior frontend engineer specializing in shadcn/ui.

You have access to shadcn MCP tools. You MUST use them to verify every component.
Do NOT write implementation code yet. Do NOT guess component names from memory.

## Your task: Component Mapping Plan

Take the UX Structure Plan below and map each section to specific shadcn components.

Rules:
1. Use `list_components` to see all available components before starting
2. Use `get_component` to verify each component exists and check its current API
3. Use `get_blocks` to check if a ready-made block covers any section (prefer blocks over individual components)
4. Write component names EXACTLY as returned by MCP — no variations, no guessing
5. If a section needs multiple components, list all of them

## UX Structure Plan

[PASTE YOUR UX STRUCTURE PLAN FROM STEP 1 HERE]

## Output format

For each section from the plan, produce:

### [Section name]
- **Component(s):** [exact names from MCP]
- **Block available?** [yes: `[block-name]` / no: assemble from components]
- **Why this component:** [1 sentence rationale]
- **Mobile variant:** [if different component or behavior on mobile]

### Installation commands
List all `npx shadcn@latest add [component]` commands needed for this mapping.

### Components NOT found in shadcn
If any section needs something outside shadcn, list it here with a note:
- [Section] → needs [what] → suggest: [Aceternity UI / Cult UI / custom]

Do not write code. Confirm the mapping with the user before proceeding to implementation.
```

## Объяснение

Это ключевой шаг, который большинство пропускает. Типичная ошибка: AI пишет `import { DataGrid } from "@/components/ui/data-grid"` — компонент которого не существует, или существовал в старой версии с другими props.

**Почему именно MCP, а не память модели:**
shadcn/ui активно обновляется. Props меняются, компоненты добавляются, блоки появляются. Модель обучена на данных прошлого — она знает shadcn, но не знает его сегодняшний API. MCP вытаскивает актуальную документацию в реальном времени.

**Правило "blocks > components":**
Shadcn blocks — это готовые составные секции: login form с валидацией, dashboard layout с sidebar, data table с сортировкой и пагинацией. Они тестированы, доступны, консистентны. Если для твоей секции есть block — берёшь его целиком, не собираешь из примитивов.

**Почему "Confirm before implementation":**
После маппинга может оказаться что нужного компонента нет в shadcn (например, rich text editor), или что block покрывает 90% секции но не всё. Это решения, которые нужно принять сознательно — не оставлять AI.

## Вариации / Tips

**Tip: добавь регистры если используешь.**
Если у тебя в `components.json` прописаны регистры (Aceternity UI, Magic UI, Cult UI) — добавь в промпт:
`Also use get_project_registries to see available registry components for animated or special sections.`

**Tip: отдельная колонка "State component".**
Для каждой секции укажи как рендерятся её состояния: Loading state → Skeleton компонент, Error → Alert, Empty → custom placeholder. Это не очевидно из основного маппинга.

**Вариация для форм:**
Для секций с формами добавь: `For form sections, also specify: which validation library (Zod + react-hook-form is shadcn default), and which Form components from shadcn are needed (Form, FormField, FormItem, FormControl, FormMessage).`

## Контекст

Шаг 2 из трёхшагового shadcn pipeline (UX Structure → Component Mapping → Implementation).

shadcn MCP server: официальный MCP от команды shadcn/ui. Инструменты: `get_component`, `get_blocks`, `list_components`. Без GitHub-токена: 60 запросов/час. С токеном: 5000 запросов/час.

## Связь с курсом

**M4, блок F6 (0:33-0:38):** "shadcn MCP server — актуальный API без устаревших props."

Это второй из трёх промптов shadcn pipeline. Используй последовательно:
1. `shadcn-ux-structure-plan.md` — зафиксировать структуру
2. `shadcn-component-mapping.md` (этот файл) — привязать к реальным компонентам
3. `shadcn-final-implementation.md` — написать рабочий код

Соответствует агентам `M4/agents/shadcn-requirements-analyzer/` и `M4/agents/shadcn-component-researcher/` — более детальная версия с отдельным шагом исследования каждого компонента.
