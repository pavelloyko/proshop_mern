# Модуль 5 — Агенты и n8n: «Мозг» системы

> **Статус:** материалы выложены ДО занятия. Дедлайн домашки — отдельно перед стартом M6.

## О модуле

В M3 вы создали **руки** системы — MCP-сервер для управления feature flags. В M4 — **глаза**: Feature Dashboard в админке. M5 добавляет **мозг**: агентский workflow в n8n, который сам принимает решения и крутит ручки через MCP.

К концу модуля у вас будет замкнутый full-stack цикл: пользователь нажимает кнопку в Dashboard → n8n-агент через MCP меняет state → Dashboard обновляется. Параллельно — scheduled defensive monitor, который сам деактивирует фичу при всплеске ошибок.

## Что в этой папке

| Файл / папка | Зачем |
|---|---|
| `homework-spec.md` | **Главный файл — всё ТЗ домашки в одном месте**: 2 workflow с ASCII-схемами, frontend snippet, X-API-Key auth, 2 Python-симулятора с синусоидой, GCAO-промпты, 3 промпта для CC-субагентов, тест на галлюцинации + 5 appendices (best-practices, algorithm-before-AI, memory types, troubleshooting, defensive-guard HITL template). ~1950 строк. |
| `agents/README.md` | Как использовать 2 CC-субагента совместно: orchestrator → spec → workflow-builder → JSON |
| `agents/n8n-requirements-orchestrator.md` | CC-субагент: user story → детальный workflow spec |
| `agents/n8n-workflow-builder.md` | CC-субагент: spec → валидный n8n JSON |
| `guides/browser-use-prompt-injection-defenses.md` | Отдельный security-reference: как защищают от prompt injection в browser-агентах (теория, не про домашку, читать опционально) |
| `guides/crewai-vs-n8n.md` | Сравнение CrewAI и n8n: когда что выбирать, гибридный паттерн |
| `guides/cloud-n8n-local-services.md` | **Если ваш n8n в облаке, а MCP/Dashboard/logs локально:** как пробросить локальные сервисы публичным HTTPS через Cloudflare quick tunnel. Docker Compose-фрагмент + примеры нод. Не часть требований домашки — справочник для совпадающего сценария. |
| `n8n Workflows/` | Справочные коллекции workflow для самостоятельного изучения: ссылки на upstream-репозитории (awesome-n8n-templates, n8n-workflows) + локальная подборка из community-таблицы. Не относится к сдаче — reference. См. `n8n Workflows/README.md`. |

## Pre-read до занятия

В LMS Knowledge Base — 4 темы:
- **5.1 Анатомия агента** — ReAct, Plan-and-Execute, Reflexion, write-manage-read цикл памяти
- **5.2 Low-code оркестрация в n8n** — AI Agent node, минимальная продакшн-связка
- **5.3 Управление состоянием** — типы памяти, чекпоинтеры, time-travel
- **5.4 Связка UI + Агент + MCP** — Algorithm-before-AI, Tool Isolation, eval-цикл

На живом занятии Сергей сверху даёт продуктовую рамку: GCAO как production-промпт-каркас, виды агентов (8+1 типов), ландшафт фреймворков 2026, история n8n, CC + n8n как новый стандарт разработки workflow.

## Связь с другими модулями

```
M3 (MCP — руки)           ──┐
                              ├──▶  M5 (Agent — мозг)  ──▶  Замкнутый цикл
M4 (Dashboard — глаза)    ──┘                                full-stack
                                                              │
                                                              ▼
                                                              M6 (Auditor — контролёр)
```

В M6 мы создадим Агента-Контролёра, который пройдётся по тому же `proshop_mern` с другой ролью — аудитор кода. Тот же agentic паттерн, другая задача.

## Что вы вынесете

- Понимание **анатомии агента** в production-коде: GCAO в system prompt + Structured Output на каждом шаге
- Связку **UI ↔ Agent ↔ MCP** на собственном проекте — full-stack замкнутый цикл
- Привычку строить **детерминированные guards** до и после LLM (Algorithm-before-AI) вместо «надежды на здравый смысл модели»
- Опыт двух production-сценариев: manual (синхронный) + scheduled (асинхронный)
- Базу для M6 (Агент-Контролёр)

---

*M5 — HSS AI-dev L1. Дедлайн домашки и способ сдачи — в чате курса.*
