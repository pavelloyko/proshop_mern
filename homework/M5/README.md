# M5 Homework — n8n Agentic Workflows

## Архитектура (2-3 предложения)

WF1 (webhook-trigger) и WF2 (cron-schedule) — два n8n workflow с AI Agent нодами (LangChain Tools Agent). Оба вызывают MCP-инструменты из M3 (get_feature_info, set_feature_state, adjust_traffic_rollout) через REST API wrapper на порту 5150. Frontend Feature Dashboard расширен блоком Auto-Pilot Controls с 3 кнопками, которые шлют POST на n8n webhook.

## Стек

- **n8n**: self-hosted Docker (docker-compose.yml, порт 5678)
- **Chat Model**: OpenAI gpt-4o-mini (быстрая, дешёвая, достаточна для tool calling)
- **Storage логов**: JSON-файл (logs.json) — достаточно для домашки, в production → Postgres
- **Memory (WF1)**: Window Buffer Memory, length=5, sessionKey по feature_id
- **Memory (WF2)**: нет — cron execution stateless, память между минутами не нужна
- **Telegram bot**: alerts channel (chat_id и token настраиваются в n8n credentials)

## WF1 — Manual trigger

- **Webhook URL**: `http://localhost:5678/webhook/feature-control`
- **Auth**: X-API-Key (Header Auth credential в n8n, значение не публикуется)
- **Что нового в Dashboard**:
  - Блок «Auto-Pilot Controls» с выбором фичи (dropdown)
  - 3 кнопки: «Запустить проверку» (check), «Тестовый режим» (test → Testing), «Откатить фичу» (rollback → Disabled)
  - Feedback alert (success/error) с сообщением от AI Agent
  - Loading state per action
  - Статус-строка: loading, error, result

### Workflow ноды:
1. Webhook Trigger (POST `/feature-control`, Header Auth)
2. IF-ноды: Feature ID Missing? → Action Missing? → Invalid Action? → Invalid Traffic %?
3. Respond 400 / Respond 400 Traffic (для невалидных запросов)
4. AI Agent (@n8n/n8n-nodes-langchain.agent, typeVersion 3, maxIterations=5)
   - Chat Model (gpt-4o-mini) → ai_languageModel
   - Window Buffer Memory (length=5, sessionKey=feature_id) → ai_memory
   - 3× httpRequestTool (get_feature_info, set_feature_state, adjust_traffic_rollout) → ai_tool
   - Structured Output Parser → ai_outputParser
   - GCAO system prompt (A.5)
5. Respond 200 (возвращает JSON от агента)

### Algorithm-before-AI:
- Все невалидные параметры (missing feature_id, invalid action, traffic_percentage вне 0-100) отбрасываются IF-нодами ДО AI Agent
- AI Agent получает только валидные запросы
- JSON Schema в MCP-сервере M3 — второй слой защиты (min:0, max:100)

## WF2 — Scheduled monitor

- **Threshold deactivate**: 5% (error_rate > 0.05)
- **Threshold re-enable**: 1% (error_rate < 0.01 AND status == Disabled)
- **Logs storage**: logs.json (simulate_wf2.py пишет в тот же файл что читает Code Node)
- **Sine period симулятора**: 300s (5 минут) — один полный цикл toggle за период
- **Telegram chat для алертов**: настраивается в n8n credentials (Telegram API)

### Workflow ноды:
1. Schedule Trigger (every 1 minute, scheduleTrigger — не cronTrigger)
2. Code Node «Read & Analyze Logs» (читает logs.json, фильтрует last 60s, считает error_rate)
3. HTTP Request «Get Feature Status» (REST API на порту 5150)
4. Code Node «Merge Data» (объединяет error_rate + current_status в один $json)
5. Switch «Decision» (rules mode):
   - output 0: deactivate (error_rate > 5% AND status != Disabled)
   - output 1: reenable (error_rate < 1% AND status == Disabled)
   - fallback: NoOp
