# Report

## Primary IDE
VS Code + Claude Code (CLI)

## Local Launch Confirmation
Запустил локально через Docker MongoDB + npm run dev (Node v16, backend :5001, frontend :3000).

## Rules Diff

Что добавлено вручную поверх auto-generated CLAUDE.md:

- **Environment Setup Gotchas** — автоген не мог знать, что на macOS порт 5000 занят AirPlay Receiver, что npm cache ломается правами доступа, и что node_modules нужно удалять после смены версии Node через nvm. Всё это выяснилось в процессе запуска проекта.

- **Deployment / Infrastructure Notes** — автоген увидел Procfile, но не мог infer, что проект привязан к Heroku и что react-scripts 3.4.3 намертво привязан к webpack 4, что делает апгрейд нетривиальной задачей.

- **When Adding New Backend Features** — автоген не мог знать конвенцию о том, что при добавлении новой модели нужно обновить seeder.js, что auth middleware подключается вручную к каждому роуту, и что новые Redux-слайсы требуют регистрации в combineReducers + localStorage.

- **Node.js v16 constraint** — автоген увидел package.json, но не мог узнать из кода, что Node v25 ломает и backend (buffer-equal-constant-time), и frontend (webpack 4 crypto hash). Это выяснилось только при запуске.

- **Port sync requirement** — автоген не мог вывести связь между PORT в .env и proxy в frontend/package.json. Это неочевидная зависимость, которую легко сломать, меняя только одно значение.

- **Team Conventions** — правила работы с git и PR (именование веток, scope-префиксы, чеклист перед PR). Автоген не имеет доступа к командным процессам.

- **Local Gotchas** — react-router-dom v5 vs v6, порядок роутов в Express, vendored bootstrap.min.css. Автоген не может отличить "работает" от "работает случайно из-за порядка регистрации".

- **AI Collaboration Preferences** — язык объяснений (русский), запрет на рефакторинг вне задачи, требование списка затронутых файлов до написания кода. Это личные предпочтения, которые невозможно вывести из кода.

## M3

### Feature Flags MCP

**IDE:** Claude Code (CLI)
**MCP-сервер:** `mcp-feature-flags/server.py` (Python FastMCP)
**Конфиг:** `.mcp.json` в корне репо

#### Тестовый сценарий — search_v2

**Промпт:** Проверь состояние фичи search_v2. Если она в статусе Disabled — переведи в Testing. Установи трафик на 25%. Подтверди финальное состояние.

**Шаг 1 — `get_feature_info(feature_name="search_v2")`**

```
→ Ответ MCP:
{
  "feature_id": "search_v2",
  "name": "New Search Algorithm",
  "description": "Replaces legacy regex-based keyword matching with a hybrid BM25 + TF-IDF ranking pipeline. Improves relevance for multi-word queries and handles common misspellings via fuzzy matching. Backend: new productController search path; index built on name, brand, category, description fields.",
  "status": "Testing",
  "traffic_percentage": 25,
  "last_modified": "2026-05-04",
  "targeted_segments": ["beta_users", "internal"],
  "rollout_strategy": "canary"
}
```

Фича уже в статусе **Testing** с traffic_percentage=25%. Перевод из Disabled не потребовался (статус уже Testing). Тем не менее выполнен явный вызов `adjust_traffic_rollout` для подтверждения значения 25%.

**Шаг 2 — `adjust_traffic_rollout(feature_name="search_v2", percentage=25)`**

```
→ Ответ MCP:
{
  "feature_id": "search_v2",
  "name": "New Search Algorithm",
  "status": "Testing",
  "traffic_percentage": 25,
  "last_modified": "2026-05-04",
  "hint": null
}
```

Трафик подтверждён на уровне 25%. `hint: null` — не 0% (иначе подсказка предложила бы Disabled) и не 100% (иначе подсказка предложила бы Enabled).

**Шаг 3 — `get_feature_info(feature_name="search_v2")` — финальное подтверждение**

```
→ Ответ MCP:
{
  "feature_id": "search_v2",
  "name": "New Search Algorithm",
  "description": "Replaces legacy regex-based keyword matching with a hybrid BM25 + TF-IDF ranking pipeline. Improves relevance for multi-word queries and handles common misspellings via fuzzy matching. Backend: new productController search path; index built on name, brand, category, description fields.",
  "status": "Testing",
  "traffic_percentage": 25,
  "last_modified": "2026-05-04",
  "targeted_segments": ["beta_users", "internal"],
  "rollout_strategy": "canary"
}
```

