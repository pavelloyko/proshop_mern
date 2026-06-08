# Keeping docs current — 3 уровня enforcement (prompt → hooks → CI)

> **Главная боль:** `project-index.json` и `AGENTS.md / CLAUDE.md` отстают от реальности за 2-3 спринта. Кто-то создал новую папку, никто не обновил index → AI-агент даёт нерелевантные ответы → команда перестаёт ему доверять.
>
> **Решение:** 3 уровня enforcement в порядке возрастания надёжности. Начинай с уровня 1, если есть время — добавляй 2 и 3.

---

## Почему «руками обновлять» не работает

Когда обновление документации = ритуал «не забыть»:
- Разработчик сделал 3 git commit'а → забыл обновить index
- Pair-programming сессия 2 часа → быстрый рефактор → забыли  
- Hotfix в 3 ночи → забыли  
- Junior пришёл — не знает что нужно обновлять  
- AI-агент создал файл — не обновил index

Результат: через 2-3 спринта `project-index.json` отличается от реальной структуры. AI-агенты читают **старую** структуру → дают советы на основе устаревшего понимания → люди начинают игнорировать AI-агентов → круг замкнут.

**Living documentation = автоматическое обновление по событию, а не «руками когда вспомнил».**

---

## Уровень 1 — Prompt-level rule (минимум, начни с этого)

> Самый простой, самый дешёвый. Работает на 60-70% случаев. Не работает когда: разработчик не использует AI-агента для изменения, agent забыл правило в длинной сессии, не работает в IDE без CLAUDE.md.

### Что добавить в `CLAUDE.md` / `AGENTS.md`

```markdown
## Поддержание project-index.json

**ВСЕГДА** обновляй `project-index.json` при ЛЮБОМ из следующих действий:

- Создание нового файла или папки
- Удаление файла или папки
- Перемещение / переименование файла или папки
- Изменение `description` подпроекта (изменилась его роль)
- Добавление / удаление dependency, которая меняет tech_stack

**Как обновлять:**
1. Открой `project-index.json`
2. Найди соответствующую секцию (subprojects / system_folders / root_files / filesystem_tree)
3. Внеси правку
4. Обнови поле `last_updated` на текущий ISO timestamp
5. Сделай отдельный commit: `docs(index): update for <change>`

**Никогда не делай:**
- Edit project-index.json без обновления `last_updated`
- Удалить субпроект без перемещения в `system_folders.archive`
- Добавить новый `hard_rule` без согласования с командой

ПЕРЕД любой работой в репо **ПРОЧИТАЙ** `project-index.json` — это твоя карта структуры.
```

### Cursor users — `.cursorrules` (или `.cursor/rules/*.mdc`)

```markdown
# Cursor rules — keeping docs current

When you create / delete / move / rename any file or folder:

1. Update `project-index.json`:
   - Add/remove entry in subprojects / system_folders / root_files
   - Update filesystem_tree
   - Bump `last_updated` to current ISO timestamp

2. If you added a new feature with new architectural decision:
   - Create `docs/adr/ADR-NN-<topic>.md` in Nygard format

3. Commit as separate commit: `docs(index): ...`

BEFORE any task, READ `project-index.json` first — it's your map.
```

### GitHub Copilot users — `.github/copilot-instructions.md`

```markdown
# Copilot custom instructions

## Project structure awareness

This repo has `project-index.json` in the root. Read it before any task to understand the layout.

## Maintaining the index

When you suggest creating/deleting/renaming files:
- Also suggest updating `project-index.json`
- Suggest updating `last_updated` field
- Suggest separate commit message: `docs(index): update for <change>`
```

### Плюсы / минусы Уровня 1

✅ **Плюсы:**
- Setup за 5 минут
- Работает в любом инструменте (CC / Cursor / Copilot / Aider)
- Без зависимостей от env, hooks, CI
- Прозрачно для команды (правило явное в `CLAUDE.md`)

❌ **Минусы:**
- AI забывает в длинной сессии (context rot после 100K токенов)
- Не работает когда разработчик НЕ использует AI (правка вручную)
- 30-40% случаев пропускается → index дрейфит за месяц-два

---

## Уровень 2 — Claude Code hooks (автоматизация на стороне CC)