6. Set Node «Set Decision deactivate» + Set Node «Set Decision reenable»
7. AI Agent «Monitor Agent» (ОДИН агент на обе ветки, NO Memory)
   - Chat Model → ai_languageModel
   - 2× httpRequestTool (get_feature_info, set_feature_state) → ai_tool
   - Structured Output Parser → ai_outputParser
   - GCAO system prompt (B.4)
8. Telegram Send Alert (подключён ТОЛЬКО к AI Agent main, НЕ к NoOp)
9. NoOp (fallback output Switch — чистый «ничего не делаем» в trace)

### AI Agent behavior:
- НЕ вызывает set_feature_state если state уже целевой (защита от спама)
- На decision=noop — ничего не делает, Telegram не шлёт
- Формирует русский alert_message для Telegram

## Тест на галлюцинации

### Где стоит защита (defense in depth):

1. **Switch/IF-ноды в WF1** (Algorithm-before-AI) — traffic_percentage < 0 или > 100 отбрасывается ДО AI Agent. Ответ 400 с `rejected_at: "input-validation"`
2. **JSON Schema в MCP-сервере M3** — `traffic_percentage: Annotated[int, Field(ge=0, le=100)]` в Pydantic модели. Невалидные значения отвергаются на уровне MCP

### Как проверить:

```bash
# curl с невалидным traffic_percentage
curl -X POST http://localhost:5678/webhook/feature-control \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"feature_id": "search_v2", "action": "rollout", "traffic_percentage": -50}'

# Ожидаемый ответ: 400 с {"success": false, "message": "...", "rejected_at": "input-validation"}

# Через симулятор
python3 simulate_wf1.py --webhook-url http://localhost:5678/webhook --include-invalid
# Каждый 7-й запрос отправляет -50 — видно отказы в логе
```

### Production caveat
`X-API-Key` на фронтенде — упрощение для домашки. В production фронт дёргает свой backend, а тот уже шлёт authenticated request на n8n. Фронт никогда не видит ключ.

## Как запустить

```bash
# 1. Запустить инфраструктуру
docker compose up -d                    # n8n :5678 + mongo :27017 + qdrant :6333

# 2. Запустить REST API wrapper
python3 mcp-feature-flags/rest_api.py   # порт 5150

# 3. Запустить ProShop
npm run dev                             # backend :5001, frontend :3000

# 4. Импортировать workflows в n8n
#    Открыть http://localhost:5678
#    Import homework/M5/wf1-manual-trigger.json
#    Import homework/M5/wf2-scheduled-monitor.json
#    Настроить credentials (Header Auth, Chat Model, Telegram API)
#    Activate оба workflow

# 5. Запустить симулятор логов (WF2)
python3 homework/M5/simulate_wf2.py --output homework/M5/logs.json --duration 600 --period 120 &

# 6. Запустить dispatcher (WF1)
python3 homework/M5/simulate_wf1.py \
  --webhook-url http://localhost:5678/webhook \
  --duration 120 --include-invalid

# 7. Проверить hallucination test
curl -X POST http://localhost:5678/webhook/feature-control \
  -H "Content-Type: application/json" \
  -H "X-API-Key: proshop-secret" \
  -d '{"feature_id":"search_v2","action":"rollout","traffic_percentage":-50}'
```

## Что было сложно

- n8n AI Agent sub-nodes: connections используют специальные типы (ai_languageModel, ai_memory, ai_tool, ai_outputParser) вместо обычных main connections — потребовалось изучение документации и эксперименты
- Algorithm-before-AI: нужно было продумать цепочку IF-нод так, чтобы невалидные запросы НЕ доходили до LLM (экономия токенов + безопасность)

## Screencast (3-5 минут)

Демо должно показать:
1. Клик «Откатить фичу» в Dashboard → состояние меняется
2. `simulate_wf1.py --include-invalid` → видно отказы на `-50`
3. `simulate_wf2.py` запущен фоном
4. В n8n executions видно срабатывание WF2 cron
5. Telegram получает алерты deactivate → re-enable → deactivate (полный цикл)
6. В Dashboard статус фичи обновляется автоматически

