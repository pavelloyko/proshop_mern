# Multi-level docs stack — 8 уровней живой документации

> **Главная идея:** один слой документации недостаточен. Только `README.md` — мало. Только OpenAPI — мало. Только `CLAUDE.md` — мало. Эффективная живая документация 2026 — это **8 уровней**, каждый под свой контекст и аудиторию.

---

## Зачем 8 уровней — продуктовая логика

Когда у тебя 1 репо и 1 разработчик — хватает README. Когда у тебя **15+ репо** или **100+ микросервисов** — README не масштабируется:

- **Разработчик** ищет: «как запустить?» → README + Quick-start
- **AI-агент** ищет: «какие conventions у этого проекта?» → `AGENTS.md`
- **API consumer** ищет: «какой контракт у /api/orders?» → OpenAPI spec
- **PM** ищет: «кто owner сервиса payments-svc?» → Backstage catalog-info
- **Architect** ищет: «почему мы выбрали PostgreSQL, а не Mongo?» → ADR
- **On-call** ищет: «что делать когда DB упала?» → Runbook
- **Audit** ищет: «какие персональные данные у нас в системе?» → Wiki + compliance docs
- **AI-агент в IDE** ищет: «какие у тебя файлы и где что лежит?» → `project-index.json`

**Каждый из этих 8 контекстов = отдельный слой документации.** Слои авто-синкаются через PR-триггеры (это и есть «живая» в названии).

---

## Полная таблица — 8 уровней

| # | Уровень | Артефакт | Auto-gen tool | AI-readability | Кто читает |
|---|---|---|---|---|---|
| **1** | **Code** | `///` XML-doc / docstrings / JSDoc | DocFX, pdoc, JSDoc, TypeDoc | ★★★★★ (направлено на AI) | LLM при чтении файла, IDE hover |
| **2** | **Repo** | `README.md` (Role / Owner / On-call / Quick-start / Endpoints / Dependencies / Runbook) | readme-ai, GitHub AI Writer | ★★★★ | Разработчик при первом knock'е, AI при `tree -L 2` |
| **3** | **API** | OpenAPI 3.1 auto-spec из аннотаций | Swashbuckle (.NET), FastAPI (Python), tsoa (TS), springdoc (Java) | ★★★★★ (typed contract) | API consumer, fronend, codegen для клиентов |
| **4** | **Catalog** | `catalog-info.yaml` (Backstage) | manual + scaffold templates | ★★★★ | PM, SRE, on-call rotation |
| **5** | **Architecture** | ADR (Markdown) + C4 diagrams (Mermaid / draw.io) | adr-tools, log4brains, auto-adr | ★★★ (human + AI) | Architect, новый senior dev, AI при «почему такое решение?» |
| **6** | **Operational** | Runbooks + PagerDuty playbooks | автогенерация из incidents (Datadog AI) | ★★★ | On-call инженер в 3 ночи |
| **7** | **Wiki** | Azure DevOps Wiki / GitBook / TechDocs / Confluence | DocFX → wikiMaster branch | ★★★★★ (search-indexed) | Кросс-командный поиск, audit, новый сотрудник |
| **8** | **AI-context** | `CLAUDE.md` / `AGENTS.md` / `project-index.json` | `update_project_index.py` (custom), Anthropic /init | ★★★★★ (designed for AI) | Claude Code / Codex / Cursor / Windsurf при старте сессии |

---

## Как каждый слой обновляется — таблица событий и автоматизации

> «Живая» документация = слой обновляется **автоматически по событию**, не по расписанию (cron-расписание оставляет 24-часовое окно где docs устарели).

| # | Уровень | Триггер обновления | Как именно | Кто валидирует |
|---|---|---|---|---|
| 1 | Code | На PR / `pre-commit` | `pre-commit` hook запускает linter с обязательным docstring check | CI блокирует merge если нет docstring у public function |
| 2 | Repo | Manual + AI-assist | Раз в квартал PR с `readme-ai` regen | Human review |
| 3 | API | На build / PR | OpenAPI генерируется из кода → `openapi.json` коммитится в `/docs` | CI сравнивает с previous version, ломает build на breaking change без version bump |
| 4 | Catalog | На `git push` нового сервиса | `catalog-info.yaml` обязателен в каждом репо, Backstage scrapes | Backstage UI shows orphaned services |
| 5 | Architecture | На большое решение (manual) | Разработчик создаёт ADR через `adr new "..."` команду | Tech lead approves в PR |
| 6 | Operational | После incident (manual + AI-suggest) | Postmortem → runbook. AI-агент предлагает draft на основе incident timeline | On-call инженер тестирует runbook на следующем drill'e |
| 7 | Wiki | На каждый docs PR | `DocFX` → push to `wikiMaster` branch → Azure DevOps Wiki индексирует | Search-quality eval раз в месяц |
| 8 | AI-context | На любое изменение структуры | `update_project_index.py` hook на `mv` / `rm` / `mkdir` | Hard rule в CLAUDE.md: «при создании папки запустить script» |

