# Claude Code Review — полный setup (4 механизма запуска)

> Универсальный setup-доку: как запустить AI Code Review на своём проекте. **4 механизма** — от локального ручного до cloud Agent Team. С готовыми промптами, YAML, hooks, ценой, плюсами/минусами.

---

## TL;DR — что выбрать

| Когда хочешь review | Какой механизм | Цена per run | Reliability | Setup сложность |
|---|---|---|---|---|
| Учусь / отлаживаю промпт / live demo | **Вариант 1**: локально, вручную в CC сессии | ~$0.50-2 (Opus team) | 100% | ⭐ просто |
| Защитить critical paths до коммита | **Вариант 2**: pre-commit / pre-push hook | $0.10-2 / commit | ~70% | ⭐⭐ средне |
| Production CI на каждый PR (default) | **Вариант 3**: GitHub Action + single Claude | $0.04-0.30 / PR | **99%** | ⭐ просто |
| Глубокий review для критичных PR | **Вариант 4**: GitHub Action + Agent Team | $0.50-2 / PR | ~60% | ⭐⭐⭐ сложно |

**Production-рекомендация:** Вариант 3 как default + Вариант 4 как manual trigger по label.

---

## Pre-requisites — что нужно в проекте

Перед любым из 4 вариантов:

1. **Anthropic API ключ** (получить на https://console.anthropic.com/settings/keys)
2. **Claude Code установлен** (`npm i -g @anthropic-ai/claude-code`, версия `v2.1.32+` для Agent Teams)
3. **`.claude/agents/` папка** с mate-файлами — готовая shared библиотека лежит в [`../agents/`](../agents/):
   - [`security-mate.md`](../agents/security-mate.md) — OWASP Top 10 + secrets + crypto
   - [`architecture-mate.md`](../agents/architecture-mate.md) — layer boundaries + ADR compliance
   - [`performance-mate.md`](../agents/performance-mate.md) — N+1 + memory + throughput
   - [`legacy-auditor-mate.md`](../agents/legacy-auditor-mate.md) — plan-mode orchestrator (для legacy/audit потоков)
   - [`test-writer-mate.md`](../agents/test-writer-mate.md) — генерация тестов с сильными assertions
4. **`CLAUDE.md` / `AGENTS.md`** в корне проекта (project-specific rules для всех агентов)
5. **`docs/adr/*`** (или эквивалентная папка решений) если есть — architecture-mate их прочитает перед review

Скопировать готовых агентов в свой проект:

```bash
mkdir -p .claude/agents
cp aidev-course-materials/M6/agents/*.md .claude/agents/
```

---

## Вариант 1 — Локально, вручную (CC сессия) ⭐ для live demo

**Когда:** учишься, отлаживаешь промпт, демонстрируешь команде, ревьюишь свой текущий branch.

### Setup

```bash
# 1. Включить experimental Agent Teams в settings
cat > .claude/settings.json << 'EOF'
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
EOF

# 2. Запустить CC сессию в корне проекта
cd ~/my-project
claude
```

### Главный промпт (копируй-вставляй)

```
Spawn an agent team from .claude/agents/ to review my current branch.

Team config:
- 3 teammates: security-mate, architecture-mate, performance-mate
- All on claude-opus-4-7
- Run in parallel with peer-to-peer mailbox enabled

Steps:
1. Each teammate reads `gh pr diff <PR-NUMBER>` (or `git diff origin/main..HEAD` if no PR yet)
2. Each writes findings as JSONL to `.agent-team-reports/<mate-name>-findings.jsonl`
3. Each writes summary to `.agent-team-reports/<mate-name>-summary.md`
4. Teammates may use peer-to-peer mailbox at `.claude/teams/{team-id}/inboxes/` for cross-category findings

After all 3 teammates finish:
1. Read all 3 JSONL reports + inbox traffic
2. Synthesize into single report at `.agent-team-reports/synthesis.md`:
   - Group by SEVERITY (HIGH/MEDIUM/LOW)
   - Within severity, group related findings by file:line
   - Highlight cross-mate collaborations (e.g. security-mate + architecture-mate found same issue)
3. Output top 5 HIGH severity items to console for my review
4. Do NOT post to GitHub or modify any source files
```

### Что произойдёт (timeline)

| t (мин) | Что видишь |
|---|---|
| 0:00 | CC создаёт `~/.claude/teams/code-review-1/config.json` |
| 0:10 | Спанятся 3 mate'а (новые CC процессы) |
| 0:20 | security-mate начинает читать diff |
| 0:30 | architecture-mate читает `docs/adr/*` |
| 0:40 | performance-mate ищет N+1 паттерны |
| 1:00 | Первые findings появляются в `.agent-team-reports/*.jsonl` |
| 2:00 | Mailbox messages between mate'ов (если есть пересечения категорий) |
| 3:00 | Все mate'ы завершают |
| 3:30 | Lead синтезирует `synthesis.md` |
| 4:00 | Top 5 HIGH в консоли — done |

**Cost:** ~$0.50-2 per run (Opus 4.7 × 3 mate'ов).

✅ **Плюсы:** полный контроль, видишь каждый шаг, можешь interrupt и поправить промпт, нет CI зависимости
❌ **Минусы:** не масштабируется на команду, не работает без тебя, реальный live demo рискует (~50% reliability у Agent Teams)

### Если упало (fallback)

В CC сессии вместо Agent Team — обычный single sub-agent через `Agent` tool:

```
Use the Agent tool to spawn a security-focused sub-agent that reviews my
current branch diff. Output JSON findings only. Use Read/Grep tools only.
```

Single sub-agent через `Agent` tool — **100% reliability**, дешевле, но без peer-to-peer collaboration.

---

## Вариант 2 — Локально, автоматически (git hooks)

**Когда:** хочешь блокировать commit/push, если в код попала уязвимость или N+1 query.

### Что такое git hook (для нулевого уровня)

Git позволяет навесить скрипт на события: `pre-commit`, `pre-push`, `commit-msg` и т.д. Если скрипт возвращает exit code != 0 — git операция отменяется. Hooks живут в `.git/hooks/` (локально, **не синхронизируется через git**) или в `husky/` (синхронизируется через npm).

### Setup через Husky (рекомендуется для команды)

```bash
npm install --save-dev husky
npx husky init
```

Создаёт `.husky/pre-commit` skeleton и `prepare` script в `package.json`. На `npm install` у других в команде Husky автоматически активирует hooks.

### Pre-commit hook — быстрый security check на critical paths

**`.husky/pre-commit`:**

```bash
#!/bin/sh
. "$(dirname -- "$0")/_/husky.sh"

# Только проверяем изменения в auth/, payments/, crypto/, secrets/
CRITICAL_FILES=$(git diff --cached --name-only | grep -E '(backend/auth|backend/payments|backend/crypto|controllers/userController|secrets/)' || true)
if [ -z "$CRITICAL_FILES" ]; then
  exit 0
fi

echo "🔒 Critical-path security check on:"
echo "$CRITICAL_FILES"

# Single agent (быстро + дёшево) — не Agent Team, для pre-commit это overkill
unset CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS

DIFF=$(git diff --cached -- $CRITICAL_FILES)

claude -p \
  --model claude-sonnet-4-6 \
  --max-turns 5 \
  --max-tokens 2048 \
  --output-format text \
  "Review this diff for SECURITY issues only (OWASP Top 10, hardcoded secrets, auth bypass). \
   Output JSON findings. Print 'BLOCKING: <reason>' on stdout AND exit with code 1 if any HIGH severity issue found. \
   Otherwise exit 0. Diff: $DIFF"

EXIT=$?

if [ $EXIT -ne 0 ]; then
  echo ""
  echo "❌ HIGH severity security issues found."
  echo "   Fix or bypass with: git commit --no-verify"
  exit 1
fi

echo "✅ Security check passed"
```

Сделать executable:

```bash
chmod +x .husky/pre-commit
git add .husky/
git commit -m "ci: add Husky pre-commit security check"
```

### Pre-push hook — полный Agent Team review

**`.husky/pre-push`** для feature branch'ей:

```bash
#!/bin/sh
. "$(dirname -- "$0")/_/husky.sh"

BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  exit 0
fi

DIFF=$(git diff origin/main..HEAD)
if [ -z "$DIFF" ]; then exit 0; fi

export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
mkdir -p .agent-team-reports

REPORT=".agent-team-reports/pre-push-$(date +%Y%m%d-%H%M%S).md"

claude -p \
  --model claude-opus-4-7 \
  --max-turns 15 \
  --max-tokens 8000 \
  --output-format text \
  "Spawn agent team from .claude/agents/ (security, architecture, performance). \
   Review this diff. Write synthesis to $REPORT. \
   Print 'BLOCKING: <count> HIGH severity findings' AND exit 1 if any HIGH. \
   Otherwise print 'PASSED' and exit 0." \
  <<< "$DIFF"

EXIT=$?

if [ $EXIT -ne 0 ]; then
  echo "❌ HIGH severity findings. Full report: $REPORT"
  echo "   Bypass: git push --no-verify"
  exit 1
fi

echo "✅ Agent Team review passed. Report: $REPORT"
```

### Триггер / стоимость

- **Триггер:** `git commit` / `git push`
- **Где живёт код:** ноутбук разработчика
- **Кто платит:** разработчик, личным `ANTHROPIC_API_KEY` (env var)
- **Стоимость:** $0.10-2 per commit/push

✅ **Плюсы:**
- Уязвимости не уходят дальше локальной машины
- Fast feedback loop, не ждать CI

❌ **Минусы:**
- Медленно (5-30 сек pre-commit, 2-5 мин pre-push)
- Дорого если часто пушишь
- Каждый разработчик настраивает API key
- Agent Team в headless mode ~70% reliability
- Соблазн использовать `--no-verify` → правила перестают работать

⚠️ **Рекомендация:** pre-commit **только на critical paths** (auth/payments/crypto), pre-push с Agent Team — для опциональных солистов, не для team workflow.

---

## Вариант 3 — Cloud, GitHub Action + single Claude (production default) ⭐

**Когда:** хочешь автоматический review на каждый PR без блокирования разработчиков. Это **default mechanism для production**.

Один Claude (Sonnet 4.6) на каждый PR. Дёшево ($0.04-0.30), reliable (99%), масштабируется.

### Setup

#### 1. Добавить `ANTHROPIC_API_KEY` в repo secrets

GitHub → Settings → Secrets and variables → Actions → "New repository secret":
- Name: `ANTHROPIC_API_KEY`
- Value: твой API key из console.anthropic.com

#### 2. Скопировать workflow в `.github/workflows/`

Готовый YAML лежит в [`cloud-agent-team/claude-pr-review.yml`](cloud-agent-team/claude-pr-review.yml). Скопируй:

```bash
mkdir -p .github/workflows
cp aidev-course-materials/M6/6.1-ai-code-review/cloud-agent-team/claude-pr-review.yml .github/workflows/
```

**В этом workflow ДВА job'а:**
- `review-single` — single Claude на каждый PR (Вариант 3)
- `review-agent-team` — Agent Team только когда label `deep-review` (Вариант 4)

Если нужен только Вариант 3 — удали job `review-agent-team` из workflow.

#### 3. Commit + push на feature branch

```bash
git checkout -b ci/add-claude-review
git add .github/workflows/claude-pr-review.yml .claude/agents/
git commit -m "ci: add Claude PR review (single agent default)"
git push origin ci/add-claude-review
```

#### 4. Создать PR → workflow запустится автоматически

Через ~3-5 минут увидишь inline comments от Claude в PR.

### Триггер / стоимость

- **Триггер:** событие `pull_request: [opened, synchronize]`
- **Где живёт код:** GitHub-managed runner (ubuntu-latest)
- **Кто платит:** владелец repo через `ANTHROPIC_API_KEY` secret
- **Стоимость:**
  - ~$0.04 на 400-line PR (Sonnet)
  - ~$0.30 на 1500-line PR
  - Прогноз на команду 10 разработчиков × 5 PR/неделю = ~$80/мес

✅ **Плюсы:**
- 99% reliability — production-ready
- Не блокирует разработчиков локально
- Один секрет для команды, прозрачные расходы
- Inline comments прямо в GitHub PR UI
- Можно skip-ить через label `skip-review`

❌ **Минусы:**
- ~3-5 минут cold start GitHub runner
- Single agent = меньше depth (но достаточно для 95% PR)
- Зависит от GitHub runner uptime

### Управление расходами (cost guardrails)

В `claude_args` уже стоят лимиты, но можешь зажать сильнее:

```yaml
claude_args: >-
  --model claude-sonnet-4-6        # дешевле Opus в 5×
  --max-turns 8                     # лимит итераций tool calls
  --max-tokens 4096                 # cap на размер ответа
  --max-budget-usd 1.00             # hard stop по деньгам
```

Плюс в самом workflow:

```yaml
timeout-minutes: 10                 # kill switch
```

---

## Вариант 4 — Cloud, GitHub Action + Agent Team (advanced)

**Когда:** PR содержит крупное архитектурное изменение / security feature / DB migration — нужна полная депт-review с 3 специалистами.

**Ключевое отличие от Варианта 3:** YAML setup тот же, но (1) добавляется env var `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`, (2) промпт явно спавнит team из `.claude/agents/`.

### Setup

Workflow [`cloud-agent-team/claude-pr-review.yml`](cloud-agent-team/claude-pr-review.yml) уже содержит job `review-agent-team` со всеми настройками. Триггеры:

- **Manual (`workflow_dispatch`):** GitHub UI → Actions tab → "Claude PR Review" → "Run workflow" → выбрать `mode: agent-team` + PR number → Run
- **Label-triggered:** на любом PR ставишь label `deep-review` → workflow запустится автоматически

### Триггер / стоимость

- **Триггер:** label `deep-review` на PR ИЛИ ручной `workflow_dispatch`
- **Где живёт код:** GitHub-managed runner (ubuntu-latest)
- **Кто платит:** владелец repo через secret
- **Стоимость:** $0.50-2 per run на Opus 4.7

✅ **Плюсы:**
- Cost под контролем — не запускается на каждый PR
- Full Agent Team depth + inter-mate collaboration через mailbox
- Reports выкладываются как **GitHub Actions artifact** (`agent-team-reports-pr-N`), retention 30 дней

❌ **Минусы:**
- ~10-15 минут на запуск (4 параллельных CC процессов в runner'е)
- ~60% reliability (experimental Agent Team в CI ещё менее предсказуем)
- Стоит в ~10× больше чем Вариант 3
- Может падать на edge conflicts mate'ов

---

## Production-стратегия (3 слоя) — рекомендуется

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Local pre-commit (только critical paths)           │
│    └ Single Claude Sonnet, 5-30 сек, blocks commit on HIGH   │
│    └ Scope: backend/auth/, backend/payments/, secrets/       │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Cloud GitHub Action — single Claude (DEFAULT)      │
│    └ Sonnet 4.6, 3-5 мин, $0.04-0.30/PR, 99% reliability     │
│    └ NOT blocking merge — informational inline comments      │
│    └ Skip via label "skip-review"                             │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Cloud GitHub Action — Agent Team (MANUAL)          │
│    └ Opus 4.7, 10-15 мин, $0.50-2/PR, ~60% reliability        │
│    └ Triggered by label "deep-review" or workflow_dispatch    │
│    └ Reports as artifact + inline + summary comment           │
└──────────────────────────────────────────────────────────────┘
```

**Финальный merge gate** — человек (senior dev) с AI-findings перед глазами. AI **не блокирует merge автоматически** — он информирует, человек решает.

---

## Чек-лист setup'а (production)

### Все 3 слоя сразу

- [ ] `.claude/agents/` с mate-файлами (из [`../agents/`](../agents/))
- [ ] `CLAUDE.md` или `AGENTS.md` в корне (context для всех агентов)
- [ ] `docs/adr/*` если есть (для architecture-mate)
- [ ] `.husky/pre-commit` — Layer 1 (security on critical paths)
- [ ] `.github/workflows/claude-pr-review.yml` — Layer 2 + Layer 3 (из `cloud-agent-team/claude-pr-review.yml`)
- [ ] `ANTHROPIC_API_KEY` в GitHub repo secrets
- [ ] Бюджет alert в Anthropic Console (например, $50/мес для команды из 5)
- [ ] Labels `deep-review` и `skip-review` созданы в GitHub repo

### Тестирование

- [ ] Создать тестовый PR с baked-in проблемой (hardcoded secret, N+1) → Layer 2 должен поймать
- [ ] Добавить label `deep-review` → Layer 3 запустится (Agent Team)
- [ ] Добавить label `skip-review` → ничего не запустится
- [ ] Сделать commit в `backend/auth/` с уязвимостью → Layer 1 должен заблокировать

---

## Сравнительная таблица — что использовать когда

| Случай | Вариант | Почему |
|---|---|---|
| Учусь, отлаживаю промпты | 1 (manual) | Live debug, full control |
| Live demo группе | 1 (manual) | Visual, контролируемо |
| Защитить commit в `backend/auth/` | 2 (pre-commit hook) | Не уходит дальше локали |
| Защитить push на feature branch | 2 (pre-push hook) | Catches before CI |
| **Каждый PR в production** | **3 (cloud single)** | **Default. Cheap. Reliable.** |
| PR с архитектурным изменением | 4 (cloud Agent Team) | Full depth, 3 специалиста |
| PR с DB migration | 4 (cloud Agent Team) | Critical, нужен performance + security |
| Hot-fix urgent | skip (label `skip-review`) | Скорость важнее review |

---

## Связанные файлы

| Файл | Назначение |
|---|---|
| [`../agents/security-mate.md`](../agents/security-mate.md) | Security mate definition (OWASP Top 10) |
| [`../agents/architecture-mate.md`](../agents/architecture-mate.md) | Architecture mate definition (layer boundaries + ADR) |
| [`../agents/performance-mate.md`](../agents/performance-mate.md) | Performance mate definition (N+1 + memory) |
| [`../agents/legacy-auditor-mate.md`](../agents/legacy-auditor-mate.md) | Plan-mode orchestrator (discover repo + dispatch specialists + assemble living docs) |
| [`../agents/test-writer-mate.md`](../agents/test-writer-mate.md) | Test generation specialist (strong assertions, high MSI) |
| [`../agents/README.md`](../agents/README.md) | Обзор всей agent-библиотеки + два способа вызова (Task vs role-entry) |
| [`cloud-agent-team/claude-pr-review.yml`](cloud-agent-team/claude-pr-review.yml) | Production-ready GitHub Action (single + team) |
| [`cloud-agent-team/README.md`](cloud-agent-team/README.md) | Cloud Agent Team pack overview |
| [`tools-catalog.md`](tools-catalog.md) | Сравнение Claude Code Action с CodeRabbit / Qodo / Copilot CR + метрики F1/Precision/Recall |
| [`honest-risks.md`](honest-risks.md) | 5 production-инцидентов AI Code Review (что НЕ работает) |

---

## Дополнительные ссылки

- Claude Code Action (official): https://github.com/anthropics/claude-code-action
- Agent Teams docs (experimental): https://code.claude.com/docs/en/agent-teams
- Husky (git hooks для команды): https://github.com/typicode/husky
- Anthropic API console (бюджеты + ключи): https://console.anthropic.com/
- GitHub Actions syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- GitHub Actions billing (Free tier 2000 min/мес): https://docs.github.com/en/billing/managing-billing-for-github-actions
- Anthropic pricing: https://www.anthropic.com/pricing
