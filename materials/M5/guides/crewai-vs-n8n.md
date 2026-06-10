# CrewAI vs n8n — детальное сравнение (M5)

> Какой фреймворк выбрать для AI-агентов: low-code workflow-платформу n8n или code-first multi-agent фреймворк CrewAI. Distilled из практики и публичных источников Q1-Q2 2026.

---

## TL;DR за 30 секунд

| Параметр | **n8n** | **CrewAI** |
|---|---|---|
| **Тип** | Low-code workflow automation + AI Agent ноды | Code-first multi-agent framework (Python) |
| **Главное «для чего»** | Связать N сервисов и встроить AI как один из узлов | Команда AI-агентов с разными ролями работает над общей задачей |
| **UI** | Drag-and-drop canvas | Код + YAML, плюс визуальный builder в платном CrewAI AMP |
| **Язык** | JavaScript / Python в коде нод, всё остальное визуально | Python only (JS/TS SDK нет) |
| **Лицензия ядра** | Sustainable Use License (fair-code, **НЕ** OSI-open-source) | MIT (настоящий open source) |
| **GitHub stars** | ~172-184K (top GitHub 2025) | ~50K, 300 contributors |
| **Self-host бесплатно?** | Да, Community Edition без лимитов на workflows | Да, MIT-ядро, self-host где угодно |
| **Платные тарифы** | n8n Cloud €20-24/€50-60/€667/мес + Enterprise custom | CrewAI Cloud $29/1K runs или $99/5K runs + Ultra ~$120K/год (on-prem) |
| **Под капотом** | LangChain.js (нативные AI ноды) | Написан **с нуля без LangChain** |
| **Идеален для** | Интеграции 400+ сервисов + AI как компонент | Multi-agent reasoning, role-based teams |
| **Главная боль** | Слабо тянет 4-5+ инструментов в одном агенте | Дебаг multi-agent непредсказуем; uncapped runs могут стоить $400+ |

**Если за 1 строку:** *n8n — это пайпы и интеграции с AI вкраплениями. CrewAI — это команда AI-агентов, которая работает совместно над задачей. Часто их используют **вместе**, а не вместо друг друга.*

> ⚠️ **Важное предупреждение:** сравнивать CrewAI vs n8n напрямую — это **категориальная ошибка**. Они решают разные задачи на разных уровнях абстракции. n8n — это **low-code платформа интеграции и оркестровки**. CrewAI — это **code-first multi-agent фреймворк**. Прямые конкуренты:
>
> - **n8n** ↔ Make.com, Zapier, Flowise, Pipedream, **Activepieces** (MIT-альтернатива)
> - **CrewAI** ↔ LangGraph, Pydantic AI, AutoGen, Mastra, OpenAI Agents SDK, OpenAI Swarm
>
> Сравнение CrewAI vs n8n имеет смысл при выборе **архитектурного подхода** для задачи (code vs no-code), а не как «А или Б». На практике они часто **комплементарны**.

---

## 1. Что это такое — короткие определения

### n8n

**Workflow automation platform** с визуальным редактором (drag-and-drop ноды). Изначально (2019) — конкурент Zapier/Make для соединения сервисов. С 2024 добавил полноценный AI Agent node на базе LangChain.js, тысячи AI-нод от комьюнити, и в Q1 2026 — native MCP server, Data Tables, Evaluations + Guard Rails, HITL gating.

Ключевая идея: **AI — это один из узлов в детерминированном графе**, не центр системы. Граф управляет агентом, не наоборот.

**Текущее состояние (Q2 2026):**
- ~172-184K GitHub stars (точное число варьируется по источникам и моменту съёма), **200K+ активных пользователей**, **$40M ARR**
- **$180M Series C @ $2.5B valuation** (lead Accel; co-investors включая NVentures от NVIDIA)
- **400+ официальных интеграций**, 5,300+ community npm пакетов
- 37 официальных AI-нод + ~1,500 community
- **6,000+ workflow-шаблонов** в marketplace + 4,000+ на n8nworkflows.xyz (community)
- **3,000+ enterprise клиентов** в production (Vodafone, Microsoft, Delivery Hero, Wayfair, DPD, Speakeasy)
- Прошёл security audit кодовой базы от Google → упрощён Google OAuth flow

### CrewAI

**Python multi-agent framework**, написанный **с нуля** (не поверх LangChain — это важно). Главная абстракция — **Crew**: команда AI-агентов с ролями (Researcher, Writer, Editor, Manager), целями, инструментами и памятью, которые сотрудничают над задачей.

С 2025 добавлены **Flows** — детерминированный event-driven слой над Crews для production. Получился паттерн **«deterministic backbone (Flow) + intelligence islands (Crew/Agent/LLM-call)»**.

**Текущее состояние (Q2 2026):**
- ~50K GitHub stars (по данным GitHub API на май 2026), 300 contributors, 186 релизов
- Версия 1.14 (апрель-май 2026)
- 500+ инструментов в маркетплейсе
- **Cognitive Memory v2** (март 2026): encode / consolidate / recall / extract / forget на базе LanceDB
- **Production-клиенты:** DocuSign (по утверждению CrewAI — 14× меньше кода против graph-based решения), Fortune 500 (~1.4B автоматизаций/мес по их же данным)
- Встроенный AI-ассистент в официальной документации, знающий актуальный API лучше, чем общие LLM

> **Уточнение по архитектурной независимости:** ядро CrewAI написано с собственными абстракциями Agent/Task/Crew/Flow и **не зависит от LangChain как библиотеки**. При этом в production его часто **интегрируют** с LangGraph (детерминированные шаги графа делает LangGraph, недетерминированные задачи внутри узла — CrewAI agent). Это interop, а не dependency.

---

## 2. Главное концептуальное различие

