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
