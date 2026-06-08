# Milestone + /clear: борьба с «деменцией агента»

Этот гайд описывает паттерн работы с длинными задачами в AI-агентах: как избежать деградации качества при разработке сложного Dashboard или многостраничного интерфейса. Проблема называется «деменция агента» — при долгих диалогах автосжатие контекста убивает важные детали.

---

## TL;DR

- При длинных диалогах агент теряет нить: автосжатие убивает детали, агент повторяет уже сделанное.
- Решение: 3-4 milestone с явным сохранением прогресса перед `/clear`.
- После каждого milestone: `progress.md` → `/clear` → следующий milestone ссылается на файл.
- Держать загрузку контекстного окна в 40-50% — не добавлять файлы «на всякий случай».
- Директива в CLAUDE.md защищает от пропуска шага.

---

## Pain point: «деменция агента»

AI-агент хранит историю разговора в контекстном окне. При достаточно длинном диалоге — несколько часов работы над Dashboard — происходит несколько вещей одновременно:

**Автосжатие (auto-compact):** когда окно заполняется, агент автоматически сжимает старые части диалога. Детали теряются. Конкретные решения («мы используем shadcn Card с padding 24px, не 16px») заменяются на общие формулировки. Агент «забывает» архитектурные решения.

**Context rot (деградация контекста):** агент продолжает работать, но с неполными данными. Начинает повторять уже сделанное, нарушать принятые решения, игнорировать DESIGN.md. CLAUDE.md instructions drift — правила дизайн-системы перестают применяться.

**Эффект длинного хвоста:** чем длиннее диалог, тем больше «мусора» в начале. Агент тратит токены на переработку нерелевантного контекста вместо работы над задачей.

---

## Решение: 3-4 milestone с /clear

Разбиваешь задачу на логические этапы. После каждого этапа — явное сохранение прогресса, очистка контекста, свежий старт с ссылкой на сохранённый файл.

### Схема для Dashboard (4 milestone)

| Milestone | Что делаем | Артефакт |
|---|---|---|
| **M1: Каркас** | Routing + layout структура + пустые компоненты-заглушки | `progress-m1.md` |
| **M2: Компоненты** | Заполнить каждый компонент контентом и данными | `progress-m2.md` |
| **M3: Стейт** | State management, API интеграция, loading/error состояния | `progress-m3.md` |
| **M4: Стили** | Pixel-polish под DESIGN.md, responsive, accessibility | `progress-m4.md` |

### Процедура после каждого milestone

**Шаг 1. Сохранить progress.md перед завершением:**

```
Before we proceed, save a summary to progress-m1.md:
- What was completed in this milestone
- Key architectural decisions made
- List of files created or modified
- What milestone 2 needs to do
- Any open questions or TODOs
```

**Шаг 2. Выполнить `/clear`** — очистить контекст чата полностью.

**Шаг 3. Начать новый milestone со ссылки на файл:**

```
Read progress-m1.md and continue to milestone 2.
Don't redo anything from milestone 1.
Milestone 2 goal: fill each component with real content and data.
```

---

## Правило 40-50% загрузки контекста

Не добавляй файлы «на всякий случай» — это создаёт шум и ускоряет деградацию. Держи загрузку контекстного окна в 40-50%.

**Что включать в контекст:**
- `CLAUDE.md` (всегда)
- `DESIGN.md` (при UI-работе)
- `progress-mN.md` предыдущего milestone
- Только те файлы компонентов, которые активно меняются сейчас

**Что не включать:**
- Весь src/ сразу
- Файлы, которые «могут пригодиться»
- Прошлые progress.md (только последний)

---

## Директива в CLAUDE.md

Добавь в CLAUDE.md проекта, чтобы агент не забывал про milestone-процедуру:

```markdown
## Dashboard development rule

After each milestone:
1. Save progress.md with:
   - What was completed
   - Key decisions made
   - File list created/modified
   - What the next milestone needs to do
2. Wait for user to confirm progress saved
3. Do NOT proceed to next milestone without /clear

Context window target: 40-50% max.
Do not add files to context unless actively needed.
```

---

## Практический пример: Dashboard для Feature Flags

Предположим, задача — создать Dashboard для управления feature flags (проект из M3).

**M1: Каркас (15-30 минут)**
- Routing: `/dashboard`, `/dashboard/flags`, `/dashboard/settings`
- Layout: sidebar + main content area + topbar
- Пустые компоненты-заглушки: `<FlagsTable />`, `<FlagEditor />`, `<StatsOverview />`
- Ничего не заполнено — только structure

Сохраняем `progress-m1.md`, делаем `/clear`.

**M2: Компоненты (30-60 минут)**
- `<FlagsTable />` — shadcn DataTable block с колонками: name, status, rollout%, environment
- `<FlagEditor />` — shadcn Sheet (sidebar drawer) с формой: Toggle, Input, Slider
- `<StatsOverview />` — shadcn Card x3: total flags, active, rollout average
- Используем реальные данные из fixtures, не lorem ipsum

Сохраняем `progress-m2.md`, делаем `/clear`.

**M3: Стейт (20-40 минут)**
- React Query для загрузки списка флагов из API
- Optimistic updates при toggle флага
- Loading states: shadcn Skeleton в таблице
- Error states: shadcn Alert при сбое запроса

Сохраняем `progress-m3.md`, делаем `/clear`.

**M4: Стили (15-30 минут)**
- Pixel-polish под DESIGN.md: проверить spacing, цвета, типографику
- Responsive: мобильный sidebar → bottom sheet
- Accessibility: ARIA labels, keyboard navigation, focus rings
- UI reviewer subagent — финальный аудит

---

## Когда паттерн особенно важен

- Разработка Dashboard с 5+ компонентами
- Длинная рефакторинг-сессия (более 1-2 часов)
- Работа с AI-агентом над проектом несколько дней подряд
- После любой задачи, где агент уже начал повторять сделанное или нарушать DESIGN.md

---

## Сводка / Cheat sheet

```
Симптомы «деменции агента»:
  - Повторяет уже сделанное
  - Нарушает DESIGN.md (неправильные цвета, отступы, шрифт)
  - Спрашивает про решения, которые уже приняли
  - Контекст-окно > 60-70%

Процедура:
  1. [Любой момент] → сохрани progress.md
  2. /clear
  3. Прочитай progress.md → продолжай

4 milestone для Dashboard:
  M1: Каркас           (routing + пустые компоненты)
  M2: Компоненты       (реальный контент)
  M3: Стейт            (API + loading/error)
  M4: Стили            (pixel-polish + a11y)

Правило загрузки: 40-50% окна — не добавляй «на всякий случай»
```

---

## Cross-refs

- `guides/design-md-as-2026-standard.md` — почему DESIGN.md дрейфует и как sub-agent enforcement это решает
- `guides/pixel-perfect-verification.md` — финальный аудит после M4
- `guides/shadcn-pipeline.md` — shadcn компоненты для M2 milestone
- `guides/tools-landscape-2026.md` — Milestone + /clear упомянут в context Lovable best practices

## Источники

- [docs.lovable.dev](https://docs.lovable.dev) — Plan Mode и milestone паттерн