> Сильнее prompt-level rule. CC выполняет hook **гарантированно** после tool call, не зависит от того что AI «помнит». Работает только в Claude Code (не в Cursor / Copilot).

### Что такое Claude Code hooks

Hooks — это shell-команды, которые CC автоматически вызывает на определённых событиях. Описание событий:

| Event | Когда срабатывает | Использование для docs |
|---|---|---|
| `SessionStart` | При старте CC-сессии | Прочитать project-index.json в контекст |
| `PreToolUse` | До вызова tool'а | Валидация |
| **`PostToolUse`** | После успешного вызова tool'а | **← основной для docs sync** |
| `Stop` | По завершении сессии | Финальный update + commit |
| `UserPromptSubmit` | На каждое сообщение пользователя | Reminder в context |
| `Notification` | Push notification | Уведомление в Slack/etc |

### Setup — `update_project_index.py` script

Положи в `.claude/scripts/update_project_index.py`:

```python
#!/usr/bin/env python3
"""
Auto-update project-index.json filesystem_tree + last_updated.

Triggered by Claude Code PostToolUse hook on Write/Edit/Bash with file ops.
Reads stdin JSON (hook payload), determines if a structural change happened,
updates index if yes.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # .claude/scripts/ → up to repo root
INDEX_FILE = REPO_ROOT / "project-index.json"

# Folders to skip in filesystem_tree
EXCLUDE_DIRS = {".git", "node_modules", "build", "dist", ".next", ".venv", "uploads/contents"}


def is_structural_change(payload: dict) -> bool:
    """Return True if the tool call likely changed repo structure."""
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name == "Write":
        # Write to NEW file path = structural change
        # Edit to existing file = not structural (assume)
        # We can't know without checking — be conservative: always update on Write
        return True

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # File/folder operations
        structural_keywords = ["mkdir", "rmdir", "mv ", "rm ", "touch ", "cp -r"]
        return any(kw in command for kw in structural_keywords)

    return False


def walk_tree(root: Path, max_depth: int = 4) -> dict:
    """Build a dict-of-arrays filesystem_tree."""
    tree = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # Apply excludes
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        key = "." if rel == Path(".") else str(rel)
        tree[key] = sorted(dirnames + filenames)
    return tree


def update_index() -> None:
    if not INDEX_FILE.exists():
        print(f"[update-index] {INDEX_FILE} not found — skip", file=sys.stderr)
        return

    with INDEX_FILE.open("r") as f:
        index = json.load(f)

    index["filesystem_tree"] = walk_tree(REPO_ROOT)
    index["last_updated"] = datetime.now(timezone.utc).isoformat()

    with INDEX_FILE.open("w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"[update-index] ✅ updated {INDEX_FILE.name}", file=sys.stderr)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # No stdin / not a hook call → run unconditionally
        update_index()
        return

    if is_structural_change(payload):
        update_index()
    # else: skip


if __name__ == "__main__":
    main()
```

Сделай executable:

```bash
chmod +x .claude/scripts/update_project_index.py
```

### Hook config — `.claude/settings.json` (или `settings.local.json`)

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
            "command": "test -f \"$CLAUDE_PROJECT_DIR/project-index.json\" && echo '✅ project-index.json present — read it first for repo structure'"
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

### Как это работает на практике

1. Ты в CC сессии: `claude` → start
2. Hook `SessionStart` напечатал «✅ project-index.json present» — Claude видит этот hint, знает что надо прочитать
3. Ты говоришь: «Создай новый сервис `backend/services/orderService.js` с базовой логикой order workflow»
4. Claude использует Write tool → создаёт файл
5. **Hook `PostToolUse` срабатывает** → запускается `update_project_index.py` → файл обновляется автоматически
6. На stderr ты видишь: `[update-index] ✅ updated project-index.json`
7. Ты делаешь `git status` — видишь и `orderService.js`, и обновлённый `project-index.json`

**Магия:** ты не написал ни слова про index. CC «сам» обновил его благодаря hook'у.

### Плюсы / минусы Уровня 2

✅ **Плюсы:**
- Срабатывает **гарантированно** после tool call (не зависит от AI memory)
- Прозрачно для пользователя (просто работает)
- Versioned config — вся команда получает hook через git
- Можно расширять (auto-update других doc-файлов, не только index)