---

## Прогрессивное раскрытие (progressive disclosure) — главный паттерн

> AI-агент не может прочитать всё. У него ограниченный контекст (200K-1M токенов), но **деградация качества начинается с 50K**. Поэтому нельзя «вывалить» всю документацию в один файл.

**Решение — пирамида читаемости:**

```
                ┌──────────────────────────────┐
                │  CLAUDE.md / AGENTS.md       │  ← ~100-200 строк
                │  «Указатели и conventions»   │     читается КАЖДУЮ сессию
                └──────────────────────────────┘
                             │
                             ▼  (агент по запросу)
                ┌──────────────────────────────┐
                │  docs/architecture/*.md      │  ← 500-2000 строк
                │  docs/adr/*.md               │     читается ПО НУЖДЕ
                │  reference/*.md              │
                └──────────────────────────────┘
                             │
                             ▼  (агент глубже)
                ┌──────────────────────────────┐
                │  Полный source code          │  ← всё остальное
                │  Tests, migrations, configs  │     читается ТОЧЕЧНО (Read + Grep)
                └──────────────────────────────┘
```

**Правила:**
- **Top-level `CLAUDE.md` / `AGENTS.md`** содержит **только указатели**: «если про auth → читай `docs/auth/CONVENTIONS.md`».
- **Никогда не дублируй** содержимое из reference в CLAUDE.md.
- **Размер ≤200 строк** для top-level (ETH Zurich SRI Lab: больше → деградация SWE-bench в 5 из 8 настроек).
- **Inline-комментарии** в коде для местных правил, не в CLAUDE.md.

OpenAI internal репо использует **88 `AGENTS.md` файлов** (по одному на подпапку) — каждый под свой sub-context. Это и есть progressive disclosure в production.

---

## `project-index.json` + AGENTS.md/CLAUDE.md — Layer 8 в деталях

Это **самый AI-ориентированный** уровень. Состоит из 3 артефактов:

### 1. `project-index.json` — machine-readable граф структуры

JSON-файл в корне репозитория. Описывает:

```json
{
  "name": "proshop_mern",
  "type": "fullstack-monorepo",
  "subprojects": {
    "backend": {
      "path": "backend/",
      "tech": "Node.js + Express + Mongoose",
      "owner": "@team-backend",
      "claude_md": "backend/CLAUDE.md"
    },
    "frontend": {
      "path": "frontend/",
      "tech": "React 16 + Redux thunk",
      "owner": "@team-frontend",
      "claude_md": "frontend/CLAUDE.md"
    },
    "mcp": {
      "path": "mcp/",
      "tech": "Python MCP server",
      "owner": "@<your-name>",
      "claude_md": "mcp/README.md"
    }
  },
  "system_folders": {
    ".claude/": "Claude Code agent definitions",
    "docs/adr/": "Architecture Decision Records"
  },
  "hard_rules": [
    "ВСЕГДА запускать update_project_index.py при создании/удалении папки",
    "НИКОГДА не редактировать backend/features.json вручную — через MCP"
  ],
  "last_updated": "2026-05-18T14:23:00Z"
}
```

AI-агент читает этот файл **в начале сессии** и знает структуру за 1 read, без `find` / `tree`.

### 2. `AGENTS.md` (или `CLAUDE.md` — это один файл)

Operational rules для AI: tone, conventions, do/don't, project gotchas.

- **AGENTS.md** — открытый стандарт под Linux Foundation / AAIF (60K+ репо)
- **CLAUDE.md** — Anthropic-specific (Claude Code читает по умолчанию)
- **Решение:** `ln -s AGENTS.md CLAUDE.md` (symlink) — оба инструмента видят один файл

### 3. Per-subproject `CLAUDE.md` / `AGENTS.md`

Каждый подпроект имеет свой `CLAUDE.md` с локальными conventions. Top-level ссылается на них через `project-index.json`.

---

## Scaled-down версии — что брать в зависимости от размера команды

### Solo разработчик / pet-project (1 репо)

Берёшь только:
- **Layer 1** — docstrings на public functions
- **Layer 2** — README с Quick-start
- **Layer 8** — `CLAUDE.md` (basic conventions)

Опускаешь: API auto-spec, catalog, ADR, runbooks, wiki.

### PM на 15+ репо / small startup

Берёшь:
- **Layer 1** — minimal (docstrings только в critical paths)
- **Layer 2** — README в каждом подпроекте
- **Layer 3** — OpenAPI для public endpoints
- **Layer 5** — ADR для крупных решений (квартально)
- **Layer 8** — `project-index.json` + top-level `CLAUDE.md` + per-subproject `CLAUDE.md`

