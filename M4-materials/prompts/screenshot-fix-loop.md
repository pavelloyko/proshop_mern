# Screenshot fix-loop: скрин → правка → скрин

> **Когда использовать:** После любой генерации UI — вместо описания проблем по памяти или вместо полного rewrite. Модель видит то, что видишь ты, и исправляет только видимое.
> **Inputs:** скриншот текущего состояния UI (Ctrl+V в Claude Code, или attach в чат), список наблюдаемых отклонений от DESIGN.md.
> **Output:** исправленный код без изменения логики. Только то, что видно на скриншоте.

## Промпт

```
[Paste screenshot of current UI via Ctrl+V]

The current UI has these issues vs DESIGN_SYSTEM.md:
- [issue 1 — e.g., "Card borders are heavy 2px solid, should be 1px at 10% opacity"]
- [issue 2 — e.g., "Hero padding is cramped — py-3 instead of py-12"]
- [issue 3 — e.g., "Font is Inter, should be Manrope per DESIGN_SYSTEM.md §2"]

Fix only the visible problems listed above.
Do NOT touch: logic, state management, API calls, routing.
Follow DESIGN_SYSTEM.md for correct values.
After fixing, tell me what exactly you changed and in which files.
```

## Объяснение

Описывать UI-проблемы словами — ненадёжно. «Карточки выглядят тяжело» значит разное для разных людей. Скриншот в контекст — точный источник: модель видит то же самое, что видишь ты, и может обратиться к конкретным пикселям, цветам, отступам.

Паттерн работает потому, что современные мультимодальные модели умеют читать UI из скриншота лучше, чем парсить длинное текстовое описание. Они буквально видят «этот отступ меньше 24px» или «этот шрифт не Manrope». Это быстрее, чем объяснять, и точнее, чем «переделай красиво».

Явный запрет «Do NOT touch logic» защищает от регрессий. Без этой фразы модель может «оптимизировать» соседние компоненты или переписать рабочий стейт, пока правит стили. Это главная причина регрессий в vibe-coding. Список изменений в конце («tell me what you changed») даёт возможность сделать git diff перед принятием правок.

## Вариации

**Вариация A — если нет открытого preview (Claude Code без браузера):**

```
I can't see the render directly. Please:
1. Tell me what URL or component to open for preview.
2. I'll take a screenshot and paste it back.
3. Then fix only visible issues vs DESIGN_SYSTEM.md.

What should I open to see [component name]?
```

**Вариация B — итерация с ручным скетчем (для быстрого UX-фиксинга):**

```
[Attach: photo of hand-drawn sketch or rough wireframe on paper]

This sketch shows how I want the layout to look.
Please refactor [component name] to match this structure.
Keep all existing colors, typography and spacing from DESIGN_SYSTEM.md.
Only change the layout structure to match the sketch.
Don't touch logic, state, or API calls.
```

**Вариация C — автоматический loop через Playwright MCP (для Claude Code):**

```
Take a screenshot of the current state of [URL or component].
Compare it against DESIGN_SYSTEM.md.
List all visual violations you find.
Then fix them one by one, taking a new screenshot after each fix to verify.
Stop when the UI matches DESIGN_SYSTEM.md. Report what you changed.
```

Вариация C требует подключённого Playwright MCP — агент делает скриншоты сам, без участия человека.

## Контекст

Паттерн screenshot-back-into-context подтверждён в нескольких независимых практиках vibe-coding 2026 года. В Claude Code: `Ctrl+V` для вставки изображения из буфера работает нативно.

## Связь с курсом

Блок M4 F8 (практика итераций на дизайне) и связь с M3 (Playwright MCP + visual verification). Вариация C — прямая реализация sub-agent review паттерна из F7 DESIGN.md блока. Это замыкание петли: DESIGN_SYSTEM.md задаёт стандарт, screenshot-loop его верифицирует.
