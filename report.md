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
