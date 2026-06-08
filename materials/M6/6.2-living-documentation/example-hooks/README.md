# Example: Claude Code hook для project-index.json

> **Что в этой папке:** готовый набор файлов, чтобы у тебя в fork`е заработал auto-update `project-index.json` при каждом изменении структуры в `frontend/` / `backend/` / `mcp/` / `rag/`.

---

## Как hook'и работают в Claude Code (важно понять!)

**❌ Распространённое заблуждение:** «hook = отдельный файл в папке `.claude/hooks/`»

**✅ Правильно:** hook = **JSON-конфиг в `.claude/settings.json`**. Никакой отдельной папки нет. Эта секция в settings.json **указывает CC**: «когда произойдёт event X, запусти команду Y».

### Структура хука в settings.json

```jsonc
{
  "hooks": {
    "<EVENT_NAME>": [           // когда срабатывать
      {
        "matcher": "<regex>",   // на каких tools (необязательно)
        "hooks": [
          {
            "type": "command",  // обычно "command"
            "command": "..."    // что выполнить (shell / python)
          }
        ]
      }
    ]
  }
}
```

### События которые CC поддерживает

| Event | Когда срабатывает | Получает на stdin |
|---|---|---|
| `SessionStart` | При старте `claude` сессии | `{session_id, transcript_path, hook_event_name}` |
| `UserPromptSubmit` | На каждое сообщение пользователя | `{prompt, ...}` |
| `PreToolUse` | До вызова любого tool'а | `{tool_name, tool_input}` |
| **`PostToolUse`** ⭐ | После успешного вызова tool'а | `{tool_name, tool_input, tool_response}` |
| `Notification` | Push notification | `{notification_text}` |
| `Stop` | При завершении сессии (Ctrl+C, /exit, normal end) | `{session_id, ...}` |
| `SubagentStop` | После завершения sub-agent'а | `{session_id, ...}` |

### Что такое `matcher`

`matcher` — это **regex по имени tool'а** (только для `PreToolUse` / `PostToolUse`).

| matcher | Срабатывает на |
|---|---|
| `Write` | только Write tool |
| `Write\|Edit` | Write ИЛИ Edit |
| `Write\|Edit\|Bash` | три tool'а |
| `.*` | любой tool |
| (omit) | тоже любой tool |

**`matcher` НЕ умеет** фильтровать по file path — это делается **внутри команды** (твой Python-скрипт читает stdin и сам решает).

---

## Что есть в этой папке

| Файл | Назначение |
|---|---|
| `settings.example.json` | Готовый шаблон `.claude/settings.json` с 3 hook'ами (PostToolUse + SessionStart + Stop). Копируй в свой fork (без `_comment_*` ключей). |
| `update_project_index.py` | Python-скрипт который CC вызывает по hook'у. Читает stdin (payload), фильтрует по watch-paths (`frontend/`, `backend/`, `mcp/`, `rag/`), обновляет `project-index.json`. |

---

## Setup в свой fork (4 шага, ~5 минут)

### 1. Создай папки и скопируй скрипт

```bash
cd ~/your-proshop-fork
mkdir -p .claude/scripts
cp aidev-course-materials/M6/6.2-living-documentation/example-hooks/update_project_index.py .claude/scripts/
chmod +x .claude/scripts/update_project_index.py
```

### 2. Создай / обнови settings

Скопируй содержимое `settings.example.json` (БЕЗ ключей `_comment_*`) в `.claude/settings.json`:

```bash
# Очисти от _comment-полей через jq:
jq 'del(.. | objects | ._comment_1, ._comment_2, ._comment_3, ._comment_4, ._comment_5, ._doc)' \
  aidev-course-materials/M6/6.2-living-documentation/example-hooks/settings.example.json \
  > .claude/settings.json
