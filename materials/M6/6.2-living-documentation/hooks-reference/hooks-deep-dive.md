# Claude Code Hooks — подробный гайд: как устроены, как делают, что говорят

> **Официальный источник (каноничный):**
> - **Reference:** https://code.claude.com/docs/en/hooks — полная схема событий, конфиг, JSON I/O, exit codes, async/HTTP/prompt/agent hooks
> - **Guide:** https://code.claude.com/docs/en/hooks-guide — пошаговый туториал «с нуля»
> - **Agent SDK hooks:** https://code.claude.com/docs/en/agent-sdk/hooks — те же события как callbacks в SDK (Python/TS)
>
> Этот документ — синтез официальной документации + практического опыта сообщества (публичные блоги, ссылки внизу). Примеры конфигов — в соседних [`example-hooks/`](../example-hooks/) и [`examples-gallery.md`](./examples-gallery.md).

---

## 1. Что такое hook (одним абзацем)

**Hook** — это пользовательский обработчик (shell-команда, HTTP-endpoint или LLM-промпт), который Claude Code запускает **автоматически** в определённый момент своего жизненного цикла. Хук получает JSON-контекст события (для command-хуков — через **stdin**, для HTTP — в теле POST), может что-то сделать и опционально вернуть **решение** (разрешить/заблокировать/добавить контекст).

**Ключевое свойство — детерминизм.** Инструкцию в `CLAUDE.md` («всегда запускай форматтер после правки») агент выполняет *most of the time*. Hook выполняется **всегда** и его **нельзя обойти промптом или сменой permission-режима**. Это единственный механизм в стеке, который сдвигает поведение с «model compliance» на «system enforcement».

> Из практики сообщества: миграция правил из `CLAUDE.md` в хуки превращает агента «из быстрого наборщика, которого надо нянчить» в «тиммейта, которого можно оставить на пару часов одного» (T. Wiegold).

---

## 2. Где живёт конфиг хуков

**В Claude Code НЕТ отдельной папки `.claude/hooks/`.** Hook = JSON-секция `hooks` в settings-файле.

| Расположение | Скоуп | Шарится в git? |
|---|---|---|
| `~/.claude/settings.json` | все твои проекты | ❌ локально на машине |
| `.claude/settings.json` | один проект | ✅ можно коммитить в репо |
| `.claude/settings.local.json` | один проект | ❌ в gitignore (личное) |
| Managed policy settings | вся организация | ✅ админ-контролируемо |
| Plugin `hooks/hooks.json` | пока плагин включён | ✅ внутри плагина |
| Frontmatter скилла/агента | пока компонент активен | ✅ в самом компоненте |

> Project-level (`.claude/settings.json`) выигрывает у user-level при конфликте. Глобальные и проектные хуки на одно событие **запускаются оба** — не вешай один и тот же blocking-хук на оба уровня, иначе сработает дважды.

---

## 3. Структура конфига — 3 уровня вложенности

```jsonc
{
  "hooks": {
    "PostToolUse": [                       // 1. СОБЫТИЕ — на что реагируем
      {
        "matcher": "Write|Edit",           // 2. MATCHER — когда именно (regex)
        "hooks": [                          // 3. ОБРАБОТЧИКИ — что запустить
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

Три шага: **(1)** выбрать событие → **(2)** matcher-группа фильтрует когда срабатывать → **(3)** один или несколько обработчиков.

### Типы обработчиков (`type`)

| Тип | Что это | Когда брать | Стоимость |
|---|---|---|---|
| `command` | shell-команда (stdin = JSON) | 95% кейсов: формат, линт, блок, лог | 0 токенов, миллисекунды |
| `http` | POST на endpoint (тело = JSON) | внешние сервисы, CI-статусы | сетевой latency |
| `prompt` | мини-LLM-оценщик (Haiku) | субъективная проверка («решает ли код задачу») | ~$0.001/срабатывание |
| `agent` | tool-using субагент | тяжёлая проверка (overnight refactor) | реальная цена, ⚠️ experimental, 60s timeout |

Правило: для частых проверок (десятки раз за сессию, нужно за миллисекунды) — **command**. Agent-хук добавит 2–30 сек latency и тысячи токенов к каждому ответу.

---

## 4. События (event lifecycle)

Три каденции (как часто срабатывает):

**Раз за сессию:** `SessionStart`, `SessionEnd`, `Setup`
**Раз за «ход» (turn):** `UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `StopFailure`
**На каждый вызов инструмента (внутри agentic-loop):** `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`

Полный список ключевых событий:

| Событие | Когда срабатывает | Может блокировать? |
|---|---|---|
| `SessionStart` | старт/возобновление сессии (matcher: `startup`/`resume`/`clear`/`compact`) | — |
| `SessionEnd` | завершение сессии | — |
| `Setup` | `--init-only` / `--init` / `--maintenance` (one-time в CI) | — |
| `UserPromptSubmit` | юзер отправил промпт, ДО обработки | ✅ |
| `PreToolUse` | ПЕРЕД вызовом инструмента | ✅ (главный для prevention) |
| `PostToolUse` | ПОСЛЕ успешного вызова | ❌ (только реакция) |
| `PostToolUseFailure` | после неудачного вызова | — |
| `PostToolBatch` | после батча параллельных вызовов | — |
| `PermissionRequest` / `PermissionDenied` | при диалоге пермиссий / отказе | — |
| `Stop` | Claude закончил ответ | ✅ (форс-продолжение работы) |
| `StopFailure` | ход прерван API-ошибкой (output игнорируется) | — |
| `SubagentStart` / `SubagentStop` | субагент стартовал/закончил | — |
| `Notification` | CC шлёт уведомление (нужен твой ввод) | — |
| `PreCompact` / `PostCompact` | до/после компактификации контекста | — |
| `InstructionsLoaded` | загрузка `CLAUDE.md` / `.claude/rules/*.md` | — |
| `FileChanged` | следимый файл изменился на диске (matcher = имена) | — |
| `CwdChanged` | сменилась рабочая папка (`cd`) — для direnv-стиля | — |

### Matchers (фильтры)

`matcher` — это **regex**, но матчит он РАЗНОЕ в зависимости от события:
- `PreToolUse`/`PostToolUse`/... → по **имени инструмента**: `"Bash"`, `"Edit|Write"`, `"mcp__.*"`
- `SessionStart` → по способу старта: `startup`/`resume`/`clear`/`compact`
- `Notification` → по типу уведомления
- Пустой matcher (`""` или отсутствует) → срабатывает на **каждое** событие этого типа

> ⚠️ Matcher для tool-событий фильтрует **только по имени инструмента**, НЕ по путям/аргументам. Чтобы фильтровать по файлу — проверяй `tool_input.file_path` внутри своего скрипта.

---

## 5. Контракт ввода/вывода

### Ввод (stdin для command-хука) — JSON, например:

```json
{
  "session_id": "...",
  "tool_name": "Write",
  "tool_input": { "file_path": "/path/to/file.js", "content": "..." },
  "permission_mode": "default"
}
```

Первая строка скрипта почти всегда: `input=$(cat)` (читаем stdin) → дальше `jq` по полям.

### Вывод — exit codes (САМОЕ важное и самое частое место ошибок):

| Exit code | Значение | Эффект |
|---|---|---|
| **0** | approve / no-op | тихо, всё ок. **Никакого сообщения юзеру** (by design — не засорять каждый ход) |
| **1** | error | хук упал, **залогировано, но Claude продолжает** — это НЕ блок |
| **2** | **block** | tool-call физически запрещён; твой **stderr** показывается агенту как причина блока |

> Самая частая ошибка security-хуков: используют **exit 1** для блокировки и удивляются, что Claude игнорирует. **Exit 1 не блокирует. Блокирует только exit 2.** Пиши осмысленный stderr на exit 2 («Blocked: force-push to main запрещён, открой PR») — агент это читает и адаптируется.

### JSON-вывод (продвинутый, вместо/вместе с exit code)

- `PreToolUse` → `hookSpecificOutput.permissionDecision`: `"allow"` / `"deny"` / `"ask"` / `"defer"` + `permissionDecisionReason` + `updatedInput`
- `PostToolUse` → `additionalContext` (добавить инфу к результату) или `updatedToolOutput` (заменить вывод до того, как Claude увидит)
- `Stop`-хук использует **другой** enum: `{"ok": true}` / `{"ok": false, "reason": "..."}` (или `approve`/`block`), НЕ `allow`/`deny`

> ⚠️ **Enum зависит от типа хука:** `PreToolUse` → `allow`/`deny`; `Stop` → `approve`/`block` (или `ok`). Перепутаешь — JSON validation error.

---

## 6. Примеры хуков на разные события (готовые фрагменты)

> Полная галерея из 7+ примеров — [`examples-gallery.md`](./examples-gallery.md). Рабочий набор для домашки M6 — [`../example-hooks/settings.example.json`](../example-hooks/settings.example.json). Ниже — по одному примеру на каждый класс триггера.

