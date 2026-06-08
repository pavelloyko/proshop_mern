# AGENTS.md / CLAUDE.md — стандарт операционного контекста для AI-агентов

> Референс-гайд для прочтения после урока. Покрывает историю стандарта, формат,
> оптимальный размер, symlink-паттерн, прогрессивное раскрытие и примеры.

---

## История и экосистема

**9 декабря 2025** — AGENTS.md передан в Linux Foundation под структуру
**Agentic AI Foundation (AAIF)** — нейтральный дом для open, vendor-agnostic стандарта.

На момент передачи: **60K+ репозиториев** уже содержали AGENTS.md.

Поддерживают стандарт AGENTS.md:

| Инструмент | Статус |
|---|---|
| OpenAI Codex | Поддержка AGENTS.md |
| GitHub Copilot | Поддержка AGENTS.md |
| Cursor | Поддержка AGENTS.md |
| Windsurf | Поддержка AGENTS.md |
| Amp | Поддержка AGENTS.md |
| Devin | Поддержка AGENTS.md |
| Jules | Поддержка AGENTS.md |
| Aider | Поддержка AGENTS.md |
| **Claude Code** | Читает **CLAUDE.md** (workaround: symlink) |

Масштаб внедрения: OpenAI внутренний репо содержит **88 AGENTS.md файлов** — паттерн
прогрессивного раскрытия в действии (не один монолитный файл, а иерархия).

---

## Что такое AGENTS.md / CLAUDE.md

Это **операционный контекст для AI-агента** — не документация для людей. Агент читает
его в начале каждой сессии и использует как базу для принятия решений:

- Что делает проект (цель, стек, архитектура)
- Какие соглашения (naming, структура, commit style)
- Какие команды доступны (make test, npm run dev, ...)
- Какие правила нельзя нарушать (security, deprecated APIs, env setup)
- Куда смотреть за деталями (ссылки на docs/, reference/, skills/)

Ключевое отличие от README: AGENTS.md написан **для машины**, не для нового разработчика.

---

## Формат: рекомендуемые секции

```markdown
# Project

Одно предложение: что это, для чего, ключевые технологии.

## Architecture

Краткое описание структуры: какие директории за что отвечают,
как компоненты связаны.

## Conventions

- Соглашения по коду (язык, стиль, naming)
- Commit message format
- Branch strategy

## Commands

```bash
npm install          # установка зависимостей
npm run dev          # локальный сервер
npm test             # тесты
npm run build        # продакшн сборка
```

## Key constraints

- Что НЕЛЬЗЯ делать в этом проекте (явные запреты)
- Критические зависимости / совместимость версий
- Где хранится source of truth для конфигурации

## References

- docs/architecture/ — архитектурные решения (ADR)
- docs/runbooks/     — операционные руководства
- .claude/rules/     — детальные правила по категориям
```

---

## Минимальный пример: proshop_mern (~80 строк)

```markdown
# proshop_mern — MERN e-commerce reference project

Full-stack MERN (MongoDB, Express, React, Node.js) e-commerce app.
Used as course homework baseline for M2-M7.

## Architecture

- backend/  — Express API, MongoDB via Mongoose
- frontend/ — React + Redux Toolkit, Vite
- mcp/      — MCP server for feature flags (M3 homework)
- rag/       — RAG integration (M4 homework)

## Commands

```bash
# Backend
cd backend && npm install && npm run dev    # port 5000
# Frontend
cd frontend && npm install && npm run dev   # port 3000
# MCP server
cd mcp && pip install -r requirements.txt
python feature_flags_server.py
```

## Conventions

- API routes: RESTful, versioned /api/v1/
- Auth: JWT in httpOnly cookie (NOT localStorage)
- Env: docker-compose.yaml env_file IS source of truth.
  Do NOT add ARG in Dockerfile — breaks layered config.
- Tests: pytest for mcp/, jest for frontend

## Key constraints

- Node >= 18, Python >= 3.11
- MongoDB connection string in .env (never hardcode)
- Feature flags: always check via MCP server, never hardcode boolean

## References

- docs/          — architecture decisions, runbooks
- AGENTS.md      — this file (symlinked as CLAUDE.md)
- mcp/           — M3: feature flags MCP server
```