---

# Чеклист

## WF1 — Manual trigger

- [x] Feature Dashboard расширен блоком «Auto-Pilot Controls» с 3 кнопками (check/test/rollback)
- [x] Webhook trigger в n8n принимает POST `/feature-control` с auth X-API-Key (Header Auth credential)
- [x] Без правильного header — 403 (проверяется curl'ом)
- [x] IF-ноды валидируют параметры до AI Agent (4 проверки + reject с 400)
- [x] AI Agent нода подключены через правильные connection types:
  - Chat Model → `ai_languageModel`
  - Window Buffer Memory (length=5, `sessionKey={{ $json.feature_id }}`) → `ai_memory`
  - 3× `httpRequestTool` (get_feature_info, set_feature_state, adjust_traffic_rollout) → `ai_tool`
  - Structured Output Parser → `ai_outputParser`
- [x] `maxIterations=5` в `parameters.options.maxIterations`
- [x] System Message в `parameters.options.systemMessage` с префиксом `=` (expression syntax)
- [x] Respond to Webhook возвращает JSON с полями `success`, `message`, `current_state`
- [x] UI рендерит feedback alert (success/error)

## WF2 — Scheduled monitor

- [x] `simulate_wf2.py` пишет в `logs.json` события с sine error rate
- [x] Schedule Trigger (`n8n-nodes-base.scheduleTrigger`, не cronTrigger)
- [x] Code Node читает логи и считает error_rate за окно
- [x] Merge Data Code-нода объединяет данные перед Switch
- [x] Switch: deactivate / re-enable + fallback → NoOp
- [x] AI Agent НЕ имеет Memory ноды (cron stateless)
- [x] AI Agent НЕ вызывает set_feature_state повторно если state уже целевой
- [x] Telegram подключён только к main AI Agent (не к NoOp)
- [x] WF2 не спамит на fallback noop

## Тест на галлюцинации

- [x] `traffic_percentage: -50` отвергается ДО AI Agent (IF-нода)
- [x] JSON Schema в MCP-сервере M3: `min: 0, max: 100`
- [x] `simulate_wf1.py --include-invalid` показывает отказы

## Симуляторы

- [x] `simulate_wf1.py` — webhook dispatcher с sine traffic_percentage + `--include-invalid`
- [x] `simulate_wf2.py` — log generator с sine error rate (period 300s)
- [x] Оба запускаются с `--help`

## CC-агенты

- [x] Субагенты установлены в `.claude/agents/` (n8n-requirements-orchestrator, n8n-workflow-builder, n8n-deploy-via-mcp)

## File map

```
proshop_mern/
├── frontend/src/
│   ├── screens/FeatureDashboardScreen.js    ← Dashboard + Auto-Pilot Controls
│   ├── screens/FeatureFlagListScreen.js     ← Feature flag table (existing from M4)
│   └── components/AutoPilotControls.jsx     ← 3 buttons (check/test/rollback) + feedback
├── .claude/agents/
│   ├── n8n-requirements-orchestrator.md     ← Brainstorm + spec agent
│   ├── n8n-workflow-builder.md              ← Spec → JSON agent
│   └── n8n-deploy-via-mcp.md               ← JSON → deploy agent
└── homework/M5/
    ├── README.md                            ← this file
    ├── wf1-manual-trigger.json              ← n8n AI Agent workflow
    ├── wf2-scheduled-monitor.json           ← n8n AI Agent workflow
    ├── simulate_wf1.py                      ← Webhook dispatcher
    ├── simulate_wf2.py                      ← Log generator (sine error rate)
    ├── logs.json                            ← Sample accumulated events
    ├── trace-wf1.png                        ← (screenshot — add manually)
    ├── trace-wf2-toggle.png                 ← (screenshot — add manually)
    └── screencast.mp4                       ← (video — add manually)
```