**Итоговое состояние:** `status=Testing`, `traffic_percentage=25`, `last_modified=2026-05-04`, `rollout_strategy=canary`, `targeted_segments=["beta_users","internal"]`. Сценарий пройден успешно. Вызов `set_feature_state` не выполнялся — фича уже была в Testing, достаточно было `adjust_traffic_rollout`.

### RAG Pipeline (Часть 3)

**Артефакты в репо:**
- Ingestion: `scripts/vectorize.py` — BGE-M3 embeddings → Qdrant (localhost:6333, collection `proshop_chunks`)
- Retrieval: `scripts/query.py` — cosine similarity + cross-lingual RRF
- Корпус: `docs/chunks.jsonl` — 320 чанков (text + 9 полей metadata: source_file, file_path, title, parent_headings, type, keywords, summary, language, chunk_index)
- Промежуточные артефакты: `scripts/tmp/enrich_*.json`

#### Тестовые запросы (3 запроса, top-3 каждый)

**Q1: factual single-hop** — "Какая БД используется в proshop_mern и почему именно она?"

```
EN BRIDGE: which database used proshop_mern why specifically
Ожидание: adrs/adr-001-mongodb...

  #1  cosine=0.6622  rrf=0.03252  type=doc       source=architecture.md       heading=[1. System Overview]
  #2  cosine=0.6569  rrf=0.03252  type=doc       source=best-practices.md     heading=[1. Introduction: Why proshop_mern Is Deprecated]
  #3  cosine=0.6349  rrf=0.03175  type=doc       source=feature-flags-spec.md  heading=[1. Introduction > Feature Flags in This Project]
```

ADR-001 (Context) оказался на #6 по RU-вектору и #4 по EN-вектору. Обзорные чанки с упоминанием MERN/MongoDB получили более высокое косайн-расстояние. Это ожидаемое поведение dense retrieval — общие описания семантически ближе к "какая БД и почему". При подаче top-5+ в генеративную модель ADR-001 попадёт в контекст.

**Q2: multi-hop dependency** — "Какие фичи зависят от payment_stripe_v3?"

```
EN BRIDGE: which features depend payment_stripe_v3?
Ожидание: features/payments.md или feature-flags-spec.md

  #1  cosine=0.6680  rrf=0.03279  type=adr  source=adrs/adr-004-paypal-vs-stripe.md  heading=[Alternatives Considered > Stripe > Braintree]
  #2  cosine=0.6585  rrf=0.03226  type=adr  source=adrs/adr-004-paypal-vs-stripe.md  heading=[Migration Path]
  #3  cosine=0.6158  rrf=0.03150  type=doc  source=feature-flags-spec.md              heading=[4. Feature Flag Catalog > Payments]
```

Результаты релевантные: ADR-004 про выбор PayPal vs Stripe и feature-flags-spec с каталогом payment-флагов. Чанк из features/payments.md не попал в top-3, но общий контекст достаточен для ответа.

**Q3: filtered retrieval** — "Что случилось во время последнего incident с checkout?"

```
EN BRIDGE: what happened during time last incident checkout?
FILTER:   type=incident
Ожидание: incidents/

  #1  cosine=0.5692  rrf=0.03279  type=incident  source=incidents/i-001-paypal-double-charge.md  heading=[Timeline]
  #2  cosine=0.5523  rrf=0.03226  type=incident  source=incidents/i-001-paypal-double-charge.md  heading=[Summary]
  #3  cosine=0.5502  rrf=0.03150  type=incident  source=incidents/i-001-paypal-double-charge.md  heading=[Root Cause Analysis]
```

Фильтр `type=incident` сработал корректно — все 3 результата из `incidents/i-001-paypal-double-charge.md`. Top-1 = Timeline, top-2 = Summary, top-3 = Root Cause — идеальный набор для генеративного ответа об инциденте.

#### Reflection

Для RAG-пайплайна выбран стек: **BGE-M3** (эмбеддинги, 1024-dim cosine), **Qdrant** (векторная БД), **RRF** (Reciprocal Rank Fusion) для кросс-язычного слияния результатов. BGE-M3 — мультиязычная модель, что критично для проекта с русскоязычными запросами и англоязычным корпусом. Qdrant выбран за лёгкость развёртывания (Docker, один контейнер), встроенную поддержку payload-фильтрации и хорошую производительность на <10K векторах. RRF позволяет мерджить результаты RU- и EN-поиска без внешних API перевода — вместо word-by-word перевода используется ранговое слияние, где чанки, попавшие в топ обоих запросов, получают приоритет.

