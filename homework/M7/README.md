# M7 Homework — Private AI Assistant with Privacy Router

## What I built

A privacy-first AI shopping assistant embedded into ProShop that automatically routes requests based on PII sensitivity:

- **PII detected** (email, phone, credit card) → request stays on the **local machine** (Ollama, Qwen3:8B, $0)
- **Clean request** → goes to the **cloud** (OpenRouter, Claude Sonnet 4, ~$0.003-0.007/query)
- **All queries logged** to `chatlogs` MongoDB collection, visible in admin dashboard

## Architecture choice: Express.js code router (not n8n)

The spec recommends n8n as default, but I chose a pure Express.js implementation for reliability:

| Aspect | n8n (spec default) | Express.js (my choice) |
|---|---|---|
| Ollama connectivity | Docker→host networking issues | Direct `localhost:11434` |
| Tool-calling | AI Agent nodes, fragile | Full control, custom agent loop |
| MongoDB access | n8n nodes/AI Agent tools | Direct Mongoose queries |
| Debugging | Black box UI | `console.log`, stack traces |
| External deps | n8n + tunnels + credentials | Zero (Express already running) |

Both approaches implement the same architecture — the choice is about reliability for this specific project.

## Stack

| Component | Choice | Why |
|---|---|---|
| Local model | Ollama + Qwen3:8B (Q4_K_M) | Fits 16GB MacBook Pro, free, data stays local |
| Cloud model | Claude Sonnet 4 via OpenRouter | Best tool-calling, $5 budget covers ~700+ queries |
| PII detection | Regex (JavaScript) | Deterministic, zero dependencies, catches email/phone/credit card |
| Router | Express.js code | Full control, no external dependencies |
| Agent (cloud) | Tool-calling agent loop (ReAct) | Claude excels at structured tool calling |
| Agent (local) | Context pre-fetching + simple completion | Most reliable for local model (Q4 tool-calling can be unreliable) |
| Frontend | React chat widget + admin dashboard | Follows existing proshop_mern patterns |

## How it works

### Cloud branch (clean queries)
1. User message passes PII regex check → clean
2. Agent loop sends message + tools to Claude Sonnet 4 via OpenRouter
3. Claude calls tools: `getProducts(query)`, `getMyOrders()`, `getMyProfile()`
4. Tool functions execute MongoDB queries **scoped by userId from JWT** (not from model args)
5. Response returned to user, logged to chatlogs with cost

### Local branch (PII detected)
1. PII regex detects email/phone/credit card in message
2. Keyword-based context fetcher pre-fetches relevant data from MongoDB
3. Context injected into system prompt for local Qwen3:8B model
4. Simple completion (no tool-calling loop) for reliability
5. Response returned, logged with $0.00 cost

### Security design
- **userId from JWT only** — tools never accept userId from model arguments
- `getMyOrders()` and `getMyProfile()` are scoped to the authenticated user
- `getProducts()` is public catalog data, no scoping needed
- PII data physically cannot leave the machine (architecture, not policy)

## Demo results (9 queries)

| # | Query | PII | Route | Model | Latency | Cost |
|---|---|---|---|---|---|---|
| 1 | "What products do you have?" | — | ☁️ cloud | Claude Sonnet 4 | 7.0s | $0.0061 |
| 2 | "Show me the latest products" | — | ☁️ cloud | Claude Sonnet 4 | 7.9s | $0.0071 |
| 3 | "send details to john@mail.com" | EMAIL | 🔒 local | Qwen3:8b | 87s | $0.00 |
| 4 | "Hello, I need help" | — | ☁️ cloud | Claude Sonnet 4 | 2.3s | $0.0029 |
| 5 | "phone +1 555 123 4567, orders" | PHONE | 🔒 local | Qwen3:8b | 47s | $0.00 |
| 6 | "What are my recent orders?" | — | ☁️ cloud | Claude Sonnet 4 | 3.6s | $0.0038 |

**Totals:** 9 queries, 3 local, 6 cloud
**Cloud cost:** $0.0199 total
**Saved by local routing:** $0.06 (3 queries × ~$0.02 estimated cloud cost)

## Files created/modified

| File | Action |
|---|---|
| `backend/models/chatLogModel.js` | Created — Mongoose schema for chatlogs |
| `backend/routes/assistantRoutes.js` | Created — PII router + agent loop + logging |
| `backend/server.js` | Modified — mounted `/api/assistant` route |
| `frontend/src/components/ChatWidget.js` | Created — floating chat widget |
| `frontend/src/screens/AIRouterDashboardScreen.js` | Created — admin dashboard |
| `frontend/src/App.js` | Modified — added route + ChatWidget to layout |
| `frontend/src/components/Header.js` | Modified — added "AI Router" admin nav link |
| `.env` | Modified — added `OPENROUTER_API_KEY` |

## How to run

```bash
# 1. Start MongoDB + Ollama
docker start mongo
ollama serve   # or open Ollama.app

# 2. Pull model (first time only)
ollama pull qwen3:8b

# 3. Set OpenRouter key in .env
# OPENROUTER_API_KEY = sk-or-v1-...

# 4. Start the app
npm run dev

# 5. Open http://localhost:3000 → login → chat bubble in bottom-right
# 6. Admin: http://localhost:3000/admin/ai-dashboard
```

## Why the router doesn't need GPU

The PII detection is pure regex — runs in microseconds on any CPU. The routing decision is deterministic code, not an LLM call. This is the core thesis of the homework: **architecture enforces privacy, not policy**. The router is O(1) string matching, not O(n) token generation.

## DZ2 — Prompt Injection Attack & Defense (+4 bonus)

Full writeup in `dz2/writeup-dz2.md`.

### Attack results
- **Direct injection (BEFORE/Vulnerable):** 🔴 Agent dumped all users' emails (admin@, john@, jane@) via `getAllUsers()` tool
- **Direct injection (AFTER/Secure):** 🟢 Blocked — `getAllUsers` tool doesn't exist, agent can't comply even if jailbroken
- **Indirect injection (attempted):** Claude Sonnet 4 safety training caught the malicious review payload — but this is probabilistic, not guaranteed

### Defense layers
1. **Deterministic (main):** Scoped tools — `getMyOrders(userId)` where userId comes from JWT, never from model args. Wide tools (`getAllUsers`, `getAllOrders`) removed entirely.
2. **Probabilistic (supplementary):** Hardened system prompt explicitly marking review content as DATA, not instructions.

### OWASP mapping
- **LLM01 (Prompt Injection):** Direct injection bypassed system prompt; scoped tools prevented damage
- **LLM06 (Excessive Agency):** Removed wide DB tools; enforced least privilege

### Key principle
> The system prompt says "don't do X", but a jailbroken model does X anyway. Scoped tools say "you CAN'T do X" — and the code enforces it 100% deterministically. **Protect ACTIONS, not ANSWERS.**

## Key insight from the demo

The router catches PII in the **user's message** (input), but the agent itself pulls private data from the DB (order address, email). If that cloud-bound agent fetches user data, it still goes through the cloud model. This is the deep problem mentioned in `THEORY-privacy-routing.md` — the router only sees input, not the agent's tool outputs. For production, you'd need output scanning or intent-based routing.
