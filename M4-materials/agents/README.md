# M4 — Agents (промпты для прототипирования)

Подборка агент-промптов для прототипирования UI: UX → UI → shadcn компоненты → frontend.

> **Статус (2026-05-04):** консолидировано. У каждого агента — единый `prompt.md` без манифестов. `ux-designer-basic` и `ux-engineer` упразднены, контент влит в соответствующие агенты.

## Состав

| Папка | Что | Когда вызывать |
|---|---|---|
| `ux-designer/` | UX Designer (объединённая v2.0.0: premium + basic core + ux-engineer wireframing) | До дизайна. Брейнштормишь сценарии, делаешь user journey, ASCII wireframes, UX-планы, design system |
| `accessibility-expert/` | Accessibility Expert (WCAG 2.1/2.2, screen readers, semantic HTML) | Для DESIGN.md секции a11y. Часто закрывает AI-slop баги (contrast, focus, ARIA) |
| `mobile-ui-specialist/` | Mobile UI Specialist (iOS/Android, 44pt touch targets) | Если делаешь мобильную часть — для веб-курса опционально |
| `shadcn-requirements-analyzer/` | shadcn Pipeline 1/4 — переводит business-требования в shadcn-термины | Когда есть scope от UX Designer'а — первый shadcn-агент |
| `shadcn-component-researcher/` | shadcn Pipeline 2/4 — подбор конкретных компонентов из registries (содержит `library-rule-example.mdc` как эталонный workflow) | После Requirements Analyzer'а |
| `shadcn-implementation-builder/` | shadcn Pipeline 3/4 — генерация кода на shadcn | После Component Researcher'а. Запускается как sub-agent |
| `shadcn-quick-helper/` | shadcn Ad-hoc — быстрые вопросы вне линейного pipeline | По вызову, параллельно с любой стадией |
| `shadcn-components/` | **Shared config** для всех 4 shadcn-агентов: `components.json` (35+ registries) + README | Не агент, а справочник. Положи `components.json` в корень проекта |
| `frontend-developer/` | Frontend Developer (React/Vue/Angular, state, styling, perf, a11y, testing) + Wireframe handoff appendix | Когда стек не shadcn ИЛИ поверх кастом-дизайна. Получает wireframes от UX Designer'а |

## Как использовать

Два варианта:

1. **Как sub-agent в Claude Code / Cursor / Codex** — положи `prompt.md` рядом с конфигурацией агентов своего IDE
2. **Просто в чат** — скопируй `prompt.md` в новый чат и работай с ним напрямую

## Pipeline (как они складываются)

```
UX Designer (диалог) → требования + сценарии + wireframes + DESIGN.md
        ↓
shadcn Requirements Analyzer (1/4) → требования в shadcn-терминах
        ↓
shadcn Component Researcher (2/4) → подбор компонентов из registries
        ↓ (читает library-rule-example.mdc + shadcn-components/components.json)
shadcn Implementation Builder (3/4) → код
        ↓
Frontend Developer → интеграция, не-shadcn куски, performance, a11y, testing

+ Accessibility Expert       — на любом этапе для a11y-аудита
+ Mobile UI Specialist        — если есть мобильная часть
+ shadcn Quick Helper         — для ad-hoc вопросов
```

В роли UX Designer / Requirements Analyzer / Component Researcher — **сам входишь**, брейнштормишь.
Implementation Builder и Frontend Developer — **запускаешь как агентов** (sub-agent режим).

## История консолидации (2026-05-04)

- ✅ `ux-designer-basic` влит в `ux-designer/` → v2.0.0
- ✅ `ux-engineer` (только manifest, без prompt) распилен:
  - 173 строки wireframing / UX-планы / handoff → `ux-designer/prompt.md`
  - 72 строки «UX Handoff Expectations» → `frontend-developer/prompt.md`
  - папка удалена
- ✅ Все agents/* консолидированы: `manifest.md` + `manifest.yaml` + `prompt.md` → один `prompt.md`
- ✅ Добавлена `shadcn-components/` с shared `components.json` (35+ registries) + README
- ✅ `library-rule-example.mdc` (Cursor-rule, эталонный workflow) перенесён в `shadcn-component-researcher/`

## Контекст

Промпт-агенты адаптированы для модуля M4 курса HSS AI-Driven Development L1 (2026-05).