```
n8n               ───  workflow первичен, AI вторичен
                      │
                      ├─ Workflow → нода (HTTP) → нода (Slack) → AI Agent нода → нода (DB)
                      │
                      └─ Граф детерминирован. LLM решает только то, что в его узле.

CrewAI            ───  агент первичен, workflow вторичен (но с Flows — паритет)
                      │
                      ├─ Crew = [Researcher, Writer, Editor]
                      │   Каждый агент с goal/backstory/tools/memory.
                      │   Они общаются и делегируют через manager-agent.
                      │
                      └─ Flow оборачивает Crew в детерминированный backbone
                         (state, branching, persistence).
```

**Метафора:**
- **n8n** — это сборочный конвейер. Каждая станция (нода) делает понятную операцию. AI — это одна из станций.
- **CrewAI** — это виртуальный отдел. У каждого сотрудника-агента роль и обязанности. Они согласуют решения между собой.

---

## 3. Лицензии и open source — нюанс на $$$

### CrewAI — настоящий open source (MIT)

- **MIT License** на ядро фреймворка → можно использовать в коммерческих продуктах, перепродавать, встраивать, white-label без ограничений.
- Платная часть — **CrewAI AMP** (платформа поверх): visual builder, monitoring, SOC 2/HIPAA, managed deployment, observability. Платишь только если нужны эти фичи или enterprise-compliance.
- Self-host ядра — бесплатно навсегда, без license-сервера и без отчётности.

### n8n — НЕ open source, а fair-code

n8n часто называют open source, но юридически это **Sustainable Use License (SUL)** — fair-code модель, не OSI-approved. Различие важное:

**Что МОЖНО под SUL (бесплатно):**
- Внутренние бизнес-процессы своей компании (sync CRM ↔ БД, internal automations).
- Консалтинг: построить workflow клиенту за деньги, поддерживать его инфру.
- Установить n8n на сервер клиента (если они владеют им).
- Сделать ноду для своего продукта (интеграция своего SaaS с n8n).
- Продавать **результаты** workflow (отчёты, сообщения, действия).

**Что НЕЛЬЗЯ под SUL (требует commercial agreement n8n Embed):**
- White-label: переименовать n8n и продавать как свой продукт.
- n8n-as-a-Service: хостить n8n и брать с клиентов деньги за доступ.
- Дать клиентам прямой доступ к интерфейсу n8n, где они сами строят workflow.
- Встроить n8n в SaaS, где пользователи логинятся с **своими** credentials.

**Дополнительный слой:** Файлы с `.ee.` в имени в n8n репо — это **n8n Enterprise License** (проприетарная), не SUL. Включают часть продвинутых фич (advanced RBAC, log streaming, etc.) — нужен платный enterprise tier для использования в production.

**Практический вывод:** если ты строишь SaaS-продукт, где n8n — это движок, который видят твои пользователи — нужен платный embed-договор. Для internal automation, консалтинга, своего pipeline — всё бесплатно.

---

## 4. Pricing — где деньги уходят на самом деле

### n8n — ценообразование

**Community Edition (self-host):** бесплатно, без лимитов на workflows / executions / users. Под SUL — для internal/non-commercial.

**n8n Cloud (managed, EUR/мес при годовой оплате):**

| Тариф | Цена | Executions | Concurrent | Shared projects | AI Builder credits | Главное |
|---|---|---|---|---|---|---|
| **Starter** | €20 | 2,500/мес | 5 | 1 | 50 | Базовый, для solo |
| **Pro** | €50 | 10,000/мес | 20 | 3 | 150 | Admin roles, global vars, workflow history, execution search |
| **Business** | €667 | 40,000/мес | — | 6 | — | SSO/SAML/LDAP, Git version control, environments |
| **Enterprise** | custom | custom | 200+ | unlimited | 1,000 | Log streaming, dedicated SLA, external secret store |

**Особенности:**
- **1 execution = весь workflow целиком**, независимо от числа нод и времени. Шаги внутри не тарифицируются.
- Превышение квоты не останавливает workflow — но придёт overage-инвойс (~€4,000 за 300K экстра-executions на Business).
- Cost per execution: $0.008 (Starter) → $0.005 (Pro) → $0.000 (self-host).
- **Free trial** есть (14 дней), permanent free tier на Cloud — **нет**.
- C августа 2025 убрали лимит на active workflows — теперь unlimited на всех тарифах.

**Self-hosted Business / Enterprise** — license key, можно применять к unlimited инстансам (квота executions суммируется по всем).

### CrewAI — ценообразование

**Open Source ядро:** бесплатно (MIT), self-host где угодно. Платишь только LLM-провайдеру (OpenAI/Anthropic/Google/Ollama/любой LiteLLM-эндпоинт).

**CrewAI AMP (managed platform):**

| Тариф | Цена | Что включает | Для кого |
|---|---|---|---|
| **Basic** (free trial) | $0 | Visual editor, AI copilot, GitHub integration, **50 executions/мес** | Прототипирование |
| **CrewAI Cloud Pro (1K)** | **$29/мес** | 1,000 runs, hosted deployment, monitoring | Solo / very small SMB |
| **CrewAI Cloud Pro (5K)** | **$99/мес** | 5,000 runs, hosted deployment, monitoring/tracing | SMB production |
| **Enterprise (scale)** | tiered, custom | Больше runs, priority support, expanded observability | Mid-market |
| **Ultra (AMP Factory on-prem)** | **~$120,000/год** | On-prem или private VPC (AWS/Azure/GCP), Studio v2 visual builder, **SOC 2 / HIPAA**, dedicated CSM | Regulated enterprise |

> **Важно:** subscription исключает underlying compute (LLM API). Платишь провайдеру LLM (OpenAI/Anthropic/Google/Ollama) отдельно. На сложных crews с автономной коллаборацией LLM может быть основной cost-driver.

**Особенности:**
- LLM-стоимость — **отдельно** (платишь напрямую провайдеру). Это важно: при uncapped agent collaboration репортятся случаи $400+ за один run сложного crew.
- Self-host ядра — никаких license-серверов и отчётности.
- Enterprise features (observability, SOC 2/HIPAA) — только в AMP, в OSS их нет.

### Прямое сравнение стоимости production

