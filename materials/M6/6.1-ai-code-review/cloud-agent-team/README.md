# Cloud Agent Team — GitHub Actions workflow для AI Code Review

Папка содержит **production-ready** конфигурацию для запуска review через Claude Code в GitHub Actions:

| Файл | Что |
|---|---|
| `claude-pr-review.yml` | GitHub Actions workflow с двумя режимами (single agent + Agent Team) |
| `README.md` | Этот файл — обзор cloud-режима, setup, стоимость, mailbox |

> ⚠️ **Sub-agent definitions переехали** в [`../../agents/`](../../agents/) — это shared библиотека на весь M6 (не только для cloud-режима). Все 5 mate-агентов (`security-mate`, `architecture-mate`, `performance-mate`, `legacy-auditor-mate`, `test-writer-mate`) лежат там.

Все agent-файлы работают на **Opus 4.7** (`claude-opus-4-7`) с **read-only tools** (Read / Grep / Glob / Bash для безопасных команд типа `gh pr diff`).

---

## Как использовать

### Вариант A — локально в Claude Code сессии

1. Скопируй mate-агентов из `M6/agents/` в свой проект:
   ```bash
   mkdir -p .claude/agents
   cp aidev-course-materials/M6/agents/*.md .claude/agents/
   ```

2. Включи Agent Teams flag в `.claude/settings.json`:
   ```json
   {"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}
   ```

3. Запусти CC сессию и вставь команду:
   ```
   Spawn agent team from .claude/agents/ (security-mate, architecture-mate, performance-mate).
   Review my current branch diff against main. Write findings to .agent-team-reports/.
   ```

### Вариант B — в GitHub Actions (cloud)

1. Скопируй `claude-pr-review.yml` в `.github/workflows/`:
   ```bash
   mkdir -p .github/workflows
   cp cloud-agent-team/claude-pr-review.yml .github/workflows/
   ```

2. Скопируй agents в `.claude/agents/` (см. Вариант A, шаг 1).

3. Добавь `ANTHROPIC_API_KEY` в GitHub repo secrets:
   GitHub → Settings → Secrets and variables → Actions → New repository secret.

4. Commit + push. Workflow срабатывает автоматически:
   - **Default mode** (single agent, Sonnet) — на каждый PR
   - **Agent Team mode** (Opus 4.7) — когда на PR ставят label `deep-review`

---

## Что делает каждый агент

### security-mate (OWASP Top 10 + secrets + crypto)

- Sканирует diff на injection / XSS / SSRF / auth bypass
- Проверяет hardcoded credentials в коде и конфигах
- Анализирует password hashing, JWT verification, session cookies
- Запускает `npm audit` / `pip-audit` для dependency CVE
- **Role-locked:** только finding, без fixes

### architecture-mate (layer boundaries + ADR compliance)

- Читает `docs/adr/*` ПЕРЕД review
- Проверяет соответствие diff'а принятым ADR
- Ищет layer violations (DB call в route handler, business logic в view)
- Детектит breaking changes в public API
- Драфтит **новые ADR в Nygard format** для архитектурных решений без документации
- Criticality: C1 (irreversible) / C2 (reversible with effort) / C3 (hygiene)

### performance-mate (N+1 + memory + throughput)

- Ищет N+1 queries, blocking I/O, memory leaks
- Анализирует bundle size, lazy imports, caching opportunities
- Оценивает impact **квантитативно** (мс, MB) когда возможно
- Frontend: Core Web Vitals (LCP/CLS/FID)
- Backend: connection pooling, DB indexes, transaction scope

---

## Mailbox / peer-to-peer collaboration

Mate'ы могут писать друг другу через JSON inbox:
- `.claude/teams/{team-id}/inboxes/security-mate.jsonl`
- `.claude/teams/{team-id}/inboxes/architecture-mate.jsonl`
- `.claude/teams/{team-id}/inboxes/performance-mate.jsonl`

**Типичные cross-mate сценарии:**

| Кто пишет | Кому | Зачем |
|---|---|---|
| security-mate | architecture-mate | «Missing rate-limit on /login — это ADR-004 violation?» |
| security-mate | performance-mate | «ReDoS в /search regex — есть DoS impact?» |
| architecture-mate | security-mate | «ADR-008 требует payment abstraction — твой finding на Stripe call upgrade-ить?» |
| architecture-mate | performance-mate | «N+1 в getMyOrders — это симптом missing service layer?» |
| performance-mate | security-mate | «Memory leak на auth endpoint — DoS vector?» |

Mate ожидает ответа до **30 сек**, потом продолжает с best judgment + помечает finding `"crossref": "no response"`.

---

## Output — где найти результаты

После завершения работы команды в `.agent-team-reports/`:

```
.agent-team-reports/
├── security-findings.jsonl       # JSON Lines, по одному finding на строку
├── security-summary.md           # Human-readable summary
├── architecture-findings.jsonl
├── architecture-summary.md
├── performance-findings.jsonl
├── performance-summary.md
├── proposed-adrs/                # Драфты ADR от architecture-mate
│   └── ADR-NN-draft.md
└── synthesis.md                  # Финальный отчёт от lead'а
```

В GitHub Actions reports выкладываются как **artifact** (`agent-team-reports-pr-N`), retention 30 дней.

---

## Стоимость и SLA

| Режим | Время | Cost per PR | Reliability |
|---|---|---|---|
| Single agent (Sonnet) | 3-5 мин | $0.04-0.30 | 99% |
| Agent Team (Opus 4.7) | 10-15 мин | $0.50-2 | ~60% (experimental) |

**Рекомендация:** Single agent на каждый PR (Layer 2), Agent Team только при label `deep-review` (Layer 3). Подробнее — `../review-trigger-mechanisms.md`.

---

## Дополнительные ссылки

- Анатомия каждого варианта запуска: `../review-trigger-mechanisms.md`
- Сравнение с другими CR tools: `../tools-catalog.md`
- Метрики (F1/Precision/Recall): `../tools-catalog.md#как-читать-метрики-f1--precision--recall`
- Honest risks: `../honest-risks.md`
- Claude Code Action: https://github.com/anthropics/claude-code-action
- Agent Teams official docs: https://code.claude.com/docs/en/agent-teams
