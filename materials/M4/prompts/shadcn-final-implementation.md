# shadcn Pipeline — Step 3: Final Implementation

> **Когда использовать:** После того как Component Mapping Plan (Step 2) утверждён и установочные команды выполнены. Это финальный шаг — написание рабочего кода.
> **Inputs:** UX Structure Plan (Step 1) + Component Mapping Plan (Step 2). Компоненты должны быть уже установлены через `npx shadcn@latest add`.
> **Output:** Рабочий React/TypeScript код с правильными props, типизацией, состояниями (loading/error/empty) и accessibility.

## Промпт

```
You are a senior frontend engineer. Implement the UI based on the plans below.

You have access to shadcn MCP tools. Use them if you need to verify a prop or check exact API.

## CRITICAL RULE: Blocks before components
Before writing any section from scratch — call `get_blocks` first.
If a shadcn block covers this section (even partially), use the block as a base.
Only assemble from individual components if no suitable block exists.

## Plans

### UX Structure Plan
[PASTE UX STRUCTURE PLAN FROM STEP 1]

### Component Mapping Plan
[PASTE COMPONENT MAPPING FROM STEP 2]

## Implementation requirements

### Code quality
- TypeScript: all props typed, no `any`
- Forms: react-hook-form + Zod validation (shadcn default)
- State: useState for local state, specify if you need external state management
- All imports: from exact paths returned by MCP or standard shadcn paths

### All states must be implemented
For every section that has data:
- Loading state: use Skeleton component from shadcn
- Error state: use Alert with variant="destructive"
- Empty state: placeholder with clear call-to-action

### Accessibility
- All interactive elements: aria-label or visible label
- Images: alt text
- Form fields: proper label association via htmlFor / FormLabel

### Mobile-first
- Use Tailwind responsive prefixes: mobile default, then `md:` and `lg:` for larger screens
- Navigation: implement mobile behavior as specified in UX Structure Plan

## Delivery format

For each page/component:
1. File path: `src/components/[ComponentName].tsx`
2. Full component code
3. Brief note: what decisions were made and why (only non-obvious ones)

After completing all components, list:
- Any components that need additional setup (providers, context)
- Any props that the parent component needs to pass
- Any TODO items for non-UI logic (API calls, real data)
```

## Объяснение

Почему Step 3 после двух предыдущих шагов — а не сразу: AI без плана и маппинга делает три вещи одновременно. Принимает UX-решения. Выбирает компоненты. Пишет код. Делает все три плохо, потому что контекст размазан.

После Steps 1 и 2 AI в Step 3 делает только одно: пишет код по чёткой спецификации. Качество кода заметно выше.

**Правило "blocks before components" в действии:**
Shadcn поставляет готовые blocks для типичных задач:
- `dashboard-01` — полный layout с sidebar, header и content area
- `login-01` — форма входа с email/password и валидацией
- `data-table` — таблица с сортировкой, фильтрацией и пагинацией

Каждый из них — десятки строк кода с правильными a11y атрибутами и responsive поведением. Писать то же самое руками — трата времени.

**Почему TypeScript и Zod, а не "просто JS":**
shadcn/ui по умолчанию TypeScript. Все примеры из официальной документации типизированы. Код без типов будет несовместим со стандартными shadcn блоками.

**States — не опция:**
Пустое состояние — не "потом добавим". Пользователь ВСЕГДА увидит пустое состояние при первом запуске. Загрузка — ВСЕГДА при каждом API-запросе. Ошибка — ИНОГДА, но обязательно обработана.

## Вариации / Tips

**Tip: запускай по одной странице.**
Не давай всё приложение за раз. Один промпт = одна страница или крупная секция. Используй `/clear` между страницами (паттерн Milestone + /clear).

**Tip: после имплементации — запусти Step 2 verify.**
После получения кода вставь конкретный компонент обратно в промпт:
```
Check this component against shadcn docs using get_component.
Are there any deprecated props? Any missing required props?
```

**Вариация для форм:**
Добавь в промпт: `Generate the Zod schema first, then build the form around it. Show the schema separately before the component code.`

**Вариация для data tables:**
Если в маппинге есть DataTable block: `Use the shadcn data-table block as the base. Customize columns for [your data shape]. Keep all built-in features (sorting, filtering, pagination).`

## Контекст

Шаг 3 из трёхшагового shadcn pipeline (UX Structure → Component Mapping → Implementation). Правило «blocks > components» — ключевая идея этого шага.

shadcn blocks документация: официальный раздел shadcn/ui. Доступен через MCP инструмент `get_blocks`.

## Связь с курсом

**M4, блок F6 (0:33-0:38):** «3-step pipeline: UX план → Component Mapping (через MCP) → Имплементация (blocks > components).»

Это третий и финальный промпт shadcn pipeline. Используй последовательно:
1. `shadcn-ux-structure-plan.md` — зафиксировать структуру
2. `shadcn-component-mapping.md` — привязать к реальным компонентам
3. `shadcn-final-implementation.md` (этот файл) — написать рабочий код

Соответствует агенту `M4/agents/shadcn-implementation-builder/` — тот же подход в формате sub-agent для Claude Code.