| Сценарий | n8n | CrewAI |
|---|---|---|
| **Solo разработчик, MVP** | Self-host бесплатно или Cloud Starter €20/мес | OSS бесплатно + LLM API ($5-50/мес зависит от usage) |
| **Команда 5-10 человек, internal automations** | n8n Cloud Pro €50/мес | OSS + любой self-host + LLM API |
| **Production: 10K executions/мес** | n8n Pro €50/мес ($0.005/exec) | OSS бесплатно + ~$50-500/мес LLM (зависит от crew size) |
| **Production: 100K executions/мес** | n8n Business €667/мес → нужен Enterprise overage | OSS + $500-5000/мес LLM (контролируешь сам через rate-limits) |
| **Regulated (healthcare/fintech)** | n8n Enterprise (custom, обычно $XX,XXX/год) | CrewAI Ultra ~$120K/год или AMP Factory custom |

**Скрытый риск CrewAI:** при автономной коллаборации нескольких агентов с большими промптами счёт за LLM может превысить план в разы. Production-командам нужны cost-caps в коде или через `kickoff_async` + budget watchdog.

**Скрытый риск n8n:** при `Conversation Buffer Memory` без window-limit агент маршрутизатора на 500 запусков в день может накопить **$400/мес OpenAI** только из-за того, что вся история отправляется в каждый запрос (известный production-кейс). Лекарство — Window Buffer Memory с длиной 5-10 сообщений.

---

## 5. Архитектура и ключевые фичи

### n8n — ключевые сущности

| Сущность | Что |
|---|---|
| **Workflow** | DAG из нод. Триггер → operations → AI Agent (если нужен) → action нодa. |
| **Trigger nodes** | Webhook, Schedule (cron), Chat, App-specific events (Gmail, GitHub PR, etc.) |
| **AI Agent node** | LangChain.js под капотом. Соединяется с Chat Model + Tools + Memory + System Prompt. |
| **Tools** | Native nodes (Slack, Gmail, ...), HTTP Request, MCP Client Tool, кастомные ноды JS/Python. |
| **Memory** | Window Buffer / Conversation Buffer / Postgres Chat / Redis Chat / Vector Store / Simple. |
| **Code node** | JS или Python для произвольной логики. |
| **Data Tables** (Q1 2026) | Встроенная БД в n8n без подключения PostgreSQL извне для простых таблиц. |
| **Evaluations + Guard Rails** (Q1 2026) | LLM-as-judge паттерн встроен, production-grade safety (защита от prompt injection / jailbreak). |
| **HITL gating** (Q1 2026) | AI tool не выполняется без явного human approval. Реализовано через ноду Wait с таймаутом. |
| **MCP Server node** (n8n 2.0, декабрь 2025) | n8n стал не только consumer, но и **provider** MCP-инструментов («MCP Server Trigger»). |
| **AI Workflow Builder** (beta, начало 2026) | Генерация схемы workflow из текстового описания (промпт до 1000 символов). |
| **Chat node v2 + End-user role** | Встроенный чат-интерфейс с ролью end-user (доступ только к чату), позволяет white-label чат на платном тарифе. |

### CrewAI — ключевые сущности

| Сущность | Что |
|---|---|
| **Agent** | Роль + goal + backstory + tools + LLM + (опционально) memory. |
| **Task** | Одна работа для агента. Имеет description, expected_output, опциональные guardrails и context. |
| **Crew** | Команда агентов + список задач + process (sequential / hierarchical / consensual). |
| **Flow** | Детерминированный event-driven workflow с `@start`, `@listen`, `@router`, `and_()`, `or_()`. State через Pydantic. |
| **Process types** | `sequential` (одна за другой), `hierarchical` (auto manager-агент делегирует), `consensual` (все агенты голосуют). |
| **Memory** (v2, март 2026) | Unified `Memory` класс: encode / consolidate / recall / extract / forget. Composite scoring (semantic + recency + importance). LanceDB backend. |
| **Task Guardrails** | Валидация output задачи перед передачей дальше. |
| **Structured Outputs** | `output_pydantic` / `output_json` — type-safe передача данных между задачами. |
| **LLM Hooks** | Inspect/modify messages перед/после LLM. |
| **@persist decorator** | Сохраняет state Flow в БД, переживает рестарты. |

### Side-by-side: production-критичные фичи

| Фича | n8n | CrewAI |
|---|---|---|
| **Визуальный builder** | Да, основа продукта (бесплатно) | Только в AMP (платно). OSS — код. |
| **Pre-built интеграции** | 400+ нативных, 5,300+ community | ~500 tools в marketplace |
| **Custom code в workflow** | JS + Python в Code node | Python везде — это сам framework |
| **Multi-agent native** | Через цепочку AI Agent нод (workaround) | **Нативно**: Crew = команда агентов |
| **Memory типы** | 6 встроенных (Window, Conv Buffer, Postgres, Redis, Vector, Simple) | Unified Memory с adaptive recall (deep/shallow) |
| **State management** | Workflow variables + Postgres ноды | Pydantic FlowState + @persist + LanceDB |
| **HITL** | Wait node + Chat node v2 (Q1 2026) | `requires_human_review` flag в Flow listeners |
| **MCP support** | **Mature, bi-directional**: host (consumer) + server (provider) — n8n 2.0 декабрь 2025 | **Native via `mcps` field** на агентах: Stdio + SSE + Streamable HTTP transport, auto tool-discovery, name-collision префиксы |
| **Observability** | Execution history (7-365 дней в зависимости от тарифа) | OSS: print/log; AMP: real-time tracing, OTel |
| **Scheduling** | Cron-нода встроена | Нужен внешний оркестратор (n8n / cron / k8s CronJob) |
| **Webhook trigger** | Встроен в Webhook node | Через FastAPI / Flask wrap-around |
| **Database access** | Native ноды для всех major DBs | Любая Python lib для БД |
| **RAG components** | Через интеграции (manual setup) | Custom Python (любой vector DB client) |
| **Тестирование** | Manual execution в UI + Evaluations ноды (Q1 2026) | pytest + structured outputs (type-safe) |
| **Version control** | Workflow в JSON (Git-diff messy), Git nodes в Enterprise tier | Native Git — это просто Python код |
| **CI/CD** | Через n8n CLI + license key, медленно | Стандартный Python CI (pytest, mypy) |