---

## Оптимальный размер

Исследования и практика 2025-2026 сходятся на диапазоне:

| Источник | Рекомендация |
|---|---|
| Nate Herk (практик, Claude Code) | ~87 строк |
| Cole Medin (практик, multi-agent) | ~233 строки |
| Anthropic официально | < 200 строк |

**Диапазон 87–233 строк** — оптимум для одного AGENTS.md файла.

### Почему размер критичен

**ETH Zurich SRI Lab (2025):** раздутые AGENTS.md (>200 строк) увеличивают inference
cost более чем на 20% и в 5 из 8 настроек SWE-bench Lite / AGENTbench **снижают**
долю успешно решённых задач.

**Chroma Research (2025):** на 18 моделях при росте длины input точность деградирует
с 95% до 60-70%. Модели помнят начало и конец промта значительно лучше середины.

**Vercel AGENTS.md = 19 000 токенов** — публичный анти-эталон. Это ухудшает результаты
согласно обоим исследованиям.

---

## Symlink-паттерн: один источник, два harness

Claude Code читает **CLAUDE.md**. Большинство других инструментов читают **AGENTS.md**.
Решение — symlink:

```bash
# Вариант 1: AGENTS.md — главный, CLAUDE.md — ссылка
ln -s AGENTS.md CLAUDE.md

# Вариант 2: CLAUDE.md — главный, AGENTS.md — ссылка
ln -s CLAUDE.md AGENTS.md
```

Проверить:
```bash
ls -la CLAUDE.md
# → CLAUDE.md -> AGENTS.md
```

Этот паттерн валидирован на реальном монорепо со множеством подпроектов
(проверяется через `ls -la` в demo на уроке).

**Важно:** при редактировании всегда править оригинальный файл, не symlink.
Иначе symlink будет заменён на обычный файл.

---

## Прогрессивное раскрытие

Для проектов с 15+ репозиториями или монорепо 100K+ файлов один AGENTS.md не справляется.
Архитектура прогрессивного раскрытия:

```
AGENTS.md (~100 строк)          ← агент читает всегда
    │
    ├── docs/architecture/      ← читается при архитектурных вопросах
    ├── docs/runbooks/          ← читается при операционных задачах
    ├── .claude/rules/          ← детальные правила по категориям
    └── .claude/skills/         ← on-demand specialized knowledge
```

Паттерн OpenAI internal: **88 AGENTS.md файлов** в разных директориях. Каждый описывает
свою зону ответственности. Корневой AGENTS.md содержит указатели, детали — в дочерних.

Для мульти-репо: добавить `project-index.json` — машиночитаемый граф структуры,
который агент читает в начале сессии. Содержит: список подпроектов, их цели,
nested repos, filesystem tree до глубины 4.

---

## Варианты совместимости для команд с несколькими инструментами

| Подход | Когда использовать |
|---|---|
| Единый AGENTS.md + symlink CLAUDE.md | 2-3 инструмента в команде |
| AGENTS.md + `@AGENTS.md` import в начале CLAUDE.md | Claude Code primary, Codex secondary |
| Adapter-скрипт (~30 строк): AGENTS.md → CLAUDE.md + `.cursor/rules/` + `.windsurfrules` | 4+ инструмента, частое расхождение |
| Специализированные файлы по типу (9-файловый OpenClaw, Kiro Agent Steering) | Команды с opinionated workflow |

**Bloated-файл (Vercel-style, 19K токенов):** не рекомендуется. Исследования показывают
деградацию результатов на 5 из 8 бенчмарков.

---

## Формула обоснования инвестиций

Cole Medin (практик multi-agent систем):

> «1 строка плохого PRD = 1000 строк плохого кода»

Инвестиция в качество AGENTS.md окупается не через «красивые доки», а через снижение
количества неправильно написанного кода и переработок.

---

## Внешние ссылки

- **agentsmd.com** — официальный сайт стандарта
- **Anthropic CLAUDE.md docs** — https://docs.anthropic.com/en/docs/claude-code/memory
- **Linux Foundation AAIF** — https://agentaiif.org/
- **GitHub: `filename:AGENTS.md`** — примеры в open-source репозиториях