### 6.1 `PostToolUse` — авто-форматирование после правки файла
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write || true" }]
      }
    ]
  }
}
```
`|| true` — чтобы форматтер на неподдерживаемом типе файла не блокировал правку.

### 6.2 `PreToolUse` — блок опасных команд (нельзя обойти даже в bypass-режиме)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "input=$(cat); echo \"$input\" | jq -r '.tool_input.command' | grep -qE 'rm -rf|git push --force[^-]|migrate reset|DROP TABLE' && { echo 'Blocked: destructive command. Use a safer form or ask the user.' >&2; exit 2; }; exit 0" }]
      }
    ]
  }
}
```
Блокирует `rm -rf`, force-push (но не `--force-with-lease`), `migrate reset`, `DROP TABLE`. `exit 2` + stderr = настоящий блок.

### 6.3 `SessionStart` (matcher `compact`) — переинъекция контекста после компактификации
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [{ "type": "command", "command": "echo 'Напоминание: читай project-index.json для структуры. Запускай тесты перед коммитом. Текущий спринт: <...>'" }]
      }
    ]
  }
}
```
Всё, что хук пишет в stdout, добавляется в контекст Claude как system-reminder. Можно сделать динамичным (`git log --oneline -5`).

### 6.4 `Stop` — форс-верификация (gate перед завершением)
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "input=$(cat); echo \"$input\" | jq -e '.stop_hook_active == true' >/dev/null && exit 0; npm run -s verify && exit 0; echo 'Verification failed — keep working until it passes.' >&2; exit 2" }]
      }
    ]
  }
}
```
Заставляет Claude продолжить работу, если реальная верификация (`npm run verify`) не прошла. **Критично:** проверка `stop_hook_active` в начале — иначе бесконечный цикл (см. gotchas).

### 6.5 `Notification` — десктоп-уведомление, когда Claude ждёт ввода (macOS)
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [{ "type": "command", "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'" }]
      }
    ]
  }
}
```

### 6.6 `PostToolUse` (matcher `Bash`) — audit-log всех команд
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "input=$(cat); echo \"$(date -u +%FT%TZ) $(echo \"$input\" | jq -r '.tool_input.command')\" >> .claude/bash-audit.log" }]
      }
    ]
  }
}
```

---

## 7. Что говорит сообщество (consensus + опыт)

**Консенсус практиков (community guides + RAG-база AI-dev сообщества):**
- **Pre-commit / git-hooks как quality-gate надёжнее инструкций в `CLAUDE.md`/`AGENTS.md`** — агент не закоммитит, пока не пройдут линтер/форматтер/тесты. Это «Definition-of-Done на уровне системы», а не пожелание.
- Хуки — это **guardrail + observability слой**: `PreToolUse` блокирует опасное ДО, `PostToolUse` валидирует/реагирует ПОСЛЕ, всё с **нулём AI-токенов**.
- Хуки = детерминизм. Без них ты полагаешься на то, что агент *вспомнит* про форматтер/перезапуск тестов/перезагрузку контекста.

**Стадии внедрения (T. Wiegold, 4 stages):**
1. 5-строчный форматтер (`PostToolUse: Edit|Write → prettier`) — ставить сегодня в каждый проект.
2. Bash-guard от опасных команд (`PreToolUse`) — в user-global `~/.claude/settings.json`, чтобы везде.
3. Audit-логирование — когда запускаешь агента unattended или отдаёшь его работу тиммейтам.
4. Форс-верификация (`Stop`-хук с реальными командами) — когда хочешь доверять длинным сессиям.

**Почему это не теория — реальные инциденты 2025-2026:**
- GitHub issue #10077: Claude выполнил `rm -rf` на home-директории. #12637: создал литеральную папку `~`, glob-расширение снесло содержимое home. Оба — в **обычном** permission-режиме, не bypass.
- `.env` leak: CC рутинно читает `.env` (и обходит deny через `docker compose config`, `printenv`, `cat`). Появились готовые PreToolUse-плагины (EnvShield/NoNuke), блокирующие ~15 secret-паттернов и ~60 деструктивных команд.

> Вывод сообщества: промпты и memory-rules **недостаточны** — их обходит prompt injection, edge-case или просто «плохой день модели». Hook — это то, что модель **не может переопределить**, что бы она ни решила.

---

## 8. Gotchas (подводные камни — собрано из практики)

