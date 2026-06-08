# Claude Code hooks — gallery готовых примеров

> 7 рабочих hook-конфигов копируй-вставляй. Адаптируй под свой проект.

> Все примеры — фрагменты для `.claude/settings.json` (только секция `hooks`, остальное — твоё).

---

## 1️⃣ Auto-update project-index.json (наш основной кейс)

**Что делает:** после каждого Write/Edit/Bash в `frontend/`, `backend/`, `mcp/`, `rag/` — обновляет `project-index.json` (filesystem_tree + last_updated).

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/scripts/update_project_index.py\""
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '✅ Read project-index.json first for repo structure.'"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/scripts/update_project_index.py\""
          }
        ]
      }
    ]
  }
}
```

Скрипт: [`../example-hooks/update_project_index.py`](../example-hooks/update_project_index.py)

---

## 2️⃣ Block writes to `.env` / secrets

**Что делает:** Если AI пытается записать в `.env`, `secrets/`, `*.pem`, `*.key` — блокирует операцию.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/scripts/block-secret-writes.py\""
          }
        ]
      }
    ]
  }
}
```

**`.claude/scripts/block-secret-writes.py`:**

```python
#!/usr/bin/env python3
import json, sys, re

payload = json.load(sys.stdin)
file_path = payload.get("tool_input", {}).get("file_path", "")

BANNED_PATTERNS = [
    r"^\.env$", r"^\.env\..*", r"secrets/", r"\.pem$", r"\.key$",
    r"id_rsa", r"\.aws/credentials", r"gcloud-key\.json"
]

for pattern in BANNED_PATTERNS:
    if re.search(pattern, file_path):
        print(f"❌ BLOCKED: Writing to '{file_path}' is forbidden (matches '{pattern}')", file=sys.stderr)
        print("   Reason: secret/credentials file. Use environment variables or vault instead.", file=sys.stderr)
        sys.exit(2)   # exit 2 = deny

sys.exit(0)
```

---

## 3️⃣ Auto-format on Write (prettier / black / gofmt)

**Что делает:** После Write/Edit JS/TS/Python файла — запускает форматер. Auto-saves.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/scripts/auto-format.sh\""
          }
        ]
      }
    ]
  }
}
```

**`.claude/scripts/auto-format.sh`:**

```bash
#!/bin/bash
# Read payload from stdin
PAYLOAD=$(cat)
FILE_PATH=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

case "$FILE_PATH" in
  *.js|*.jsx|*.ts|*.tsx)
    npx prettier --write "$FILE_PATH" 2>&1 && echo "[auto-format] ✅ prettier $FILE_PATH" >&2
    ;;
  *.py)
    black --quiet "$FILE_PATH" 2>&1 && echo "[auto-format] ✅ black $FILE_PATH" >&2
    ;;
  *.go)
    gofmt -w "$FILE_PATH" && echo "[auto-format] ✅ gofmt $FILE_PATH" >&2
    ;;
esac

exit 0
```

---

## 4️⃣ Audit log всех Bash команд

**Что делает:** Логирует **каждую** Bash команду которую запускает AI — для security audit.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'CMD=$(jq -r .tool_input.command); echo \"[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $CMD\" >> \"$CLAUDE_PROJECT_DIR/.claude/audit-bash.log\"'"
          }
        ]
      }
    ]
  }
}
```

Лог попадает в `.claude/audit-bash.log`:

```
[2026-05-18T16:30:12Z] git status
[2026-05-18T16:30:18Z] npm test
[2026-05-18T16:30:42Z] rm -rf node_modules/.cache
```

Удобно для post-mortem: «что именно AI делал во время инцидента».

---

## 5️⃣ Slack-уведомление о завершении сессии

**Что делает:** На `Stop` — посылает webhook в Slack с summary.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'curl -s -X POST -H \"Content-Type: application/json\" -d \"{\\\"text\\\":\\\"🤖 Claude session done in $(basename $CLAUDE_PROJECT_DIR)\\\"}\" $SLACK_WEBHOOK_URL'"
          }
        ]
      }
    ]
  }
}
```

Требует env var `SLACK_WEBHOOK_URL` (из `~/.env` или Slack incoming webhook).

---

## 6️⃣ Load ADRs in context on SessionStart

**Что делает:** При старте сессии — печатает список доступных ADR в stderr (Claude увидит).

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'echo \"📚 Available ADRs:\"; ls \"$CLAUDE_PROJECT_DIR/docs/adr/\" 2>/dev/null | sed \"s/^/  - /\"'"
          }
        ]
      }
    ]
  }
}
```

Output (stderr, виден Claude):

```
📚 Available ADRs:
  - ADR-001-database-choice.md
  - ADR-002-mcp-server-architecture.md
  - ADR-003-rag-chunking-strategy.md
```

---

## 7️⃣ Auto-commit после успешного refactor

**Что делает:** На `Stop` — если есть unstaged changes, делает auto-commit с timestamp.

⚠️ **Осторожно!** Auto-commits засоряют git history. Используй ТОЛЬКО на feature branches, никогда на main.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/scripts/auto-commit-on-stop.sh\""
          }
        ]
      }
    ]
  }
}
```

**`.claude/scripts/auto-commit-on-stop.sh`:**

```bash
#!/bin/bash
cd "$CLAUDE_PROJECT_DIR" || exit 0

# ⚠️ ONLY on feature branches
BRANCH=$(git branch --show-current)
case "$BRANCH" in
  main|master|production|release/*)
    echo "[auto-commit] skipped on $BRANCH" >&2
    exit 0
    ;;
esac

# Skip if nothing to commit
if [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

git add -A
git commit -m "auto: claude session changes ($(date -u +%Y-%m-%dT%H:%MZ))" --no-verify \
  && echo "[auto-commit] ✅ committed on $BRANCH" >&2

exit 0
```

---

## Как использовать эту галерею

1. **Выбери hook** из gallery по своему use-case'у
2. **Скопируй JSON-секцию** в свой `.claude/settings.json` (merge'ани с существующими hooks)
3. **Скопируй скрипты** в `.claude/scripts/`, сделай executable (`chmod +x`)
4. **Протестируй**: `claude` → выполни сценарий который должен триггерить hook → смотри stderr и логи

### Объединение нескольких hooks на один event

Можно навесить **несколько** hooks на один event:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 ... update_project_index.py" },
          { "type": "command", "command": "bash ... auto-format.sh" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ... track-bash.py" }
        ]
      }
    ]
  }
}
```

Они выполняются **по порядку**. Если первый exit non-zero — CC может прервать (зависит от типа event).

---

## ⚠️ Чего НЕ делать

- **Не запускай `git push` из hook'а** — push'нёт черновики и сломает CI
- **Не делай destructive операции в `PreToolUse`** — exit 2 предотвращает вызов, но твой скрипт мог уже что-то сломать
- **Не вешай длинные операции (> 5 сек) синхронно** — заблокируешь сессию. Перенеси в background: `nohup ... &`
- **Не пиши секреты в hook command** — settings.json в git, секреты увидят все
- **Не делай hooks которые блокируют каждый Write** — UX будет ужасным, придётся снимать через `--no-verify`

---

## Связанные файлы

- [`README.md`](README.md) — overview всех 8 типов hooks
- [`../example-hooks/`](../example-hooks/) — наш production-ready пример project-index hook
- [`../keeping-docs-current.md`](../keeping-docs-current.md) — 3 уровня enforcement через hooks + git + CI
- Официальная дока: https://code.claude.com/docs/en/hooks