---

## 6. Когда что выбирать — практическая матрица

### ✅ Выбирай **n8n**, если:

- **Главная задача — интегрировать сервисы**, AI как один из шагов (не центр).
- В команде есть **не-разработчики**, которые должны читать/менять workflow.
- Нужны **400+ готовых интеграций** out of the box.
- Хочешь **визуальный debugging** — пройтись по нодам, посмотреть data flow.
- Self-host **обязателен** для data sovereignty (CE бесплатно).
- Используешь много **scheduled jobs** (cron-триггеры).
- Делаешь **MVP за дни**, не недели.
- Workflow в основном **детерминированный**, AI — для одного-двух классификаций/генераций.

### ✅ Выбирай **CrewAI**, если:

- Задача **естественно декомпозируется в роли** (researcher → analyst → writer → editor).
- Нужно **multi-agent reasoning**: агенты обмениваются результатами, делегируют, валидируют друг друга.
- Команда — **Python developers**, готовы поддерживать code-base.
- Нужны **type-safe outputs** между шагами (Pydantic structured outputs).
- Хочешь **agent-as-team** метафору в коде, понятную не-инженерам в read-only.
- Production требует **строгий CI / pytest / mypy**.
- Workflow содержит **сложное reasoning** (исследование, генерация контента, code review).
- Нужна **persistent memory** между запусками (LanceDB + Cognitive Memory v2).

### ❌ НЕ бери **n8n**, если:

- Workflow содержит **>4-5 инструментов в одном агенте** — отладка ломается.
- Нужны **3+ уровня вложенности** sub-workflow — невозможно отлаживать.
- System prompt уходит за **2000+ слов** — пора декомпозировать в код.
- Нужен **sub-second latency** — event loop n8n блокирует на длинных tool-вызовах.
- B2B SaaS с **тысячами одновременных пользователей**.
- Нужны **регрессионные тесты в CI** — canvas нельзя `pytest`-нуть.
- Hard compliance: **healthcare/finance** с deterministic execution + immutable audit logs (LangGraph выигрывает).
- Нужно **white-label или SaaS-resell** n8n (юридический блок, нужен n8n Embed).

### ❌ НЕ бери **CrewAI**, если:

- **Один LLM-вызов** решает задачу — multi-agent оверкилл.
- Нужна **строгая предсказуемость cost** — uncapped agent collaboration может стоить $400+.
- Команда не пишет на Python (JS/TS — посмотри Mastra или Vercel AI SDK).
- Workflow содержит **сложные cycles и intricate state transitions** — LangGraph даёт больше контроля.
- Дебаг через **print/log** критичен — в CrewAI он работает плохо, нужно AMP observability.
- Нужны **400+ готовых интеграций** (CrewAI — это framework, не connectorhub).

---

## 7. Гибридный паттерн «Brain and Glue» — использовать оба

В индустрии за этим паттерном закрепилось название **«Brain and Glue»**:
- **n8n = Glue** — управляет триггерами, SaaS credentials через vault, human-in-the-loop approvals, error retry, delivery. Эта часть меняется часто, потому что меняются бизнес-правила.
- **CrewAI = Brain** — multi-agent reasoning, role-based decomposition, structured output. Эта часть меняется реже, но требует Python-разработчиков.

Самый частый production-паттерн от практиков:

```
┌─────────────────────────────────────────────────────────────┐
│                        n8n                                  │
│  (orchestration layer)                                      │
│                                                             │
│  Trigger → fetch data → preprocess → ┐                      │
│                                       │                     │
│                                       ▼                     │
│                                  HTTP Request               │
│                                       │                     │
│                                       ▼                     │
│                          ┌─────────────────────┐            │
│                          │   CrewAI service    │            │
│                          │   (FastAPI wrap)    │            │
│                          │                     │            │
│                          │  Crew {             │            │
│                          │    Researcher,      │            │
│                          │    Analyst,         │            │
│                          │    Writer           │            │
│                          │  }                  │            │
│                          └─────────────────────┘            │
│                                       │                     │
│                                       ▼                     │
│  ◄── deliver result → save → notify ┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Почему так:**
- **n8n** — отлично делает «plumbing»: триггеры, расписания, интеграции, error-handling, retries, delivery.
- **CrewAI** — отлично делает «thinking»: multi-agent reasoning, role-based decomposition.
- Граница чистая: n8n вызывает CrewAI-сервис через HTTP/webhook и обрабатывает результат как обычные данные.

**Когда оправдано:**
- Нужна **интеллектуальная** часть задачи (research, content generation, multi-step reasoning) + **операционная** часть (расписание, delivery, integrations).
- Не хочешь переписывать всю операционку под Python.
- Команда смешанная: ops-инженеры тянут n8n, AI-инженеры тянут CrewAI.

**Цитата практика (Nicholas Puru, AI automation builder):**
> *«N8N is still our orchestration layer and Claude Code is increasingly our build layer. This hybrid is really what works».*

Этот паттерн воспроизводится и для других связок: «n8n как платформа интеграции, не как конструктор workflow; код становится основным инструментом».

**Альтернативный паттерн «начни с n8n, мигрируй части в код»:**
1. MVP в n8n за неделю-две.
2. Когда конкретный workflow упирается в потолок (>5 tools, плохая отладка, system prompt 2000+ слов, 3+ уровня вложенности) — выносим **только эту часть** в CrewAI / LangGraph / Pydantic AI.
3. n8n остаётся как операционный слой.

**Полуавтоматический процесс миграции (community-validated, покрывает ~85% работы):**

1. Экспортировать workflow из n8n в JSON.
2. Передать JSON + документацию целевого фреймворка (Mastra / Pydantic AI / LangChain / CrewAI) кодинг-агенту типа Claude Code.
3. Оставшиеся ~15% (сложная бизнес-логика, специфика RAG, кастомные tool-вызовы) — ручная доработка.

**Альтернативные hybrid-оркестраторы:**
- **Archon** (open-source) — позиционируется как «n8n для AI-кодинга»: оборачивает кодовые фреймворки в визуальные workflow.
- **LangGraph + CrewAI** — LangGraph для детерминированных шагов графа, CrewAI вызывается внутри узлов как агент-оркестратор для недетерминированных задач.

**Twin-loop interop (обратное направление):** мало кто это делает осознанно, но это мощный паттерн — **n8n workflow экспортируется как MCP-сервер**, и тогда **CrewAI агент вызывает его как обычный tool**. Получается двусторонняя связка: CrewAI может делегировать «glue»-операции (data fetch, SaaS-вызовы, форматирование) в n8n как в инструмент, а не только наоборот.

**Конкретная метрика MCP-выигрыша:** время интеграции нового SaaS-инструмента **снижается с ~18 часов (traditional function calling — написать wrapper, схему, обработку ошибок) до ~4.2 часов (MCP server подключается декларативно)**. Это аргумент для production-команд переключаться на MCP-first архитектуру при integration-heavy workloads.

---

## 8. Production-метрики и реальные кейсы

### Точные цифры по latency / accuracy / cost

Bitext-исследование на customer-support routing (26K сообщений), 2026:

| Подход | Accuracy | Cost / запрос | Latency |
|---|---|---|---|
| Keyword routing (без AI) | 68.6% | $0 | <5ms |
| Single LLM (native API call) | 87.6% | $0.000074 | ~800ms |
| Pydantic AI | 86.4% | $0.000079 | ~850ms |
| **LangGraph** | 84.4% | $0.000089 | ~1.2s |
| **CrewAI** | **88.4%** | $0.000171 | ~2.5s |

> 💡 **Insight:** CrewAI даёт самую высокую точность, но в **2× дороже** и в **2× медленнее** одиночного LLM. На 69% запросов достаточно keyword-routing вообще без AI. **Tier-cascade architecture** (keyword → LLM → multi-agent) экономит и cost, и latency.

### Кейсы по n8n

| Кейс | Stack | Результат |
|---|---|---|
| **Vodafone** | Self-hosted n8n + threat intelligence workflows | £2.2M экономии |
| **Delivery Hero, DPD, Wayfair** | Self-hosted n8n | Масштабный AI-deployment |
| **n8n + Flowise pipeline документации** | n8n для file ingest + delivery, Flowise для RAG | Production-stack без code-framework |

### Кейсы по CrewAI

| Кейс | Stack | Результат |
|---|---|---|
| **DocuSign** | CrewAI Flows + Crews | **14× меньше кода** vs прежнее graph-based решение; та же архитектура переиспользована для разных use-cases |
| **CrewAI customers (claim)** | CrewAI AMP в Fortune 500 | ~1.4B автоматизаций/мес по их данным |
| **Cognitive Memory v2** (март 2026) | Сам CrewAI dogfood'ит свой memory system на Flows | Self-organizing hierarchy + adaptive depth recall |

---

## 9. Антипаттерны и реальные production-боли

### Антипаттерны n8n

- **Conversation Buffer Memory без window-limit** — на 500 запусков/день агент маршрутизатора накопил $400/мес счёт OpenAI просто потому что вся история улетает в каждый запрос. → **Лекарство:** Window Buffer Memory length 5-10.
- **n8n issue #12958** — настройка Context Window Length в Postgres Chat Memory **не уважается** частью узлов. В логах OpenAI улетает не последние N сообщений, а вся таблица истории. Latency 4с → 1 мин, счёт растёт. → **Лекарство:** проверяй реальный ввод в LLM через execution logs, не доверяй декларативным настройкам в UI.
- **Кастомный MCP-сервер вокруг сервиса, у которого уже есть нативная нода** — медленнее, тяжелее в отладке, никакого выигрыша. → **Лекарство:** правило **нода > HTTP > MCP**.
- **6+ инструментов в одном AI Agent** — выбор начинает галлюцинировать. → **Лекарство:** Tool Isolation (разделить агента на нескольких специализированных).
- **Visual canvas → spaghetti** при 30+ нод в одном workflow. → **Лекарство:** sub-workflows, но не глубже 2 уровней.
- **Simple Memory (Window Buffer in-memory) в production** — под капотом SQLite, который под нагрузкой «отмирает и отваливается». → **Лекарство:** Postgres Chat / Redis Chat для production. Simple Memory — только dev/notebook.
- **Cron-loops без watchdog** — агент, который проверяет «наступило ли утро» каждые 30 минут, может сжигать $80/день токенов. Накопленные неотработанные задачи кронов сжигают 5-часовой OpenAI rate-limit за полчаса. → **Лекарство:** rate-limiter + явный budget guard перед AI Agent нодой.
- **Отладка цепочки агентов:** если в workflow последовательно стоят 2+ AI Agent ноды, n8n отображает логи только последнего. Промежуточные шаги — слепая зона. → **Лекарство:** Set / Log ноды между агентами для явного снимка state, либо вынос multi-step reasoning в код.

### Антипаттерны CrewAI

- **Putting everything in agents when some of it should be code** — нельзя нормально отлаживать, costs spiral, behavior непредсказуем. → **Лекарство:** deterministic backbone (Flow) + intelligence islands (Crew/Agent/LLM-call).
- **Squeezing too much into one agent** — context windows blow up, too many tools confuse it, hallucinations increase. → **Лекарство:** разделить на специализированных агентов с фокусированными tool-наборами.
- **Hierarchical process без guard-rails** — manager-агент делегирует на основе LLM-решений, может уйти в loop или плохую координацию. → **Лекарство:** Flows с явным state + Task Guardrails.
- **Debugging through print/log** — в CrewAI работает плохо (агенты пишут параллельно, логи перемешиваются). → **Лекарство:** `flow.plot()` для визуализации + structured JSON logging с per-task IDs + CrewAI AMP tracing для production.
- **Tool calls не всегда логируются в внешний tracing (LangFuse, etc.)** — отображаются агенты и POST-запросы, но **не вызовы функций** на стороне tool. → **Лекарство:** ручная обёртка над инструментами с явным логированием перед/после вызова.
- **Uncapped autonomous runs** — репортятся случаи $400+ за один run сложного crew. → **Лекарство:** `kickoff_async` + budget watchdog в коде + `max_iterations` на агенте + `task.timeout` + per-agent token-budget каскад.
- **Автономный агент без cost-cap может «сжечь годовой бюджет на токены за ночь»** — общая боль multi-agent систем с открытым делегированием. → **Лекарство:** обязательный hard-cap на cost/токены + circuit breaker на единичную задачу.
- **Unhandled invalid router branches в Flows** — если в `@router` нет explicit handler для `invalid` state (например, validator вернул `confidence < threshold`), Flow падает молча или зависает в неопределённом состоянии. → **Лекарство:** для каждого `@router` всегда писать явный `@listen("invalid")` handler с logging + fallback.
- **Synchronous `kickoff()` bottleneck** — на множественных независимых items (1000 leads, 500 документов) последовательный `kickoff()` блокирует, теряется параллельность. → **Лекарство:** `kickoff_async()` + `asyncio.gather` для throughput. Это не только budget watchdog, но и базовый production-паттерн для batch-обработки.

---

## 10. Что выучить сначала — путь обучения

### Если идёшь по n8n:

1. **Анатомия AI Agent ноды** (Chat Model + Tools + Memory + System Prompt) — без любого из этих 4-х компонентов нет рабочего агента.
2. **Правило интеграции:** native node > HTTP Request > MCP Client Tool (см. `best-practices.md`).
3. **Algorithm-before-AI:** детерминированные guards до и после LLM (см. `algorithm-before-ai.md`).
4. **Memory types:** Window Buffer как default, остальные — по конкретным сценариям (см. `memory-types-in-n8n.md`).
5. **GCAO в System Prompt** (см. `prompts/gcao-templates.md`).
6. **Evaluations + Guard Rails ноды** (production-safety, Q1 2026).

### Если идёшь по CrewAI:

1. **Agent + Task + Crew** — minimal viable crew за 25 минут.
2. **Process types:** `sequential` (90% случаев) → `hierarchical` (когда нужен auto-manager).
3. **Flows + State** — обязательно для production. Никогда не деплой чистый Crew.
4. **Structured Outputs (Pydantic)** — type-safe передача между task'ами.
5. **Task Guardrails + LLM Hooks** — production-grade quality control.
6. **Memory v2** — when и как использовать `remember`/`recall`/`extract`.
7. **`@persist` decorator** — для long-running flows с возможностью восстановления.
8. **Cost watchdog** — обязательно перед production.

---

## 11. Чек-лист принятия решения (за 60 секунд)

Ответь на 6 вопросов:

1. **Главная сложность задачи — в интеграции с N сервисами или в reasoning?**
   - Интеграция → **n8n**.
   - Reasoning → **CrewAI**.
2. **Команда — Python developers или смешанная (включая не-инженеров)?**
   - Только Python devs → **CrewAI** опция открыта.
   - Смешанная → **n8n** (визуальный builder понятен ops-у и PM-у).
3. **Нужно multi-agent collaboration (несколько ролей, делегирование)?**
   - Да → **CrewAI**.
   - Нет, достаточно одного агента → **n8n** проще.
4. **Critical: cost predictability на scale?**
   - Yes → **n8n** (executions предсказуемо тарифицируются) или **CrewAI с явными budget caps**.
5. **Compliance (SOC2/HIPAA/SOC1) обязателен?**
   - Yes → **n8n Enterprise** или **CrewAI Ultra / AMP Factory** (за деньги).
   - Нет → OSS-вариант любого.
6. **Готовы держать Python codebase в production (CI, тесты, deps)?**
   - Yes → **CrewAI** в полном объёме.
   - No → **n8n** с минимальным JS в Code-нодах.

**Если всё ещё непонятно:** начни с **n8n** для всей операционки, добавь **CrewAI** для конкретного reasoning-блока через HTTP-вызов. Это самый безопасный starting point — не нужно сразу выбирать «либо-либо».

---

## 12. Community consensus и где он разваливается

Community-консенсус по выбору **сходится** в следующих пунктах:

1. **n8n — для API-интеграций и жёсткой бизнес-логики**, code-фреймворки (CrewAI, LangGraph, Pydantic AI) — для сложного AI. Это разные слои, не конкуренты.
2. **MVP-паттерн «n8n first, then code»**: «N8N = MVP: заработало → переписываем на Python. Стек AI-разработчика: Python + агенты + БД + FastAPI».
3. **CrewAI для быстрой проверки гипотез**, LangGraph — для жёсткой детализации workflow.
4. **«Pydantic AI иногда за 20 минут решает то, что в n8n требует 2 дня»** — общий тезис у нескольких независимых практиков (для сложных multi-agent сценариев).

**Где консенсус разваливается:**

- **«n8n не масштабируется в production»** vs **«n8n — зрелый Enterprise backend, его юзают Vodafone и Microsoft с 3000+ корпоративных клиентов»**. Раскол по аудитории: технический хардкор (data engineers) против AI-automation builders.
- **«В n8n всё как на ладони, апишка заменяется за полчаса»** (защитники visual UX) vs **«нет breakpoints, нет step-by-step debugging, multi-agent — неотлаживаемая система»** (противники).
- **«CrewAI — игрушка для прототипов»** vs **«DocuSign написал production-систему на Crews+Flows с 14× меньше кода»**. Раскол по уровню зрелости фреймворка и опыту команды.

Практическое следствие: если в твоей команде кто-то категорично «за» или «против» одного из инструментов — почти наверняка он рассуждает из своего контекста (стек, размер команды, тип задач). **Проверь применимость к твоему**, не цитируй мнение как универсальное.

---

## 13. Learning ecosystem — где учиться обоим

### n8n

- **Официальная документация** (docs.n8n.io) — qualitative, регулярно обновляется.
- **Community forum** (community.n8n.io) — активный, быстрые ответы по licensing/lifecycle вопросам.
- **n8nworkflows.xyz** — community-каталог из 4,000+ готовых автоматизаций.
- **YouTube creators**: David Ondrej, Leon van Zyl, Nate Herk — самые видимые англоязычные эксперты с растущим контентом 2025-2026.
- **Marketplace** на n8n.io/templates — 6,000+ официальных шаблонов.
- **n8n changelog** (Mintlify) — обязательно подписаться, релизы каждые 1-2 недели с production-фичами.

### CrewAI

- **Официальная документация** (docs.crewai.com) — содержит встроенный AI-ассистент, который знает актуальный API лучше общих LLM. Полезно для troubleshooting.
- **CrewAI blog** (blog.crewai.com) — обновляется ~1-2 раза в месяц, разбирает архитектурные решения (Cognitive Memory v2, Production Architecture).
- **learn.crewai.com** — 100K+ зарегистрированных разработчиков по их же данным.
- **GitHub Discussions** + Discord (точный размер сообщества варьируется в источниках).
- **Tools marketplace** — 500+ инструментов на момент апреля 2026.

### Общая литература по AI-агентам (применима к обоим)

- **«Best AI Agent Frameworks 2026»** (Agent Whispers) — независимый годовой обзор с примерами кода.
- **n8n blog: «AI Agent Orchestration Frameworks»** — n8n-нативный, но с честным разбором конкурентов.
- **CrewAI blog: «How we built Cognitive Memory»** — глубокое погружение в архитектуру agentic memory.

---

## 14. Production-метрики и enterprise-кейсы 2026

Свежие данные из независимых аналитических обзоров мая 2026.

### Adoption-контекст

- **Gartner 2026:** 61% крупных предприятий используют ≥1 production AI agent system (vs 18% в 2024). Тренд экспоненциальный.
- **Governance как Strategic Priority:** 74% организаций ставят governance во главу AI-стратегии (а не «потом разберёмся»).
- **Self-host break-even point для n8n:** ~20,000 executions/мес. Ниже — Cloud выгоднее (managed convenience). Выше — self-hosted (VPS или Mac mini амортизация ~$60/мес vs Cloud overage €4,000/300K).

### Production-кейсы CrewAI

**DocuSign — Sales Pipeline Acceleration**
- **Архитектура:** 5 специализированных агентов (Identifier, Researcher, Composer, Validator, Orchestrator) в Flow-обёртке.
- **Валидация:** 3 слоя — LLM-as-judge для стиля, hallucination-check против исходных контрактов, API-based quality scoring.
- **Метрики:**
  - **29%** reduction в contracting-related deal delays
  - **1-2%** annual revenue uplift ≈ **$4.8M** на их renewal volume

**CrewAI Cloud aggregate (data из «Lessons from 2 Billion Agentic Workflows», CrewAI blog):**
- 2 миллиарда+ agentic workflows прошло через CrewAI в 2025.
- **Success Rate Gap (важно для production):** на сложных задачах **8+ steps** CrewAI показывает ~**54% success rate** vs **62% у LangGraph**. На 10,000 complex tasks/мес это **+800 retries** на CrewAI → дополнительные compute costs + token consumption.

### Production-кейсы n8n

**Vodafone — Operational Efficiency at Scale**
- **Реализация:** **33 mission-critical workflows** между десятками внутренних SaaS-платформ.
- **Метрика:** **~5,000 person-days/year saved** (это альтернативная метрика к ранее упомянутому £2.2M — обе из официального case study).

**Delivery Hero — High-Volume IT Automation (53K employees)**
- **Проблема:** 800 account-recovery requests/мес × **35 минут** на запрос = много IT-ресурса.
- **Решение:** один n8n workflow с автоматическими API-вызовами в Okta + Jira + Google Workspace, manager approval вместо ticketing.
- **Метрика:** lockout time **35 → 20 мин**, **>200 часов/мес сэкономлено** IT-команде. Pattern переиспользован для offboarding и license assignment.

### MCP — стандарт, который меняет landscape

К середине 2026 **MCP стал de facto USB-C для агентов**: количество интеграций редуцировалось с M models × N tools (cartesian product) до M + N (linear). И n8n, и CrewAI имеют native MCP support, что упрощает их interop и hybrid-паттерны.

- **n8n** — bi-directional: и host (вызывает MCP-инструменты), и server (n8n workflow → MCP-tool для внешних агентов). Через дедицированные ноды.
- **CrewAI** — через `mcps` field на агентах. Auto tool-discovery, transport Stdio/SSE/Streamable HTTP, авто-префиксы для предотвращения name-collisions.

### Дополнительный антипаттерн — Shadow AI Proliferation

Помимо ранее перечисленных, в 2026 эксперты выделяют отдельную угрозу:

> **Shadow AI Proliferation в n8n.** Из-за low-code природы бизнес-юниты могут разворачивать AI-агентов в обход IT governance. Это создаёт **data sovereignty risks** (GDPR, HIPAA, 152-ФЗ) — потому что workflow со чувствительными данными может незаметно для compliance-команды отправлять их в third-party LLM API.

**Лекарство:** централизованный self-host n8n + RBAC + audit logging + явная политика «новый workflow с PII требует security review».

---

## 15. Резюме одной таблицей

| Критерий | Победитель | Комментарий |
|---|---|---|
| Скорость старта (visual) | **n8n** | Drag-and-drop, MVP за час |
| Скорость старта (code, multi-agent) | **CrewAI** | YAML + Python, MVP за 25 мин |
| Multi-agent reasoning | **CrewAI** | Это его core feature |
| Pre-built интеграции | **n8n** | 400+ нативных, 5,300+ community |
| Self-host бесплатно | **Tie** | Оба бесплатны для internal/non-resell use |
| Open source чистота | **CrewAI** | MIT vs n8n fair-code SUL |
| Production cost predictability | **n8n** | Executions-based pricing, executions = 1 запуск |
| Visual debugging | **n8n** | UI execution history по дефолту |
| Программное debugging | **CrewAI** | Python stack traces, `flow.plot()`, structured logs |
| MCP-зрелость | **n8n** | Client + server в Q1 2026 |
| Type safety | **CrewAI** | Pydantic structured outputs |
| Compliance enterprise | **Both paid tiers** | n8n Enterprise или CrewAI Ultra/AMP Factory |
| Total cost ownership (low-volume) | **n8n self-host** | CE бесплатно, ноль LLM-overhead на orchestration |
| Total cost ownership (high reasoning) | **CrewAI OSS** | Платишь только за LLM, инфра self-host |

---

## Источники

Distilled из публичных источников Q1-Q2 2026:

**Официальные:**
- n8n: документация (docs.n8n.io), n8n blog (Series C announcement октябрь 2025, pricing changes август 2025), n8n changelog 2.0-2.9.x, n8n GitHub repo (n8n-io/n8n), n8n.io/pricing, Sustainable Use License docs.
- CrewAI: документация (docs.crewai.com), CrewAI blog (Cognitive Memory v2 март 2026, Agentic Systems декабрь 2025, Production Architecture), CrewAI GitHub repo (crewAIInc/crewAI), crewai.com/pricing, crewai.com/opensource.

**Независимые сравнения и аналитика:**
- pikagent.com (CrewAI vs n8n comparison), integrationinsider.com (CrewAI vs Langflow vs n8n), agentforeverything.com, Agent Whispers (Best AI Agent Frameworks 2026), Medium посты по hybrid pattern, peerspot.com.
- Vadim's blog (CrewAI Unique Features deep-dive), Jahanzaib AI (CrewAI Flows Production Guide), CallSphere (Flows vs Crews 2026), Interconnected (CrewAI 2026 Guide).
- Ascendient Learning (Zapier/n8n/CrewAI rise), openhosst.com (n8n Cloud pricing breakdown).

**Production-метрики и кейсы:**
- Bitext 26K dataset customer support routing study (accuracy/cost/latency per framework).
- DocuSign CrewAI Flows case (по утверждению CrewAI — 14× меньше кода против graph-based).
- Vodafone case study на n8n.io (£2.2M savings — note: метрика взята с официального сайта n8n, не cross-confirmed в community-источниках).
- Self-hosted n8n cases: Delivery Hero, DPD, Microsoft.

**Cross-confirmation:**
- Внутренний документ курса `lesson5/prepared-materials/kb-examples-frameworks-landscape.md` (askaizer RAG над KB ~35K items, scores 0.820-0.950 для ключевых утверждений).
- NotebookLM rolling notebook «Everything about AI ...» (18 sources, май 2026) — cross-check метрик n8n/CrewAI, антипаттернов, community consensus.
- Свежий NotebookLM Deep Research notebook «CrewAI vs n8n — детальное сравнение M5» (создан май 2026, 45 sources).

**Ключевые URL из Deep Research (для самостоятельного чтения):**
- Production-метрики и benchmarks: [pooya.blog CrewAI vs LangGraph vs AutoGen 2026](https://pooya.blog/blog/crewai-vs-langgraph-autogen-comparison-2026/), [zenml.io CrewAI vs n8n](https://www.zenml.io/blog/crewai-vs-n8n), [47billion.com AI Agents in Production](https://47billion.com/blog/ai-agents-in-production-frameworks-protocols-and-what-actually-works-in-2026/), [madappgang.com AI Agent Framework decision guide](https://madappgang.com/blog/ai-agent-framework-decision-guide-2026/).
- Кейсы: [n8n.io/case-studies/delivery-hero](https://n8n.io/case-studies/delivery-hero/), [blog.crewai.com/lessons-from-2-billion-agentic-workflows](https://blog.crewai.com/lessons-from-2-billion-agentic-workflows/), [docusign.com capitalizing-on-AI-deloitte-2026](https://www.docusign.com/blog/capitalizing-on-AI-deloitte-2026).
- Pricing deep-dive: [zeabur.com n8n Pricing Guide](https://zeabur.com/blogs/n8n-pricing-shift-self-hosting-business-costs-zeabur-guide), [finbyz.tech Self-Hosting n8n Enterprise Guide](https://finbyz.tech/n8n/insights/self-hosting-n8n-enterprise-guide), [connectsafely.ai n8n Pricing 2026](https://connectsafely.ai/articles/n8n-cloud-pricing-guide).
- Архитектура: [jahanzaib.ai CrewAI Flows Production Guide](https://www.jahanzaib.ai/blog/crewai-flows-production-multi-agent-guide), [docs.crewai.com/en/mcp/overview](https://docs.crewai.com/en/mcp/overview), [docs.crewai.com/en/concepts/agent-capabilities](https://docs.crewai.com/en/concepts/agent-capabilities), [blog.n8n.io AI Agent Architecture Patterns](https://blog.n8n.io/ai-agent-architecture-patterns/).
- MCP стандарт: [digitalapplied.com MCP vs LangChain vs CrewAI](https://www.digitalapplied.com/blog/mcp-vs-langchain-vs-crewai-agent-framework-comparison), [workos.com MCP in 2026](https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026).

**Note:** разбросы в точных цифрах (GitHub stars n8n: 172K vs 184K; CrewAI: 23.5K-50K в разных источниках) объясняются датой съёма метрики и тем, считать ли total stars n8n-io org или только основной репозиторий. Для production-решений эти разбросы не критичны — порядок величины одинаков во всех источниках.

---

*Гайд М5 — HSS AI-dev L1. Living document — обновляется при значимых релизах фреймворков.*