1. **Stop-хук → бесконечный цикл.** Всегда проверяй `stop_hook_active` в начале и `exit 0`, если `true`. «Каждый разработчик учится этому один раз» (часто — дважды).
2. **`PostToolUse` не может отменить** — к моменту срабатывания файл уже записан. Для *prevention* — `PreToolUse`, для *reaction* — `PostToolUse`.
3. **Exit 1 ≠ блок.** Блокирует только **exit 2**. Exit 1 = ошибка хука, Claude продолжает.
4. **Разные enum'ы у разных хуков:** `PreToolUse` → `allow`/`deny`; `Stop` → `approve`/`block`. Перепутал → JSON validation error.
5. **Env-переменные НЕ переживают границу субпроцессов.** Поставил переменную в `PreToolUse`, ждёшь в `PostToolUse` — будет undefined (разные процессы).
6. **Параллельность: last-write-wins.** Несколько `PreToolUse`-хуков, переписывающих `updatedInput` одного инструмента → порядок недетерминирован. Не давай двум хукам драться за одно поле.
7. **`additionalContext` — кап 10 000 символов** и «протухает» на resume. Время-зависимые данные клади в `SessionStart` (он перезапускается с `source: "resume"`), не в `PostToolUse`.
8. **Загрязнение shell-профиля.** Безусловный `echo` в `~/.zshrc` попадёт в stdout хука и сломает JSON-парсинг. Оборачивай интерактивный вывод в `[[ $- == *i* ]]`.
9. **Тихая зависимость от `jq`.** Нет `jq` → оба `jq`-вызова молча падают, переменные пустые, хук «одобряет всё» = ноль enforcement без ошибки. Добавь явный `command -v jq` check.
10. **macOS notification permission.** `osascript ... display notification` идёт через Script Editor, которому нужно разрешение в System Settings → Notifications. Без него уведомления молча не показываются.
11. **Хуки одобрены = тихо.** Успешный хук не печатает ничего (никакого «Ran 1 hook»). Видимый вывод даёт только блок. Поэтому нужен **тест-набор**, а не «проверю глазами».
12. **Невалидный `settings.json` молча игнорируется.** Проверяй `jq . .claude/settings.json` после правки. Скрипт исполняемый (`chmod +x`)? Stdin читается (`input=$(cat)` в начале, иначе хук виснет)?
13. **Версии ломали хуки.** Были релизы, где хуки не грузились (issue #11544) или ломались целиком (v2.0.31). Держи `claude --version` под контролем при отладке.
14. **`PermissionRequest` не срабатывает в headless** (`-p`). Для автоматических permission-решений в CI используй `PreToolUse`.

---

## 9. Mental model (как думать про хуки)

- **Separate concerns** — не клади логику `PostToolUse` в `PreToolUse`, не используй `Stop` для обработки падения одного инструмента. Каждая фаза — своя ответственность.
- **Prevention vs reaction** — `PreToolUse` предотвращает (может блокировать), `PostToolUse` реагирует (не может отменить).
- **System enforcement > model compliance** — хук там, где цена промаха = сломанный main, утёкший секрет, проигнорированный lint. CLAUDE.md = контекст, skills = рецепты, **hooks = принуждение**.
- **Тестируй на dummy-репо.** Хуки, трогающие git/npm, могут молча сломать. Прогоняй сценарии на тестовом репозитории.

---

## 10. Связь с домашкой M6

- **Этап 3 (авто-документирование):** настрой `PostToolUse` (Write|Edit) → авто-обновление `project-index.json` (см. [`../example-hooks/`](../example-hooks/)). Пришли скриншот настроенных хуков (local `settings.json` в gitignore — не коммитится).
- **Этап 1-2 (агент-аудитор / рефакторинг):** `PreToolUse` Bash-guard + `Stop`-верификация — чтобы агент не сломал репо и не «закончил» с падающими тестами.
- Правило в `CLAUDE.md`/`AGENTS.md` «перезапусти тесты перед завершением» работает ~70-80%; тот же эффект через `Stop`-хук — 100%.

---

## Источники

**Официальная документация Claude Code (каноничный источник):**
- Hooks reference — https://code.claude.com/docs/en/hooks
- Hooks guide (туториал) — https://code.claude.com/docs/en/hooks-guide
- Agent SDK hooks — https://code.claude.com/docs/en/agent-sdk/hooks
- Plugins reference (plugin hooks) — https://code.claude.com/docs/en/plugins-reference

**Практический опыт сообщества (публичные блоги):**
- T. Wiegold — «Claude Code Hooks: From Linting to Hardened AI Workflows» — https://thomas-wiegold.com/blog/claude-code-hooks/
- Claude Lab (M. Hirokawa) — «Complete Field Guide to All Hook Types» — https://claudelab.net/en/articles/claude-code/claude-code-hooks-complete-guide-2026
- A. Kothari — «What is a hook in Claude Code» — https://amitkoth.com/what-is-a-hook-claude-code
- J. Kontra — «Guardrails that actually work» — https://jakubkontra.com/en/blog/claude-code-hooks-complete-guide
- The Prompt Shelf — «10 Real-World Examples» — https://thepromptshelf.dev/blog/claude-code-hooks-guide/

---

*Документ собран для курса HSS AI-Driven Development L1, Модуль 6 (Живая документация). Ресёрч: официальная документация Claude Code + публичные practitioner-блоги + срез community-консенсуса. Дата: 2026-05-26.*
