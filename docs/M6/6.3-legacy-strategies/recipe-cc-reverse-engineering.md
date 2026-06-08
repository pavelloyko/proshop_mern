# Рецепт: Reverse Engineering legacy через Claude Code

> **Источник паттерна:** Anthropic Code Modernization (P22 public workflow)
> **Применимость:** незнакомый legacy-модуль до ~250K токенов (подробнее о лимитах — в конце)
> **Тайминг:** ~7-8 минут на модуль (4 шага по 1.5-2 мин каждый)

---

## Когда использовать

Этот рецепт подходит для:
- Изучения незнакомого модуля перед рефакторингом
- Подготовки к code review унаследованного кода
- Создания документации для undocumented legacy
- Генерации базы для characterization tests (Stage 2 homework)

**Не подходит:**
- Модули >300K токенов (context rot — см. раздел «Ограничения» ниже)
- Cross-module invariants (agent stays in own layer, не пересекает HTTP handler)
- Implicit ordering между сервисами (Service A flushes before B checks)

---

## Демонстрационный файл

Все примеры ниже построены на `backend/controllers/userController.js` из проекта [proshop_mern](https://github.com/bradtraversy/proshop_mern) (BradTraversy 2020, ~120 LOC, Express auth).

Это реальный production-стиль код: JWT auth, bcrypt, MongoDB — достаточно сложный чтобы быть полезным примером, достаточно маленький чтобы уместиться в один экран.

---

## Шаг 1 — Понять: описание бизнес-логики (~2 мин)

**Цель:** получить текстовое описание того, что делает код, — словами менеджера, не программиста.

**Промпт-шаблон:**

```
Read /path/to/file. Describe the business logic in plain English.
What does this file do? Who calls it? What invariants does it maintain?
What assumptions does it make about the input data?
Format: markdown, 200-400 words.
```

**Для `userController.js`:**

```
Read backend/controllers/userController.js and backend/middleware/authMiddleware.js.
Describe the business logic in plain English: what endpoints does userController
expose, what business rules does each one enforce, what are the assumptions about
the data, and what invariants does the controller maintain?
Format: markdown, 200-400 words.
```

**Что получаем:**
Текстовое описание на 200-400 слов. На живом файле AI нередко замечает вещи которые неочевидны из кода: например, что `/api/users/login` возвращает и токен и объект пользователя в одном ответе — что нарушает SRP, но является намеренным дизайном.

---

## Шаг 2 — Decision table: все ветвления (~2 мин)

**Цель:** структурировать все if/switch/case в таблицу — чтобы увидеть скрытые ветки.

**Промпт-шаблон:**

```
List all branching points (if/switch/case) with their conditions and outcomes
as a markdown table. Columns: condition, then-action, else-action, edge case.
Include nested conditions as separate rows.
```

**Для `userController.js`:**

```
List all branching points (if/switch/case) in userController.js as a markdown table.
Columns: condition | then-action | else-action | edge case or failure mode.
Include nested conditions as separate rows.
```

**Что получаем:**
Таблица из 10-15 строк. На практике в таблице всплывают ветки которые сложно заметить при линейном чтении кода — например, что один endpoint молча игнорирует несуществующих пользователей вместо возврата 404.

---

## Шаг 3 — Mermaid sequence diagram (~2 мин)

**Цель:** визуализировать execution flow для happy path и как минимум одного error path.

**Промпт-шаблон:**

```
Generate a mermaid sequenceDiagram showing the typical execution flow
for the happy path + 1 error path. Include middleware calls.
Show actor labels clearly.
```

**Для `userController.js` (endpoint login):**

```
Generate a mermaid sequenceDiagram for the login flow in userController.js.
Show: Client → Router → authMiddleware (if applicable) → userController.loginUser
→ DB query → bcrypt.compare → JWT sign → Response.
Include the error path for wrong password.
```

**Что получаем:**
Mermaid-блок который можно вставить в любой markdown-файл и который рендерится в GitHub, Notion, Miro. Визуальный reverse engineering — позволяет объяснить flow коллеге без показа кода.

---

## Шаг 4 — Edge cases list (~1.5 мин)

**Цель:** список граничных случаев — основа для characterization tests.

**Промпт-шаблон:**

```
List edge cases this code handles (or fails to handle). Markdown bullet list.
Separate into: handled correctly / handled incorrectly or partially / not handled at all.
```

**Для `userController.js`:**

```
List edge cases for each endpoint in userController.js. For each:
- Is it handled correctly?
- Is it handled incorrectly or partially?
- Is it not handled at all?
Include: missing user, wrong password, malformed token, race conditions,
concurrent requests, malicious input, partial failures.
```

**Что получаем:**
Bullet-list на 15-25 пунктов. Этот список становится входным контекстом для генерации characterization tests на следующем шаге работы с кодовой базой.

---

## Итоговый артефакт

После 4 шагов у вас есть `specification.md` (~5K токенов):

```
# Specification: userController.js

## 1. Business logic description
[текст из шага 1]

## 2. Decision table
[таблица из шага 2]

## 3. Sequence diagram
[mermaid из шага 3]

## 4. Edge cases
[список из шага 4]
```

Этот файл служит:
1. Документацией для команды
2. Контекстом для следующей сессии (Dump + clear pattern)
3. Базой для написания characterization tests

---

## Dump + clear pattern (важно при длинных сессиях)

Контекст сессии накапливается и деградирует. После получения артефактов:

1. Сохрани specification.md в проект
2. Запусти `/clear` в Claude Code
3. Начни новую сессию с:

```
Read specification.md. Based on this spec, generate characterization tests
for backend/controllers/userController.js covering all edge cases listed in section 4.
```

Новая сессия с чистым контекстом и конкретным заданием даёт значительно лучший результат чем продолжение «грязной» сессии.

---

## Ограничения: 1M context — маркетинг, не практика

Claude Code официально поддерживает 1M токенов контекстного окна. Реальность:

- **Эффективный предел: 250-300K токенов** — Cole Medin (публичный исследователь, тесты 2025-2026) показал, что на больших контекстах «needle-in-haystack» задачи резко деградируют. Модель «помнит» начало и конец, теряет середину.
- **Для монолитов >300K**: делите на сессии по подграфам (один контроллер, один сервис), не пытайтесь загрузить весь backend в один контекст.
- **Для кодовых баз >500K LOC**: рассматривайте специализированные инструменты (CodeConcise / Thoughtworks) которые работают с семантическими подграфами, а не со всем кодом.

Правило активации (если нужна большая контекстная сессия):

```bash
# через env var (Claude Code CLI)
ANTHROPIC_BETAS=context-1m-2025-08-07 claude
```

Работает для модулей ~200K токенов. Для большего — разбивайте.

---

## Дополнительные ресурсы

- Claude Code docs: [docs.anthropic.com/en/docs/claude-code](https://docs.anthropic.com/en/docs/claude-code)
- Anthropic Code Modernization guide (P22): [anthropic.com/research](https://www.anthropic.com/research)
- Karan Prasad «512K reverse engineering» (публичный пост): поиск по «Claude Code reverse engineering 512k context»
- Cole Medin context rot tests: YouTube канал Cole Medin (поиск «Claude Code context window»)
