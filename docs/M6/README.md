# Модуль 6 — AI-Конвейер и Legacy: промышленный стандарт

> **Статус:** материалы выложены ДО занятия. Все рецепты, ссылки на тулы и домашка — здесь.
> **Дедлайн домашки M6:** перед стартом M7 (примерно 2 недели после занятия).

## О модуле

Это переходный модуль между «вы построили pipeline» (M2–M5) и «вы доводите его до production-уровня» (M7). Главный вопрос M6: где у AI-инструментов **реальные границы**, и как настроить процесс так, чтобы команда выиграла, а не утонула в false positives, silent corruption и stale documentation.

В M3 вы построили **руки** (MCP), в M4 — **глаза** (Dashboard), в M5 — **мозг** (n8n + агенты). В M6 вы добавляете **аудит и нервную систему** — Агента-Контролёра, который сам ходит по вашему `proshop_mern` fork'у, находит уязвимости, недокументированные модули и рефакторит legacy-слои.

К концу модуля у вас будет:
- запущенный **агент-аудитор** на собственном forked-проекте,
- 3 топовых finding'а исправленных через safe-refactor recipe,
- расширенный AGENTS.md / CLAUDE.md / project-index.json для своих M3–M5 модулей,
- (опционально) live mutation-testing замер MSI > 70% на одном модуле.

## Что в этой папке

| Файл / папка | Зачем |
|---|---|
| `homework-spec.md` | **Главный файл — полное ТЗ домашки** (4 stages, ~7-9 часов работы) |
| `agents/` | Shared библиотека из 5 универсальных mate-агентов (security / architecture / performance / legacy-auditor / test-writer) + README + templates/ |
| `6.1-ai-code-review/` | Topic 6.1: AI Code Review + Agent Teams. Рецепты + сравнение тулов + honest risks + cloud GitHub Action |
| `6.2-living-documentation/` | Topic 6.2: Living Documentation, AGENTS.md/CLAUDE.md, inline comments, project-index.json |
| `6.3-legacy-strategies/` | Topic 6.3: Стратегии работы с legacy. 4-step CC reverse engineering + 7 правил безопасного refactor |
| `6.4-synthetic-testing/` | Topic 6.4: Synthetic testing, mutation testing, coverage vs MSI, CI/CD layered strategy |

Каталог инструментов M6 со ссылками на docs / pricing — в `6.1-ai-code-review/tools-catalog.md`.

## Pre-read до занятия

В LMS Knowledge Base — 4 темы:
- **6.1 AI Code Review** — эталонная архитектура (webhook → LLM → CI/CD), 4 специализированных агента, calibration через CLAUDE.md/ADR, production cases (GitHub 90% adopt, Shopify -30% critical)
- **6.2 Живая документация** — RAG Freshness Rot (60% RAG fails), AGENTS.md под Linux Foundation, project-index.json, event-driven docs
- **6.3 Стратегии работы с Legacy** — 7 правил безопасного refactor, 5-фазный фреймворк, CodeConcise для 500K+ LOC
- **6.4 Synthetic Testing** — synthetic test-cases vs synthetic data, mutmut/cosmic-ray, Anthropic PBT-agent, CI/CD layered strategy

На живом занятии — **продуктовая оптика поверх LMS**: где AI работает (greenfield Python +50× ускорение), где буксует (enterprise legacy -20% senior productivity), и какую архитектуру процесса вокруг AI нужно построить, чтобы выигрывать.

## Связь с другими модулями

```
M2 (IDE + CC)          ─┐
M3 (MCP — руки)         ├──▶  M6 (Аудитор + Legacy)  ──▶  M7 (Privacy/Security/Cost)
M4 (Dashboard — глаза)  ├──▶                              prod hardening
M5 (Agents — мозг)      ─┘
```

Домашка M6 — **ваш собственный код M3–M5 + чужой BradTraversy 2020-х слой как тренировка** на legacy-практику.

## Где обсуждать вопросы

Студенческий Telegram-канал. Меточки `#m6-stage1`, `#m6-stage4`, `#m6-mutation-msi`, `#m6-agents-md` — для быстрой навигации в чате.
