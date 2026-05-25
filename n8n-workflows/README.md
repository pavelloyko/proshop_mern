# n8n Integration — Setup & Usage Guide

## Quick Start

```bash
# 1. Start all services
docker compose up -d          # n8n (5678), mongo (27017), qdrant (6333)

# 2. Start REST API wrapper (MCP tools over HTTP)
python3 mcp-feature-flags/rest_api.py   # port 5150

# 3. Start ProShop app
npm run dev                   # backend :5001, frontend :3000

# 4. (Optional) Start traffic simulator
python3 simulators/traffic_simulator.py # writes simulators/logs.json
```

## Import Workflows into n8n

1. Open http://localhost:5678
2. Click **"..." menu** → **Import from File**
3. Select `n8n-workflows/wf1-manual-toggle.json` or `wf2-scheduled-monitor.json`
4. Click **Activate** (top-right toggle)

## WF1 — Manual Feature Toggle

**Trigger**: Frontend button click → POST to n8n webhook

**Flow**:
```
Frontend → n8n Webhook → Auth Check → Switch (action)
  → enable/disable/testing: REST API call → Respond to frontend
  → traffic: validate 0-100 → REST API call → Respond
  → invalid: Respond with error (Algorithm-before-AI)
```

**Webhook URL**: `http://localhost:5678/webhook/feature-toggle`

**Fallback**: If n8n is down, frontend calls REST API directly on port 5150.

**Test**:
```bash
# Valid toggle
curl -X POST http://localhost:5678/webhook/feature-toggle \
  -H "Content-Type: application/json" \
  -H "x-auth: proshop-secret" \
  -d '{"feature_name":"dark_mode","action":"enable"}'

# Anti-hallucination test (should be rejected)
curl -X POST http://localhost:5678/webhook/feature-toggle \
  -H "Content-Type: application/json" \
  -H "x-auth: proshop-secret" \
  -d '{"feature_name":"dark_mode","action":"traffic","traffic_percentage":-50}'
```

## WF2 — Scheduled Defensive Monitor

**Trigger**: Cron every 1 minute

**Flow**:
```
Schedule (1 min) → Get Logs → Get Feature State → Calc Error Rate
  → error_rate > 15% → Disable feature + Telegram alert
  → error_rate <= 15% + disabled → Re-enable feature + Telegram alert
  → otherwise → No action
```

**Test with simulator**:
```bash
# Terminal 1: Start REST API
python3 mcp-feature-flags/rest_api.py

# Terminal 2: Start simulator with aggressive error rate
python3 simulators/traffic_simulator.py --period 60 --amplitude 0.25 --base-rate 0.10

# Terminal 3: Run threshold test (live mode, real toggles)
python3 simulators/threshold_test.py --live --ticks 120 --period 30 --interval 0.5
```

**Expected output**:
```
Tick   3: enabled → disabled (error_rate=16.8%)  OK
Tick  13: disabled → enabled (error_rate=13.1%)  OK
PASS: Full auto-toggling cycle observed
```

## REST API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/features` | No | List all 25 features |
| GET | `/api/features/{name}` | No | Get one feature |
| POST | `/api/features/{name}/state` | Yes | Set state (Enabled/Disabled/Testing) |
| POST | `/api/features/{name}/traffic` | Yes | Set traffic % (0-100) |
| GET | `/api/logs` | No | Read traffic logs |

Auth: `x-auth: proshop-secret` header required for POST endpoints.

## Anti-Hallucination Validation

All input validation happens BEFORE any action (Algorithm-before-AI):

| Input | Rejected by | Response |
|-------|------------|----------|
| `percentage: -50` | REST API + n8n IF node | `400 INVALID_PERCENTAGE` |
| `percentage: 999` | REST API + n8n IF node | `400 INVALID_PERCENTAGE` |
| `state: "Hacked"` | REST API + n8n Switch | `400 INVALID_STATE` |
| Missing `x-auth` | REST API + n8n IF node | `401 UNAUTHORIZED` |

## Claude Code Prompts

Three agent prompts in `.claude/agents/`:

1. **n8n-requirements-orchestrator.md** — Idea → spec (nodes, connections, data flow, validation rules)
2. **n8n-workflow-builder.md** — Spec → n8n JSON (importable workflow)
3. **n8n-deploy-via-mcp.md** — JSON → deploy (import via n8n API without copy-paste)

## Simulators

### traffic_simulator.py
Generates synthetic traffic with sinusoidal error rate:
```bash
python3 simulators/traffic_simulator.py --period 120 --amplitude 0.15 --base-rate 0.05
```

### threshold_test.py
Runs auto-toggling cycle test:
```bash
# Dry run (no real toggles)
python3 simulators/threshold_test.py --ticks 120 --period 30

# Live mode (toggles real features via REST API)
python3 simulators/threshold_test.py --live --ticks 120 --period 30
```

## File Structure

```
proshop_mern/
├── .claude/agents/
│   ├── n8n-requirements-orchestrator.md
│   ├── n8n-workflow-builder.md
│   └── n8n-deploy-via-mcp.md
├── mcp-feature-flags/
│   ├── server.py              # MCP stdio (for Claude Code)
│   ├── http_server.py         # MCP streamable-http (unused, requires session)
│   └── rest_api.py            # REST wrapper (for n8n HTTP Request nodes)
├── simulators/
│   ├── traffic_simulator.py   # Sinusoidal log generator
│   ├── threshold_test.py      # Auto-toggle cycle test
│   └── logs.json              # Generated traffic logs
├── n8n-workflows/
│   ├── wf1-manual-toggle.json # Manual trigger workflow
│   ├── wf2-scheduled-monitor.json # Scheduled monitor workflow
│   └── README.md              # This file
└── docker-compose.yml         # n8n + mongo + qdrant
```