Сложнее всего оказалась чанкинг-стратегия: разбиение по H2/H3-заголовкам давало чанки разного размера (от 50 до 1500 токенов), что влияло на качество эмбеддингов. Пришлось добавить порог слияния мелких секций и задать целевой размер ~600 токенов. Вторая проблема — кросс-язычный bridge: словарь ~80 RU→EN пар покрывает основные термины, но не справляется со сложными конструкциями ("во время последнего incident" → "during time last incident" вместо "during the latest incident"). Эмбеддинговая модель частично компенсирует это за счёт мультиязычности BGE-M3, но идеальным решением был бы LLM-перевод запроса.

Если бы начинали заново, добавили бы **гибридный поиск** (BM25 sparse + dense cosine) — точное совпадение терминов помогло бы в запросах типа Q1, где ADR-001 содержит искомые слова, но проигрывает по семантической близости общим обзорным чанкам. Также имеет смысл добавить **re-ranker** (например, cross-encoder) на финальном этапе — он оценивает релевантность query+chunk парно, а не через косайн-расстояние, и лучше понимает "почему именно она?" как запрос на обоснование решения.

### Search-docs MCP (Часть 4)

MCP-сервер `proshop-rag-search` (FastMCP, tool `search_project_docs(query, top_k)`) обёртывает query.py. Ниже — лог 3 запросов, проведённых через MCP tool, с анализом чанков и формулировкой итогового ответа.

#### Q1: "Какая БД используется в proshop_mern и почему именно она?"

**Вызов:** `search_project_docs(query="Какая БД используется в proshop_mern и почему именно она?", top_k=3)`

**MCP вернул (top-3):**

| # | score | rrf_score | type | source_file | snippet |
|---|-------|-----------|------|-------------|---------|
| 1 | 0.6622 | 0.03252 | doc | architecture.md | "Deprecation notice. The upstream project is explicitly marked as deprecated in favour of proshop-v2. This document describes the v1 codebase as-is..." |
| 2 | 0.6569 | 0.03252 | doc | best-practices.md | "Practical engineering guidance for building production-grade e-commerce systems on the MERN stack. Written for the proshop_mern study project — a deliberately dirty 2020-era codebase..." |
| 3 | 0.6349 | 0.03175 | doc | feature-flags-spec.md | "The ProShop MERN codebase is a teaching project: a full-stack e-commerce application built with MongoDB, Express, React, and Node.js..." |

**Анализ:** Все три чанка — общие обзорные документы. Ни один не содержит обоснования выбора БД. Чанк #3 упоминает MongoDB, что подтверждает факт, но не отвечает на "почему". Выполняю fallback — по source_file из чанков и знанию структуры корпуса читаю полный ADR-001.

**Ответ на основе ADR-001 (adrs/adr-001-mongodb-vs-postgres.md):**

В proshop_mern используется **MongoDB** через Mongoose ODM. Решение принято 2023-01-10 (ADR-001). Причины:
1. **Schema flexibility** — ожидались variable attributes у продуктов (электроника: wattage, clothing: размер), что естественно для document store.
2. **Embedded documents** — Order embeds order items, полный заказ читается одним document fetch без JOIN.
3. **Mongoose ODM** — beginner-friendly API, maps naturally к Express controller patterns.
4. **Atlas free tier** — M0 cluster достаточен для dev/staging, zero cost первые 6 месяцев.
5. **Learning goal** — команда хотела получить опыт MongoDB (у обоих был SQL-опыт).

Альтернатива — PostgreSQL + JSONB — могла бы справиться не хуже. В ретроспективе (ADR-001 Current Assessment) схема продуктов стабилизировалась за 2 месяца, и variable attributes так и не стали реальной проблемой.

---

#### Q2: "Какие фичи зависят от payment_stripe_v3?"

**Вызов:** `search_project_docs(query="Какие фичи зависят от payment_stripe_v3?", top_k=3)`

**MCP вернул (top-3):**