❌ **Минусы:**
- Работает **только в Claude Code** — не в Cursor / Copilot / Aider
- Если разработчик правит файлы **руками** (не через CC), hook не сработает
- Hook замедляет каждый PostToolUse на 100-500ms (Python startup)

---

## Уровень 3 — Git pre-commit hook + CI (максимальная защита)

> Работает **независимо** от того что использует разработчик: CC, Cursor, vim, IDE — всё равно перед commit'ом index должен быть в синке. Самый строгий уровень.

### Setup — `.husky/pre-commit`

```bash
#!/bin/sh
. "$(dirname -- "$0")/_/husky.sh"

# Check if any file/folder operation happened in this commit
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACDR | grep -v "^project-index.json$")
ADDED_OR_REMOVED=$(git diff --cached --name-status --diff-filter=ACR | wc -l)

# If files added/removed/renamed but project-index.json NOT in commit → fail
if [ "$ADDED_OR_REMOVED" -gt 0 ]; then
  INDEX_IN_COMMIT=$(git diff --cached --name-only | grep -c "^project-index.json$" || true)
  if [ "$INDEX_IN_COMMIT" -eq 0 ]; then
    echo "❌ Files were added/removed/renamed but project-index.json NOT updated."
    echo ""
    echo "Run this to auto-update:"
    echo "  python3 .claude/scripts/update_project_index.py"
    echo "  git add project-index.json"
    echo ""
    echo "Bypass (rare cases): git commit --no-verify"
    exit 1
  fi
fi

exit 0
```

### CI validation — `.github/workflows/docs-sync-check.yml`

```yaml
name: Docs sync check

on:
  pull_request:
    branches: [main, master]

jobs:
  index-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Update index in CI clone
        run: |
          python3 .claude/scripts/update_project_index.py

      - name: Verify index unchanged
        run: |
          if ! git diff --exit-code project-index.json; then
            echo "❌ project-index.json is out of sync with actual repo structure"
            echo "   Run locally: python3 .claude/scripts/update_project_index.py"
            echo "   Then: git add project-index.json && git commit --amend"
            exit 1
          fi
          echo "✅ project-index.json is in sync"
```

### Плюсы / минусы Уровня 3

✅ **Плюсы:**
- **Гарантия в production** — нельзя смерджить PR с устаревшим index
- Работает независимо от инструмента разработки (CC / Cursor / vim — без разницы)
- Catches mistakes Layer 1+2 не поймали

