# Topic 6.1 — AI Code Review + Agent Teams

Материалы по теме 6.1 курса AI-dev Level 1, Модуль 6 «AI-Конвейер и Legacy».

---

## Что в этой папке

| Файл / папка | Что внутри |
|---|---|
| `README.md` | Этот файл: обзор темы, ключевые идеи, ссылки |
| `tools-catalog.md` | Сравнение 5 инструментов AI Code Review (май 2026) |
| `claude-code-review-setup.md` | Универсальный setup-доку: 4 механизма запуска review (locally / hooks / GitHub Action single / Agent Team) |
| `cloud-agent-team/` | Production-ready GitHub Actions workflow (single + team) для cloud-режима |
| `honest-risks.md` | 5 production-рисков с митигациями и источниками |

> Все mate-агенты (security / architecture / performance / legacy-auditor / test-writer) живут в shared библиотеке [`../agents/`](../agents/) на уровне модуля.

---

## Главные идеи

- **Тэглайн:** «AI code review — не выбор тула, а архитектурный выбор: цензор (single-pass) vs партнёр (Agent Team peer-to-peer)». AI-coding ускорил написание кода, но создал bottleneck на review. Решение: изменить архитектуру процесса, а не наращивать темп.

- **4 специализированных агента (из LMS-теории):** security / performance / architecture / testing. Каждый получает только свои инструменты, работает изолированно, не пересекается по scope с другими.

- **Калибровка через CLAUDE.md + ADR:** operational context проекта — главный сигнал качества AI review. Без него AI остаётся цензором (adoption 16.6%) вместо партнёра (56.5%). Разница — в том, что AI знает о проекте.

- **Agent Teams (Anthropic, Feb 2026):** peer-to-peer mailbox на JSON-файлах. Внутри Anthropic: coverage 16% → 54%. Но: экспериментально, ~50% reliability, 2.5-4× токенов vs single agent.

- **Production кейсы:** Jellyfish (PR/dev 11.4 → 23.9, +110% за 9 мес), Stripe Minions review model, Claude Code managed avg $25/review. Метрика успеха: не FP rate, а **comment action rate >60% + cycle time -10-20%**.

---

## После урока — что читать первым

1. `tools-catalog.md` — выбрать тул для своей команды (таблица + рейтинг Signal/Noise).
2. `claude-code-review-setup.md` — выбрать механизм запуска (4 варианта, цена + reliability + setup-сложность).
3. `cloud-agent-team/README.md` + `cloud-agent-team/claude-pr-review.yml` — скопировать workflow в свой репо, настроить за 15 минут.
4. `honest-risks.md` — изучить 5 рисков перед production rollout.

---

## Дополнительные ссылки

- Anthropic Agent Teams (официальная дока): https://code.claude.com/docs/en/agent-teams
- Claude Code Action (GitHub): https://github.com/anthropics/claude-code-action
- CodeRabbit: https://www.coderabbit.ai / docs: https://docs.coderabbit.ai
- Qodo Merge: https://www.qodo.ai/products/qodo-merge/
- GitHub Copilot Code Review: https://github.com/features/copilot
- Cursor BugBot: https://www.cursor.com/bugbot
- Signal65 AI Code Review study (Mar 2026): https://signal65.com/wp-content/uploads/2026/03/Signal65-Insights_Evaluating-AI-Code-Review-Tools.pdf
- arXiv 2604.03196 (MSR 2026, CRA PR study): https://arxiv.org/abs/2604.03196
- arXiv 2603.15911 (adoption rate study): https://arxiv.org/abs/2603.15911