```

> ⚠️ Если у тебя уже есть `.claude/settings.json` с другими ключами — **смерджи** руками `hooks` секцию, не перезаписывай весь файл.

### 3. Создай initial `project-index.json`

```bash
# Запусти скрипт без аргументов, он создаст ничего не было — обновит существующий
python3 .claude/scripts/update_project_index.py
```

Если `project-index.json` ещё нет — попроси Claude Code:

```
Read AGENTS.md and walk the repo structure. Build a project-index.json
following the schema in aidev-course-materials/M6/6.2-living-documentation/project-index.example.json.
Save to repo root.
```

### 4. Проверь что hook работает

```bash
claude
```

В CC сессии вставь:

```
Create a test file `backend/services/_hook_test.js` with content "// hook test".
```

После того как Claude создаст файл — **на stderr** должно появиться:

```
[update-index] ✅ updated project-index.json (tree + last_updated)
```

Если появилось — hook работает! Можешь удалить тестовый файл:

```
Delete backend/services/_hook_test.js
```

---

## Watch-paths — что фильтруется

Скрипт `update_project_index.py` смотрит только на изменения внутри:

```python
WATCH_PATHS = ("frontend/", "backend/", "mcp/", "rag/", "feature flags/")
```

Это значит:
- ✅ Создал файл в `backend/services/` → index обновится
- ✅ Удалил папку в `frontend/src/` → index обновится
- ❌ Создал файл в `docs/` → index НЕ обновится (docs не критичны для AI-навигации, обновляй вручную если хочешь)
- ❌ Создал файл в `.agent-team-reports/` → НЕ обновится (это runtime artefacts)

**Хочешь расширить?** Открой `update_project_index.py`, добавь путь в `WATCH_PATHS` tuple:

```python
WATCH_PATHS = ("frontend/", "backend/", "mcp/", "rag/", "feature flags/", "docs/")
```

---

## Что произойдёт во время Claude сессии — sequence diagram

```
You: "Create backend/services/orderService.js"
                       │
                       ▼
              Claude reads project-index.json (SessionStart hint)
                       │
                       ▼
              Claude uses Write tool → creates orderService.js
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  PostToolUse hook fires                  │
        │  matcher "Write|Edit|Bash" matches Write │
        │  CC executes the command:                │
        │  python3 update_project_index.py         │
        │  (stdin: JSON payload with file_path)    │
        └──────────────────────────────────────────┘
                       │
                       ▼
              Script reads stdin, sees file_path = "backend/services/orderService.js"
                       │
                       ▼
              _path_is_watched() → True (backend/ matches)
                       │
                       ▼
              walk_tree() rebuilds filesystem_tree
              Compare old vs new → tree changed
                       │
                       ▼
              Write project-index.json with new tree + last_updated
                       │
                       ▼
              Print on stderr: [update-index] ✅ updated project-index.json
                       │
                       ▼
              Claude continues with response
```

---

## Troubleshooting

### Hook не срабатывает (нет сообщения на stderr)

1. Проверь что путь к скрипту правильный: `ls -la "$CLAUDE_PROJECT_DIR/.claude/scripts/update_project_index.py"`
2. Проверь executable: `chmod +x .claude/scripts/update_project_index.py`
3. Проверь settings.json не сломан: `cat .claude/settings.json | jq .` (должен пройти без ошибок)
4. Запусти CC с verbose: `claude --debug 2>&1 | grep -i hook` — увидишь логи срабатывания
5. Проверь что файл в watch-path: добавь временно `print(f"DEBUG: payload={payload}", file=sys.stderr)` в начало `main()`

### Hook срабатывает, но `last_updated` не меняется

- Скорее всего `filesystem_tree` не изменился (Edit на существующий файл не меняет дерево). Это **корректное** поведение — `last_updated` обновляется только на структурные изменения.
- Создай **новый файл** для проверки.

### `[update-index] ✅` появляется на каждый Edit (слишком шумно)

- В скрипте `is_structural_change()` — поменяй `if tool_name in ("Write", "Edit"):` на `if tool_name == "Write":`. Edit на существующий файл не будет триггерить.

### Hook ломает CC сессию

- Проверь exit code скрипта: должен быть `0` в нормальном случае. Если скрипт падает с non-zero — CC может остановиться.
- Логи CC: `~/.claude/logs/` (если включены).

---

## Альтернативные триггеры (если ты НЕ на Claude Code)

| Инструмент | Аналог hook'а |
|---|---|
| **Cursor** | Cursor пока не имеет аналога PostToolUse hook. Используй git hook (.husky/pre-commit) |
| **Cline / Roo Code** | Похожий механизм через `.clinerules` или `.roo/rules` |
| **GitHub Copilot** | Нет native hooks. Используй .github/copilot-instructions.md prompt-level + git pre-commit |
| **Aider** | `.aider.conf.yml` `auto-commits: true` + custom prompt rules |

**Минимум для всех:** git pre-commit hook через Husky — он работает независимо от IDE. См. [`../keeping-docs-current.md`](../keeping-docs-current.md) → Уровень 3.

---

## Связанные файлы

- [`../keeping-docs-current.md`](../keeping-docs-current.md) — 3 уровня enforcement (prompt → hooks → CI) с полными примерами
- [`../multi-level-docs-stack.md`](../multi-level-docs-stack.md) — где project-index.json в стеке (Layer 8)
- [`../project-index.example.json`](../project-index.example.json) — пример project-index.json из proshop_mern

## Дополнительные ссылки

- Claude Code hooks (official docs): https://code.claude.com/docs/en/hooks
- Claude Code settings reference: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/settings
- AGENTS.md spec: https://agentsmd.com