❌ **Минусы:**
- Setup-time ~1 час
- Husky зависимость для всей команды
- CI запуск +30 сек на каждый PR
- Может раздражать новых разработчиков («почему мой PR не merge'ится?»)

---

## Recommended stack — combine all 3 levels

| Layer | Где enforce | Что catches |
|---|---|---|
| 1 (prompt) | `CLAUDE.md` / `.cursorrules` / `.github/copilot-instructions.md` | AI-агент сам обновит в большинстве случаев |
| 2 (CC hooks) | `.claude/settings.json` | Гарантия что CC обновит даже если AI забыл |
| 3 (git + CI) | `.husky/pre-commit` + `.github/workflows/` | Финальный barrier — нельзя смерджить устаревший index |

**Время setup'а:** ~2 часа на всё (один раз).
**Время поддержки:** 0 (всё автоматически).

---

## Пример — что произойдёт у студента M6 если он применит все 3 уровня

**Сценарий:** Студент создаёт новый файл `backend/services/auditLogService.js` для своего Stage 1 агента-аудитора.

```
1. Студент в CC: "Создай новый сервис auditLogService.js в backend/services/"
   │
   ├─ CC использует Write tool → создаёт файл
   │
   ├─ [Уровень 2] Hook PostToolUse срабатывает
   │  └─ update_project_index.py обновляет filesystem_tree + last_updated
   │
   └─ Студент видит на stderr: [update-index] ✅ updated project-index.json

2. Студент: git add . && git commit -m "feat(services): add auditLogService"
   │
   ├─ [Уровень 3] .husky/pre-commit срабатывает
   │  ├─ Видит что auditLogService.js добавлен
   │  ├─ Видит что project-index.json тоже в commit (✅ от уровня 2)
   │  └─ Пропускает commit
   │
   └─ Commit успешен

3. Студент: git push → создаёт PR
   │
   ├─ [Уровень 3] CI workflow docs-sync-check.yml запускается
   │  ├─ Re-runs update_project_index.py в CI runner
   │  ├─ git diff project-index.json → empty (всё уже синке)
   │  └─ ✅ PASS
   │
   └─ PR ready to merge
```

**Если бы студент **руками** в vim создал файл, минуя CC** — Уровень 2 не сработает, но Уровень 3 (pre-commit) поймает на commit'е. Студент запустит `update_project_index.py` руками, добавит изменения, передкоммитит. Index всё равно синке.

---

## Что класть в `update_project_index.py` — пять стандартных секций

Для надёжности скрипт должен обновлять минимум 5 секций:

| Секция в JSON | Что обновляется | Триггер |
|---|---|---|
| `filesystem_tree` | Полное дерево folder → list-of-children (depth 4) | Любое `mkdir`/`rmdir`/`mv`/`rm` |
| `last_updated` | ISO timestamp UTC | Каждый запуск (если что-то изменилось) |
| `subprojects` (метаданные) | Annotated metadata подпроектов (path / tech / owner) | Manual обновление при смысловой смене |
| `system_folders` | Annotated metadata system-folders | Manual обновление при добавлении новой |
| `root_files` | Annotated root-level файлы | Manual при добавлении root .md/.json |

**Автоматизируется:** `filesystem_tree` + `last_updated`.
**Manually обновляется:** annotated секции (когда меняется СМЫСЛ подпроекта, не только наличие).

В скрипте можно сделать 2 режима:
- `--full` — переписать `filesystem_tree` + `last_updated`
- `--check-only` — только проверить, есть ли drift (для CI)

---

## Anti-pattern — чего НЕ делать

| Anti-pattern | Почему плохо |
|---|---|
| Хранить `filesystem_tree` в RAM и пересчитывать на каждое чтение | Медленно. AI читает 10× за сессию. |
| Auto-commit `project-index.json` из hook без `--amend` | Создаёт мусорные commits в истории |
| Включать `node_modules/`, `.git/`, `build/` в tree | JSON разрастается до 50K+ строк, AI задыхается |
| Хранить `subprojects` annotations в auto-обновляемой секции | При auto-rebuild теряются ручные annotations |
| Не иметь `last_updated` поля | Невозможно понять когда index был синке последний раз |
| Заставлять разработчиков обновлять руками без хуков | Pure willpower — не работает |
| `pre-commit` блокирует ВСЕ commits даже без structural changes | Раздражает на typo-fix commits |

---

## Quick start — что сделать СЕГОДНЯ (15 минут)

1. **Добавь в `CLAUDE.md` / `AGENTS.md`** секцию «Поддержание project-index.json» (см. Уровень 1)
2. **Создай `.claude/scripts/update_project_index.py`** (~50 строк, шаблон выше)
3. **Добавь hook в `.claude/settings.json`** — PostToolUse на Write|Edit|Bash (см. Уровень 2)
4. **Запусти один раз вручную:** `python3 .claude/scripts/update_project_index.py`
5. **Commit** обновлённый `project-index.json`

Уровень 3 (Husky + CI) можно добавить через неделю когда увидишь как Уровень 2 работает.

---

## Связанные файлы

- [`multi-level-docs-stack.md`](multi-level-docs-stack.md) — 8 уровней документации (Layer 8 = project-index.json)
- [`agents-md-claude-md-standard.md`](agents-md-claude-md-standard.md) — формат CLAUDE.md / AGENTS.md
- [`recipe-inline-comments.md`](recipe-inline-comments.md) — Layer 1, локальные правила в коде
- [`numbers-card.md`](numbers-card.md) — статистика по AGENTS.md adoption, RAG freshness

---

## Дополнительные ссылки

- Claude Code hooks docs: https://code.claude.com/docs/en/hooks
- Husky (git hooks для команды): https://github.com/typicode/husky
- Cursor rules format: https://docs.cursor.com/context/rules
- GitHub Copilot custom instructions: https://docs.github.com/en/copilot/customizing-copilot
- AGENTS.md spec: https://agentsmd.com
