# Cheatsheet: Pre-flight checklist перед UI-промптом

> 7 пунктов, которые нужно проверить ПЕРЕД отправкой промпта на генерацию UI.
> Принцип: «constraint specificity is the moat» — чем точнее описал что нельзя, тем лучше результат.

---

## 7-point checklist

- [ ] **Все цвета — дизайн-токены, не raw hex.**
  Используй `var(--color-*)` или `var(--primary)` из `DESIGN.md`. Никаких `#3b82f6` напрямую в промпте.

- [ ] **No box shadows.**
  Глубина = только через разницу фонов (3 уровня: page bg → card bg → card-alt bg).
  Если нужна тень — это признак, что не хватает контраста в палитре.

- [ ] **Typography scale явно, с pixel values.**
  Не «большой заголовок» — а `H1 48px / H2 32px / body 16px / caption 12px`,
  `line-height: 1.5 body / 1.2 headings`, `tracking: -0.02em headings`.

- [ ] **Card pattern описан один раз, применяется везде.**
  Один канонический card = `padding 24px, border 1px solid var(--border), radius 12px, bg var(--card)`.
  Не разные карточки на разных страницах одного проекта.

- [ ] **Mobile layout явно указан.**
  Breakpoints в каждом промпте: `<640px` / `640-1024px` / `>1024px`.
  Количество колонок, base font-size, поведение nav — всё явно.

- [ ] **Dark mode через CSS variables, не `dark:` prefixes.**
  `--bg`, `--fg`, `--card`, `--border` меняются в `[data-theme="dark"]`.
  Никаких `dark:bg-gray-900` — это не система, это хак.

- [ ] **No "click here".**
  Каждая кнопка — purposeful label: `«Начать бесплатно»`, `«Скачать отчёт»`, `«Попробовать демо»`.
  «Узнать больше» и «click here» запрещены.

---

## Бонус: 4 финальных вопроса перед отправкой

Если хоть один ответ «нет» — переписывай промпт.

1. Я указал шрифт явно (НЕ Inter)?
2. Я приложил референс или `DESIGN.md` в контекст?
3. Я ограничил scope (одна секция, не вся страница)?
4. Я указал interactive states (hover / focus / loading / empty)?

---

## Как использовать системно

Добавь этот блок в начало каждого UI-промпта для Lovable/Bolt/Claude Code:

```
Before generating any UI:
- Colors: design tokens only (var(--primary), not hex)
- No box shadows — depth via bg contrast
- Typography: H1 48px / H2 32px / body 16px
- Card pattern: [describe once]
- Mobile: [describe breakpoints]
- Dark mode: CSS variables, not dark: prefixes
- Buttons: purposeful labels, no "click here"
```

Полная версия guard-rails: `../prompts/anti-ai-slop-guards.md`

---

## Связанные материалы

- `12-signs-of-ai-look.md` — полная таблица 12 AI-паттернов
- `10-vibecoding-best-practices.md` — системные правила итерации
- `prompt-kit-5-templates.md` — готовые промпты для copy-paste
- `../prompts/anti-ai-slop-guards.md` — полный блок Design Principles

---

## Контекст

Чеклист собран из публичных кейсов соло-разработчиков и маркетологов 2026, которые без команды собирают полнофункциональные продукты через AI-агенты. Общий паттерн: «no shadows» + design tokens система → consistency без дизайнера.