| # | score | rrf_score | type | source_file | snippet |
|---|-------|-----------|------|-------------|---------|
| 1 | 0.6680 | 0.03279 | adr | adrs/adr-004-paypal-vs-stripe.md | "Stripe is now the team's preferred payment processor for new projects. Key advantages over PayPal: Test mode is a faithful replica of production..." |
| 2 | 0.6585 | 0.03226 | adr | adrs/adr-004-paypal-vs-stripe.md | "Migration Path: 1. Install stripe (backend) and @stripe/react-stripe-js (frontend). 2. Create a Stripe Payment Intent on order creation..." |
| 3 | 0.6158 | 0.03150 | doc | feature-flags-spec.md | "Payments — paypal_express_buttons: PayPal Express Checkout Buttons, Default state: Enabled (100%)..." |

**Анализ:** Чанки #1 и #2 — из ADR-004 (разделы про Stripe vs PayPal и Migration Path). Чанк #3 — каталог payment-флагов из feature-flags-spec. Ни один чанк не содержит прямого графа зависимостей от `payment_stripe_v3`. Выполняю fallback — дополняю данными из feature-flags MCP.

**Дополнительно:** вызван `list_features()` из proshop-feature-flags MCP. Найдены payment-фичи: `paypal_express_buttons` (Enabled, 100%), `stripe_alternative` (Testing, 5%), `express_checkout` (Disabled), `apple_pay` (Disabled), `gift_message` (Disabled), `multi_step_checkout_v2` (Testing, 20%).

**Ответ:**

В корпусе нет явного графа зависимостей для `payment_stripe_v3` (этого флаг-идентификатора не существует — есть `stripe_alternative`). По ADR-004 и feature-flags-spec:

- **`stripe_alternative`** (Testing, 5%) — Stripe как альтернативный payment processor. Migration path описан в ADR-004: заменить PayPal JS SDK на Stripe Elements + webhook handler.
- **Фичи, которые затронет миграция на Stripe:** `paypal_express_buttons` (будет заменён), `express_checkout` (depends on payment processor), `multi_step_checkout_v2` (payment step).
- ADR-004 рекомендует Stripe для новых проектов, но PayPal остаётся основным processor в текущем deployment.

---

#### Q3: "Что случилось во время последнего incident с checkout?"

**Вызов:** `search_project_docs(query="Что случилось во время последнего incident с checkout?", top_k=3)`

**MCP вернул (top-3):**

| # | score | rrf_score | type | source_file | snippet |
|---|-------|-----------|------|-------------|---------|
| 1 | 0.6276 | 0.03279 | runbook | runbooks/incident-response.md | "Phase 6: Communication — Timeline: T+0 IC: Incident declared. Investigating. T+5 IC: Issue..." |
| 2 | 0.6013 | 0.03226 | runbook | runbooks/incident-response.md | "Phase 7: Post-Incident — Postmortem template: Incident Postmortem: PayPal Payment Processor Outage, Date: 2024-04-15..." |
| 3 | 0.5974 | 0.03175 | doc | feature-flags-spec.md | "express_checkout — Express One-Click Checkout, Default state: Disabled..." |

**Анализ:** MCP вернул runbook по incident response вместо самого инцидента. Это ограничение текущего MCP tool — нет параметра `type` для pre-filtering (query.py поддерживает `--type incident`, но MCP не экспортирует этот параметр). Выполняю fallback — по знанию структуры корпуса читаю `incidents/i-001-paypal-double-charge.md`.

**Ответ на основе i-001-paypal-double-charge.md:**

**Инцидент i-001: PayPal Sandbox Double-Charge** (P1, resolved, 2023-11-04 — 2023-11-06).

**Что случилось:** PayPal sandbox при определённых network conditions дважды вызывал `onApprove` callback. Backend не проверял, что заказ уже оплачен — каждый вызов помечал заказ как paid и декрементировал `countInStock`. Результат: 7 заказов с duplicate `paymentResult`, 3 товара с отрицательным остатком (один — `-1`).

**Timeline:**
- `2023-11-03 21:14` — PayPal sandbox получает payment
- `21:14:02` — первый `onApprove` → order paid, stock decremented
- `21:14:04` — второй `onApprove` → order updated again, stock decremented again
- `2023-11-04 09:30` — QA замечает `countInStock = -1` в admin panel
- `11:00` — root cause: no idempotency check on `PUT /api/orders/:id/pay`
- `14:00` — fix deployed to staging
- `2023-11-05 10:00` — fix deployed to production

**Fix:** Добавлен idempotency guard (`if (order.isPaid) return 200`) и проверка `isModified('isPaid')` в stock decrement middleware.

