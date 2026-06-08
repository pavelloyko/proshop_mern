# Claude Code hooks — reference и каталог типов

> **Что это:** обзор всех типов hook'ов Claude Code, когда срабатывают, что получают на stdin, что можно делать. Плюс библиотека готовых примеров.

> **Официальная дока:** https://code.claude.com/docs/en/hooks

---

## ⚡ Что такое hook (одной фразой)

Hook — это **shell-команда**, которую Claude Code запускает **гарантированно** на определённом событии (например, после Write). Hook конфигурируется в `.claude/settings.json` (или `settings.local.json`). **Не файл в папке** — JSON-конфиг.

---

## 📋 Все 8 типов hook'ов Claude Code

| # | Event | Когда срабатывает | Кейс использования |
|---|---|---|---|
| 1 | **`SessionStart`** | При старте `claude` (новая сессия) | Загрузить контекст, напомнить AI читать `project-index.json` |
| 2 | **`UserPromptSubmit`** | На каждое сообщение пользователя (перед обработкой) | Audit log промптов, redact PII, добавить context |
| 3 | **`PreToolUse`** | Перед вызовом любого tool'а (Write/Edit/Bash/...) | **Block dangerous ops** (rm -rf, secrets write) — exit code 2 = deny |
| 4 | **`PostToolUse`** ⭐ | После УСПЕШНОГО вызова tool'а | **Auto-update docs**, format on save, lint, audit log |
| 5 | **`Notification`** | Push notification к пользователю | Slack alert, desktop notification, sound |
| 6 | **`Stop`** | При завершении сессии (Ctrl+C, /exit, normal) | Финальный update индекса, autocommit, cleanup |
| 7 | **`SubagentStop`** | После завершения sub-agent'а (Agent tool) | Audit log sub-agent работы, aggregate results |
| 8 | **`PreCompact`** | Перед compaction контекста (длинная сессия) | Сохранить ключевые findings до компакта |

---

## 🎯 Какой hook выбрать для какой задачи

| Задача | Hook | Почему |
|---|---|---|
| Обновить project-index.json после создания файла | `PostToolUse` matcher Write\|Edit\|Bash | Срабатывает гарантированно после успешной операции |
| Заблокировать commit с секретами | `PreToolUse` matcher Bash | Можно вернуть exit 2 → CC не выполнит команду |
| Загрузить ADR в контекст при старте | `SessionStart` | Один раз в начале, не нагружает каждый prompt |
| Audit log всех Bash команд | `PreToolUse` matcher Bash | Хочешь логировать ДО выполнения |
| Slack-уведомление о завершении долгой задачи | `Stop` или `Notification` | Конец сессии или push notification |
| Авто-format кода после Write | `PostToolUse` matcher Write | Запускаешь prettier/black после успешной записи |
| Сохранить ключевые findings до сжатия контекста | `PreCompact` | Compaction убирает старое — успей записать |

---

## 🧩 Структура hook'а в settings.json

```jsonc
{
  "hooks": {
    "<EVENT_NAME>": [           // например "PostToolUse"
      {
        "matcher": "<regex>",   // optional, только для PreToolUse/PostToolUse
        "hooks": [
          {
            "type": "command",  // обычно "command"
            "command": "..."    // shell command или path to script
          }
        ]
      }
    ]
  }
}
```

### Поля `matcher` (только PreToolUse / PostToolUse)

Регулярка по **имени tool'а**:

| matcher | Срабатывает на |
|---|---|
| `Write` | только Write |
| `Write\|Edit` | Write ИЛИ Edit |
| `Write\|Edit\|Bash` | три tool'а |
| `mcp__.*` | все MCP-tools |
| `.*` или omit | любой tool |

**`matcher` НЕ умеет** фильтровать по file path — это делается **внутри команды** (твой скрипт читает stdin и сам решает).

---

## 📤 Что hook получает на stdin

Каждый hook получает **JSON-payload** через stdin. Структура зависит от event:

### `PostToolUse` payload пример

```json
{
  "session_id": "abc-123",
  "transcript_path": "/Users/.../session.jsonl",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "backend/services/orderService.js",
    "content": "export class OrderService { ... }"
  },
  "tool_response": {
    "type": "create",
    "filePath": "backend/services/orderService.js"
  }
}
```

### `PreToolUse` payload пример

```json
{
  "session_id": "abc-123",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules"
  }
}
```

### `SessionStart` payload пример

