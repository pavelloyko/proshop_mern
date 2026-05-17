# M4 — Прототипирование инструментов

> **Тема:** От идеи до UI за 15 минут. UX-первый подход, ландшафт инструментов 2026, DESIGN.md как стандарт, дизайн-система как версионируемый артефакт.
> **Сквозной проект:** `proshop_mern` — продолжение M3.

---

## О чём модуль

M4 — про то, как строить интерфейс продуктово: сначала UX, потом UI. Ландшафт инструментов для генерации UI за последний год прошёл пять разных эпох — от browser-builders до pre-code design platforms и встроенных дизайн-режимов в IDE. Сейчас в 2026 у разработчика есть пять категорий инструментов под разные контексты, и выбор между ними — это не вкус, а стратегия.

Ключевой артефакт модуля — `DESIGN.md`. Это то же самое, что `CLAUDE.md` из M2, только для дизайна: статически закодированные правила визуального языка, которые агент читает при каждой генерации UI. С апреля 2026 это открытый стандарт. Файл живёт в корне репо рядом с `CLAUDE.md` и становится единственным источником правды о цветах, типографике, отступах и компонентах.

---

## Что внутри M4/

```
M4/
├── README.md                  ← этот файл
├── homework-spec.md            ← полная спецификация домашки
├── homework-checklist.md       ← чек-лист для самопроверки перед PR
│
├── agents/                    ← промпт-агенты для UX/UI работы
│   ├── README.md              ← как пользоваться агентами
│   ├── ux-designer/           ← UX Designer (premium + core + wireframing/UX-планы из ux-engineer)
│   ├── shadcn-requirements-analyzer/   ← требования → shadcn-термины
│   ├── shadcn-component-researcher/    ← подбор компонентов из реестра
│   ├── shadcn-implementation-builder/  ← генерация кода
│   ├── shadcn-quick-helper/            ← ad-hoc вопросы
│   ├── frontend-developer/             ← не-shadcn куски, интеграция
│   ├── accessibility-expert/           ← a11y проверка (WCAG, ARIA)
│   └── mobile-ui-specialist/           ← мобильные breakpoints
│
├── guides/                    ← гайды (появятся)
│   └── design-md-guide.md     ← как писать и использовать DESIGN.md
│
├── prompts/                   ← готовые промпты для типовых задач
│   ├── reverse-design.md      ← скриншот → DESIGN_SYSTEM.md
│   └── ascii-wireframe.md     ← фиксация структуры до кода
│
├── templates/                 ← шаблоны файлов
│   └── DESIGN.md.template     ← минимальный шаблон DESIGN.md
│
└── cheatsheets/               ← quick-reference
    └── anti-ai-slop.md        ← 12 признаков AI-look и как избежать
```

**Примечание:** папки `guides/`, `prompts/`, `templates/`, `cheatsheets/` появятся по мере наполнения модуля. Ядро M4 — `agents/` и три корневых файла.

---

## Как пользоваться

### Для домашки

1. Прочитайте `homework-spec.md` полностью — там 4 обязательные части и Q&A-блок.
2. Возьмите шаблон из `templates/DESIGN.md.template` как основу для вашего `DESIGN.md`.
3. Агенты из `agents/` — используйте как sub-agents в CC/Cursor или копируйте `prompt.md` в новый чат.
4. Перед сдачей пройдитесь по `homework-checklist.md`.

### Для self-study

- `agents/README.md` — с чего начинать при работе с агентами, какой запускать интерактивно, какой как агент.
- `prompts/reverse-design.md` — если нет дизайнера и референса: скриншот Stripe/Linear/Vercel → `DESIGN_SYSTEM.md` за один промпт.
- `cheatsheets/anti-ai-slop.md` — перед тем как отправлять промпт в browser-builder, пробегитесь по списку запретов.

### Референсы к модулю

| Что | Где |
|-----|-----|
| Агенты (UX, shadcn, a11y) | `agents/` |
| Домашка: спецификация | `homework-spec.md` |
| Домашка: чек-лист | `homework-checklist.md` |
| Гайд по DESIGN.md | `guides/design-md-guide.md` |
| Промпт reverse-design | `prompts/reverse-design.md` |
| Anti-AI-slop шпаргалка | `cheatsheets/anti-ai-slop.md` |

---

## Сквозной проект — proshop_mern

`proshop_mern` — MERN e-commerce приложение, которое мы используем как учебный полигон начиная с M3.

**M3** — вы написали MCP-сервер (3 tools: `get_feature_info`, `set_feature_state`, `adjust_traffic_rollout`) и подняли RAG на документации. `features.json` с 25 фичами лежит в корне репо.

**M4** — добавляем визуальную оболочку:
- Dashboard для управления feature flags (на основе `features.json` из M3)
- Редизайн одной или нескольких страниц proshop_mern
- `DESIGN.md` в корне репо — визуальный язык всего проекта

**M5** — Dashboard оживёт: кнопка Toggle → webhook → n8n-агент → MCP-сервер из M3 меняет реальный флаг. Сейчас (M4) — только UI с mock-данными.

**M6** — агент-аудитор пройдётся по коду M3 + M4 на security и architecture.

---

## Ключевые ссылки

- Агенты: [`agents/README.md`](agents/README.md)
- Домашка: [`homework-spec.md`](homework-spec.md)
- Самопроверка: [`homework-checklist.md`](homework-checklist.md)
- Данные для домашки: [`../M3/project-data/features.json`](../M3/project-data/features.json)
- Спецификация фича-флагов: [`../M3/project-data/feature-flags-spec.md`](../M3/project-data/feature-flags-spec.md)

---

*M4 — HSS AI-dev L1. Следующий модуль: M5 — Агенты и автоматизация.*