**Урок:** PayPal sandbox не faithful replica production. Это стало главной причиной, почему команда предпочитает Stripe для новых проектов (ADR-004).

### End-to-end: search-docs + feature-flags MCP (Часть 5)

**Сценарий:** Найти в документации `payment_stripe_v3`, проверить статус через feature-flags MCP, если Disabled — перевести в Testing 25%, процитировать документацию.

#### Шаг 1 — Поиск в документации (search-docs MCP)

`search_project_docs(query="payment_stripe_v3 dependencies", top_k=3)`

MCP вернул чанки из `feature-flags-spec.md` и `adrs/adr-004-paypal-vs-stripe.md`. В документации идентификатор `payment_stripe_v3` **не встречается** — реальный feature ID: **`stripe_alternative`** ("Stripe as Alternative Payment Processor").

Из `feature-flags-spec.md` — описание фичи:

> The `PaymentScreen` currently has a Stripe radio button that is commented out. This flag enables the Stripe payment path: the user selects Stripe, enters card details in a Stripe Elements form, and payment is confirmed via a backend webhook. Acts as a redundant payment path when PayPal is unavailable.
>
> **System impact:** `PaymentScreen.js` (uncomment + wrap in flag check), new backend route `POST /api/orders/stripe-pay`, Stripe webhook handler.
>
> **Kill Switch.** An external payment provider has a service outage. You disable `stripe_alternative` in seconds, routing all traffic back to PayPal. No code changes, no redeployment.

Зависимости (по docs): `apple_pay` зависит **от** `stripe_alternative` (обратная зависимость — `apple_pay` требует Stripe active).

#### Шаг 2 — Проверка статуса (feature-flags MCP)

```
get_feature_info("payment_stripe_v3")
→ {"error": "FEATURE_NOT_FOUND", "message": "No feature with ID 'payment_stripe_v3' exists in features.json."}

get_feature_info("stripe_alternative")
→ {
    "feature_id": "stripe_alternative",
    "name": "Stripe as Alternative Payment Processor",
    "status": "Testing",
    "traffic_percentage": 5,
    "last_modified": "2026-04-05",
    "targeted_segments": ["beta_users"],
    "rollout_strategy": "canary"
  }
```

Фича уже в **Testing** (5%), не Disabled. Условие "если Disabled" не выполняется, но задача — установить трафик 25%.

Дополнительно проверены связанные фичи:
- `paypal_express_buttons` — **Enabled, 100%** (основной payment processor)
- `apple_pay` — **Disabled, 0%** (зависит от `stripe_alternative`)

#### Шаг 3 — Установка трафика 25%

```
adjust_traffic_rollout(feature_name="stripe_alternative", percentage=25)
→ {
    "feature_id": "stripe_alternative",
    "name": "Stripe as Alternative Payment Processor",
    "status": "Testing",
    "traffic_percentage": 25,
    "last_modified": "2026-05-10",
    "hint": null
  }
```

#### Шаг 4 — Финальное подтверждение

```
get_feature_info("stripe_alternative")
→ {
    "feature_id": "stripe_alternative",
    "name": "Stripe as Alternative Payment Processor",
    "status": "Testing",
    "traffic_percentage": 25,
    "last_modified": "2026-05-10",
    "targeted_segments": ["beta_users"],
    "rollout_strategy": "canary"
  }
```

#### Цитата из документации (зачем нужна фича)

Из `feature-flags-spec.md`, секция `stripe_alternative`:

> Enables the Stripe payment method option that is currently commented out in PaymentScreen.js. Adds a Stripe checkout backend route to orderController and handles webhooks for async payment confirmation. **Acts as a fallback when PayPal is unavailable** and provides credit card tokenization independent of PayPal.

Из `adrs/adr-004-paypal-vs-stripe.md`, раздел "Why Stripe":

> Stripe test mode uses the same code paths as production. Test card numbers produce predictable, reproducible behavior. **The double-callback incident (i-001) would have been surfaced and verifiable in Stripe's test environment.**

**Итоговое состояние:** `stripe_alternative` → status=Testing, traffic=25%, rollout=canary, segments=beta_users, last_modified=2026-05-10.

**Примечание:** Идентификатор `payment_stripe_v3` из задания не существует в features.json и не упоминается в документации. Реальный feature ID — `stripe_alternative`. Это расхождение может указывать на устаревший идентификатор из ранней версии спецификации или на planned feature, которая была переименована.
