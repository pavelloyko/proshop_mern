# Cheatsheet: 10 best practices vibe-coding

> Канонический список из docs.lovable.dev, lovable-prompts.com, idlen.io.
> Применимо к Lovable, Bolt, Claude Code и любому AI-агенту в UI-задачах.

---

## Таблица правил

| # | Правило | Почему | Пример |
|---|---------|--------|--------|
| 1 | **Iterate, не rewrite** | Rewrite = потеря всего предыдущего контекста | `«Increase hero py to 80px. Don't touch colors or typography.»` вместо «переделай hero» |
| 2 | **Plan Mode между milestones** | Без плана модель делает «что логично», не «что нужно» | Перед каждым новым блоком: `/plan` → описываешь задачу → валидируешь перед запуском |
| 3 | **Build by component, не full page** | Больше промпт = больше галлюцинаций | hero → nav → pricing card → footer. Не «сделай всю pricing страницу» |
| 4 | **Real content в промптах** | Lorem ipsum скрывает UX-проблемы до финала | Реальный заголовок, реальный CTA-текст, реальные названия с первого промпта |
| 5 | **Визуальный стиль BEFORE function** | Функциональный рефакторинг ломает стиль | Фиксируй DESIGN.md и CSS variables до добавления логики |
| 6 | **Guardrails «не трогай X»** | Без защиты модель «оптимизирует» работающее | После каждой итерации: `«Don't touch nav/auth. Only modify hero section.»` |
| 7 | **Mobile breakpoints явно** | По умолчанию AI верстает только под desktop | `«Mobile <640px: stack в 1 col, 14px base. Tablet 640-1024: 2 col. Desktop >1024: 3 col.»` |
| 8 | **«I am frustrated...» pattern** | Эмпирически активирует другой режим внимания | `«I am frustrated. The previous attempt didn't solve [X]. Here is specifically what needs to change: ...»` |
| 9 | **Явно запрашивать a11y** | Skeleton loaders, ARIA, контраст 4.5:1 не появляются сами | Добавка к промпту: `«skeleton loaders for async content, ARIA labels, contrast ≥4.5:1»` |
| 10 | **Milestone + /clear (40-50% контекста)** | Агент теряет нить при долгих диалогах | Разбей на 3-4 milestone → сохрани `progress.md` → `/clear` → следующий milestone стартует с ссылки |

---

## Детали по ключевым правилам

### Правило 8 — «I am frustrated»

Lovable docs прямо рекомендует этот паттерн. Работает когда AI делает не то
во второй-третий раз:

```
I am frustrated. The previous attempt didn't solve [X].
Here is specifically what needs to change:
- [конкретная проблема 1]
- [конкретная проблема 2]
Don't touch anything else.
```

### Правило 10 — Milestone + /clear

Разбивка для крупного Dashboard:
1. Milestone 1: каркас + DESIGN.md
2. Milestone 2: компоненты
3. Milestone 3: state management
4. Milestone 4: polish + a11y

После каждого: `progress.md` → `/clear` → новый чат.

> «Context rot убивает большие проекты. Milestone + clear — стандартный паттерн защиты.»

---

## Быстрые добавки к любому промпту

```
- Don't touch [nav / auth / pricing]. Only modify [hero].
- Mobile (<640px): stack to 1 column.
- Add skeleton loaders for all async content.
- Every interactive element: hover, focus, loading, empty states.
```

---

## Связанные материалы

- `../prompts/lovable-bring-your-vibe.md` — полный шаблон промпта под Lovable
- `../prompts/screenshot-fix-loop.md` — итерация через скриншот
- `12-signs-of-ai-look.md` — guard-rails против AI-look
- `pre-flight-checklist.md` — проверка промпта перед отправкой

---

## Источники

- [docs.lovable.dev](https://docs.lovable.dev) — Plan Mode, AGENT.md
- [lovable-prompts.com](https://lovable-prompts.com) — каталог промптов