Опускаешь: catalog (нет 100+ сервисов), runbooks (нет on-call ротации), wiki (всё в repo markdown).

### Enterprise / 100+ микросервисов

Все 8 уровней + auto-sync pipeline:

```
1. Build pipeline scans XML-doc + markdown
2. PR triggers regeneration of OpenAPI + Catalog + Wiki
3. Push to Wiki branch (git push origin wikiMaster)
4. Wiki indexes content (full-text search ready in seconds)
5. Backstage scrapes catalog-info.yaml → service ownership graph
6. PagerDuty syncs on-call ротация
```

В одном крупном enterprise-консалтинг кейсе (100+ микросервисов): **before** этого стека — 0 README, <3% files с XML-doc, 0 ADR, 2 architecture guides на 108 проектов. **После** внедрения — quarterly cadence ADR, 100% public APIs с OpenAPI, MTTU (mean time to understand) для нового инженера: 1-2 недели → 2-3 дня.

---

## Где какой слой документации хранится — пример каталога

```
my-project/
├── AGENTS.md                          # ← Layer 8 (top-level, ≤200 строк)
├── CLAUDE.md → AGENTS.md              # ← symlink (Layer 8)
├── project-index.json                 # ← Layer 8 (machine-readable граф)
├── README.md                          # ← Layer 2 (Quick-start)
│
├── docs/
│   ├── adr/                           # ← Layer 5 (Architecture Decision Records)
│   │   ├── ADR-001-database-choice.md
│   │   └── ADR-002-auth-jwt-vs-session.md
│   ├── architecture/                  # ← Layer 5 (C4 diagrams)
│   │   ├── context.mermaid
│   │   └── containers.mermaid
│   ├── runbooks/                      # ← Layer 6 (Operational)
│   │   ├── db-recovery.md
│   │   └── cache-invalidation.md
│   └── openapi/                       # ← Layer 3 (API contract)
│       └── openapi.json
│
├── catalog-info.yaml                  # ← Layer 4 (Backstage)
│
├── backend/
│   ├── CLAUDE.md                      # ← Layer 8 (per-subproject)
│   ├── README.md                      # ← Layer 2 (backend Quick-start)
│   └── controllers/
│       └── userController.js          # ← Layer 1 (docstrings inline)
│
└── frontend/
    ├── CLAUDE.md                      # ← Layer 8 (per-subproject)
    └── README.md                      # ← Layer 2 (frontend Quick-start)
```

---

## Quick decision — какой слой добавить следующим

**Если у тебя сейчас:**

| Текущая ситуация | Следующий слой | Почему |
|---|---|---|
| Только README | Layer 8 (`CLAUDE.md`) | AI-агент получает контекст с первого сообщения |
| README + CLAUDE.md | Layer 3 (OpenAPI) если есть public API | Typed contract для frontend / клиентов |
| Всё выше + 5+ репо | Layer 8.2 (`project-index.json`) | AI перестаёт делать `find` каждый раз |
| Всё выше + 10+ архитектурных решений в истории | Layer 5 (ADR) | Новые разработчики не задают одни и те же вопросы |
| Всё выше + production incidents | Layer 6 (runbooks) | On-call не паникует ночью |
| Всё выше + cross-team поиск нужен | Layer 7 (Wiki) | Search-indexed shared knowledge |
| Всё выше + 20+ микросервисов | Layer 4 (Backstage) | Ownership + dependency graph |

**Не нужно делать всё сразу.** Добавляй слои по мере роста проекта / команды.

---

## Связанные файлы

- [`agents-md-claude-md-standard.md`](agents-md-claude-md-standard.md) — деталь по Layer 8: AGENTS.md / CLAUDE.md format, optimal size, anti-patterns
- [`recipe-inline-comments.md`](recipe-inline-comments.md) — деталь по Layer 1: когда inline-комментарии лучше глобальных rules
- [`numbers-card.md`](numbers-card.md) — ключевые цифры (60K+ репо, RAG Freshness Rot 60%, ETH Zurich SWE-bench)

---

## Дополнительные ссылки

- AGENTS.md spec (Linux Foundation): https://agentsmd.com
- Anthropic Claude Code docs: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code
- Backstage TechDocs: https://backstage.io/docs/features/techdocs
- DocFX (.NET docs generator): https://dotnet.github.io/docfx
- Anthropic Sub-agents reference: https://docs.anthropic.com/en/docs/build-with-claude/sub-agents
- Cole Medin on CLAUDE.md sizing: публичный блог автора (поиск «Cole Medin AGENTS.md»)
- adr-tools (manage ADRs): https://github.com/npryce/adr-tools
- log4brains (visualise ADRs): https://github.com/thomvaill/log4brains
