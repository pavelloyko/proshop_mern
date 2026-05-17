# shadcn Pipeline — Step 1: UX Structure Plan

> **Когда использовать:** Первый шаг перед написанием любого кода с shadcn. Запускай после того как определился с требованиями (через Question Burst или UX Designer агент). Фиксирует навигацию и иерархию страниц ДО того, как AI начнёт "творить" визуально.
> **Inputs:** Описание приложения (что делает, кто пользователь, основные сценарии). Можно подать ASCII wireframe если уже есть.
> **Output:** Дерево секций с навигацией, иерархией страниц, ключевыми CTA и состояниями. БЕЗ кода — только структурный план.

## Промпт

```
You are a senior UX engineer. Your task is to create a UX Structure Plan.

Do NOT write any code. Do NOT pick components yet. Do NOT describe visual styles.
Focus only on: navigation structure, page hierarchy, user actions, and states.

## Application context

[DESCRIBE YOUR APPLICATION: what it does, who uses it, main user scenarios]

## Deliver a UX Structure Plan in this format:

### Navigation
- Navigation type: [top nav / sidebar / breadcrumbs / tabs / bottom bar]
- Navigation items: list all top-level destinations
- Active state behavior: [what changes when user is on a section]
- Mobile behavior: [how navigation collapses/transforms on small screens]

### Page / Screen Hierarchy
For each main page or screen, describe:
- **[Page name]**
  - Purpose: [one sentence — what the user accomplishes here]
  - Sections (in order from top to bottom):
    1. [Section name] — [what it contains, why it's in this position]
    2. [Section name] — [...]
  - Primary CTA: [what is the main action, where is it positioned]
  - Secondary actions: [any other key interactions]

### States to design
For each page, list the states that must exist:
- Empty state: [what the user sees when there's no data yet]
- Loading state: [what shows while data is fetching]
- Error state: [what shows when something goes wrong]
- Success state: [confirmation after an action]

### User flow summary
Describe the most common user journey in 3-5 steps:
1. User arrives at [page] because [reason]
2. User sees [section] and does [action]
3. ...

Do not start implementing. Wait for confirmation of this plan before moving to component mapping.
```

## Объяснение

Без этого шага AI делает что умеет: лепит generic layout. Sidebar слева, content справа, header сверху. Это не плохо само по себе — но это решение принятое по умолчанию, а не осознанно.

UX Structure Plan форсирует осознанные решения ДО начала кода. Три эффекта:

1. **Ты видишь проблемы раньше.** Если навигация не помещается в 4 пункта — значит scope слишком большой для MVP. Видно на плане, не после недели работы.

2. **AI не галлюцинирует структуру.** В следующих шагах (Component Mapping, Implementation) AI работает по твоему плану, а не придумывает архитектуру заново.

3. **Состояния зафиксированы.** Пустые экраны, загрузка, ошибки — студенты про это забывают. В плане они видны явно.

**Почему "Do NOT write any code" в промпте:** без этого ограничения GPT/Claude начинают писать JSX на втором абзаце. Ты теряешь итерационный момент — план сложно поменять когда он уже в коде.

## Вариации / Tips

**Вариация для лендинга:**
Замени "Page / Screen Hierarchy" на секции лендинга. Используй User Journey First паттерн: Hero → Features → Social Proof → CTA.

**Вариация для Dashboard:**
Особенно важен раздел States: dashboard с пустой БД vs с данными — разный UX. Добавь: "First-time user state: [what user sees before any data exists]".

**Tip: итерируй план текстом.**
После получения плана — правь словами ("перемести Notifications в sidebar, не в top nav"), не кодом. Это быстро и дёшево. Только когда план устраивает — переходи к шагу 2.

**Tip: сохрани план в файл.**
Положи UX Structure Plan в `docs/design/[feature-name]/ux-structure.md`. Step 2 (Component Mapping) будет ссылаться на него явно.

## Контекст

Шаг 1 из трёхшагового shadcn pipeline (UX Structure → Component Mapping → Implementation). На этом шаге фиксируется UX-логика в виде структурированного плана — без единой строки кода. Дальше планы переходят в Step 2 (Component Mapping через shadcn MCP) и Step 3 (Implementation с правилом «blocks > components»).

## Связь с курсом

**M4, блок F6 (0:33-0:38):** "Готовые компонентные библиотеки как base layer AI-генерации."

Это первый из трёх промптов shadcn pipeline (Step 1 → Step 2 → Step 3). Используй последовательно:
1. `shadcn-ux-structure-plan.md` (этот файл) — зафиксировать структуру
2. `shadcn-component-mapping.md` — привязать секции к реальным shadcn компонентам
3. `shadcn-final-implementation.md` — написать рабочий код

Соответствует агенту `M4/agents/shadcn-requirements-analyzer/` — более подробная версия с MCP-интеграцией.