```json
{
  "session_id": "abc-123",
  "transcript_path": "/Users/.../session.jsonl",
  "hook_event_name": "SessionStart",
  "matcher": "startup"
}
```

---

## 🚦 Exit codes — что делает CC

| Exit code | Поведение CC |
|---|---|
| `0` | Success. Continue normally. stdout идёт в логи, не в Claude. |
| `2` | **Deny** (только для PreToolUse) → CC отменяет вызов tool'а. stderr попадает в Claude как причина. |
| Прочее | Warning в лог, но CC продолжает работу. |

### Специальный поток `stderr` → Claude

Для **PostToolUse** stderr из hook'а попадает в **system messages** Claude, который может это прочитать в следующем шаге. Это позволяет hook'у «общаться» с моделью.

Пример: hook update_project_index.py пишет `[update-index hook] ✅ updated project-index.json` → Claude видит это сообщение, понимает что index обновлён.

---

## 📚 Каталог готовых примеров

См. [`examples-gallery.md`](examples-gallery.md) — 7 практических hook'ов копируй-вставляй:

1. **Auto-update project-index.json** (наш основной кейс)
2. **Block writes to `.env` / secrets**
3. **Auto-format on Write** (prettier / black / gofmt)
4. **Audit log всех Bash команд**
5. **Slack-уведомление о завершении сессии**
6. **Load ADRs in context on SessionStart**
7. **Auto-commit после успешного refactor**

---

## ⚠️ Важные ограничения

- **Hooks не работают** в **headless mode** Claude Code (`claude -p ...`) для некоторых event'ов — проверь свою версию через `claude --version`.
- **Timeout по умолчанию: 60 секунд** на hook. Долгие операции вынеси в background (`&` в shell).
- **Hooks выполняются с правами твоего юзера** — будь осторожен с `rm`, `git push`, и другими destructive операциями.
- **`PreToolUse` exit 2** заменяет вызов tool'а — Claude не сможет его повторить. Используй осторожно.
- **Performance:** каждый PostToolUse hook добавляет 100-500ms на tool call (зависит от языка скрипта). Питон / node — медленнее. Bash — быстрее.

---

## 🛠 Best practices

1. **Идемпотентность** — hook должен быть безопасен при многократном вызове. Проверяй state ДО изменений.
2. **Fast-path** — если hook не нужен в этом случае (например, path не в watch-list) — выходи быстро с exit 0.
3. **Логируй на stderr** — stdout попадает в логи CC, stderr попадает к Claude. Используй stderr для важных сообщений.
4. **Не блокируй** — если hook займёт > 5 сек, перенеси в background.
5. **Версионируй** — клади скрипты в `.claude/scripts/` (в git), не в `~/.claude/`.
6. **Тестируй standalone** — твой скрипт должен работать и без stdin (для CI / manual run).
7. **Не делай side effects при ошибке** — если skрипт падает, hook должен выйти с exit 0 (warning) или exit 1 (errors logged), а не уронить CC.

---

## 🔗 Дополнительные ссылки

- **Официальная дока Claude Code hooks:** https://code.claude.com/docs/en/hooks
- Settings reference: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/settings
- Claude Code CLI reference: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/cli-usage
- Community hooks gallery (unofficial): https://github.com/anthropics/claude-code/discussions (поиск «hook»)
- Hooks vs sub-agents — когда что: https://docs.anthropic.com/en/docs/build-with-claude/sub-agents

---

## 💡 Идеи на будущее (не в этом модуле, но полезно знать)

| Hook | Идея |
|---|---|
| `UserPromptSubmit` | Redact PII (email, phone) из промпта перед отправкой Claude |
| `PreToolUse` | Анализатор Bash команд — block `curl https://...` без allowlist |
| `PostToolUse` matcher MCP | Логировать все MCP-tool вызовы для audit'а |
| `Stop` | Auto-PR создать после успешной сессии |
| `SubagentStop` | Aggregate sub-agent findings в общий report |
| `PreCompact` | Сохранить ADR drafts + open questions перед сжатием |

---

## Связанные файлы в студ-репо M6

- [`../example-hooks/`](../example-hooks/) — готовый рабочий пример (project-index auto-update)
- [`../keeping-docs-current.md`](../keeping-docs-current.md) — 3 уровня enforcement docs sync (включая hooks)
- [`../multi-level-docs-stack.md`](../multi-level-docs-stack.md) — где hooks в общей картине documentation
