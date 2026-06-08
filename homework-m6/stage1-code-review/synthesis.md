# Code Review Synthesis — proshop_mern (homework M6 Stage 1)

**Date:** 2026-06-07
**Reviewer:** 3-agent team (security + performance + architecture)
**Scope:** entire repository — backend/, frontend/src/, mcp-feature-flags/, mcp-rag-search/, scripts/, simulators/, n8n-workflows/, docker-compose.yml, root config
**Files scanned:** ~12,000 lines across 60+ files

---

## Summary

| Metric | Count |
|---|---|
| Total findings | 55 |
| HIGH (C1) | 7 security + 5 performance + 4 architecture = **16** |
| MEDIUM (C2) | 10 security + 10 performance + 9 architecture = **29** |
| LOW (C3) | 2 security + 4 performance + 4 architecture = **10** |

---

## HIGH severity (16 findings)

### Security (7)

| # | File:Line | Issue | Fix approach | Effort |
|---|-----------|-------|-------------|--------|
| S-1 | `backend/routes/featureFlagRoutes.js:14` | Feature flag write endpoints unauthenticated | Add `protect, admin` middleware | 15min |
| S-2 | `backend/routes/autopilotRoutes.js:49` | Autopilot proxy has no auth (acknowledged in comment) | Add `protect, admin` middleware | 15min |
| S-3 | `docker-compose.yml:13` | Hardcoded n8n credentials committed to git | Move to .env, rotate secrets, scrub git history | 30min |
| S-4 | `n8n-workflows/wf1-manual-toggle.json:29` | Shared secret "proshop-secret" hardcoded in workflow JSON (6 occurrences) | Parameterize via n8n env vars | 30min |
| S-5 | `mcp-feature-flags/rest_api.py:44` | Default auth secret "proshop-secret" as fallback | Remove default, fail if env var missing | 15min |
| S-6 | `backend/routes/userRoutes.js:16` | No rate limiting on login — brute-force vulnerable | Add express-rate-limit (5 attempts / 15 min) | 20min |
| S-7 | `backend/utils/generateToken.js:4` | 30-day JWT with no refresh/revocation mechanism | Reduce to 1h access + 7d refresh token | 2h |

### Performance (5)

| # | File:Line | Issue | Impact | Fix approach | Effort |
|---|-----------|-------|--------|-------------|--------|
| P-1 | `featureFlagController.js:15,45,77,114` | Sync fs.readFileSync/writeFileSync in all feature-flag endpoints | +1-10ms event-loop block per request | Cache in module scope, async I/O | 1h |
| P-2 | `orderController.js:112` | GET /api/orders returns ALL orders, no pagination | +5MB at 10K orders | Add pagination (limit/offset) | 1h |
| P-3 | `orderController.js:105` | GET /api/orders/myorders unbounded | +500KB for active buyers | Add pagination + .select() | 30min |
| P-4 | `featureFlagController.js:77,114` | Triple sync I/O in write endpoints | +5-15ms event-loop block per mutation | Async I/O or in-memory cache | 1h |
| P-5 | `productRoutes.js:16` | Route ordering bug: `/top` registered after `/:id` | Homepage carousel broken, wasted DB queries | Move `/top` before `/:id` | 5min |

### Architecture (4)

| # | File:Line | Issue | Criticality | Fix approach | Effort |
|---|-----------|-------|-------------|-------------|--------|
| A-1 | `productController.js:7` | No service layer — business logic in controllers (violates CLAUDE.md convention) | C1 | Extract services (incremental) | 4h+ |
| A-2 | `orderController.js:7` | Client-supplied prices trusted for financial data (no server-side recalculation) | C1 | Server-side price recalculation from product DB | 1.5h |
| A-3 | `featureFlagController.js` + `mcp-feature-flags/server.py` | Shared mutable file as IPC — no locking, race conditions | C1 | Move to MongoDB (ADR-006 proposal) | 3h |
| A-4 | `productRoutes.js:16` | Route ordering bug (same as P-5) | C1 | Move `/top` before `/:id` | 5min |

---

## MEDIUM severity (29 findings)

### Security (10)

| # | File:Line | Issue | OWASP |
|---|-----------|-------|-------|
| S-8 | `orderController.js:43` | IDOR: getOrderById doesn't verify ownership | A01 |
| S-9 | `orderController.js:60` | IDOR: updateOrderToPaid doesn't verify ownership | A01 |
| S-10 | `.env:4` | JWT_SECRET set to trivial "abc123" | A02 |
| S-11 | `.env.example:4` | .env.example has same weak JWT_SECRET | A02 |
| S-12 | `productController.js:12` | MongoDB $regex from unsanitized input — ReDoS risk | A03 |
| S-13 | `userRoutes.js:15` | No rate limiting on registration | A04 |
| S-14 | `server.js:27` | No security headers (helmet) | A05 |
| S-15 | `server.js:33` | No CORS configuration | A05 |
| S-16 | `userActions.js:53` | JWT in localStorage — XSS-vulnerable (per ADR-003) | A07 |
| S-17 | `authMiddleware.js:33` | isAdmin from stale JWT claim — demoted admins keep access 30d | A07 |

### Performance (10)

| # | File:Line | Issue | Impact |
|---|-----------|-------|--------|
| P-6 | `userController.js:111` | GET /api/users unbounded, no pagination | +500KB at 10K users |
| P-7 | `orderModel.js:6` | No index on Order.user | +200-500ms at 100K orders |
| P-8 | `productModel.js` | No text index for $regex search | +50-500ms at 1K+ products |
| P-9 | `authMiddleware.js:17` | DB query on every authenticated request | +5-15ms per request |
| P-10 | `bootstrap.min.css` | 176KB full Bootstrap CSS, render-blocking | +880ms on 3G |
| P-11 | `App.js` | No code splitting, 16 screens in single bundle | +200-400KB JS |
| P-12 | `FeatureFlagListScreen.js:285` | 2-second aggressive polling after flag actions | 5 requests × 2 sync reads each |
| P-13 | `productController.js:116` | O(n) review scan + reduce on every review submission | +2ms per 100 reviews |
| P-14 | `FeatureFlagListScreen.js:255` | JSON.parse/stringify deep clone on every Redux update | ~1-2ms per poll |
| P-15 | `productReducers.js:30` | productListReducer resets to [] on REQUEST | Visual flash, DOM churn |

### Architecture (9)

| # | File:Line | Issue | Criticality |
|---|-----------|-------|-------------|
| A-5 | `featureFlagController.js:14` | Sync file I/O as data layer — no abstraction | C2 |
| A-6 | `featureFlagRoutes.js:14` | Unauthenticated flag mutation endpoints | C2 |
| A-7 | `productActions.js:73` | Massive boilerplate duplication (~12× copy-paste) | C2 |
| A-8 | `featureFlagController.js:68` + `mcp-feature-flags/server.py` | Duplicated business rules across JS and Python | C2 |
| A-9 | `autopilotRoutes.js:8` | Custom nodeFetch reimplements axios | C2 |
| A-10 | `userActions.js:53` | Auth token persistence scattered across 3 actions | C2 |
| A-11 | `server.js:42` | PayPal config endpoint inline in server.js | C2 |
| A-12 | `wf1-manual-toggle.json:29` | Hardcoded URLs and secrets in n8n workflows | C2 |
| A-13 | `orderController.js:60` | Wrong HTTP method in JSDoc (GET vs PUT) | C2 |

---

## LOW severity (10 findings)

| # | File:Line | Source | Issue |
|---|-----------|--------|-------|
| S-18 | `errorMiddleware.js:12` | security | Stack traces in non-prod errors (acceptable) |
| S-19 | `users.js:7` | security | Seed data weak password "123456" |
| P-16 | `productController.js:20` | performance | Sequential DB queries (could parallelize) |
| P-17 | `productController.js:154` | performance | No caching on getTopProducts |
| P-18 | `ProductScreen.js:124` | performance | Unbounded Array for quantity selector |
| P-19 | `store.js:84` | performance | Redux DevTools enabled in production |
| A-14 | `productReducers.js:30` | architecture | Reducer data destruction on REQUEST |
| A-15 | `orderController.js:21` | architecture | Unreachable code after throw |
| A-16 | `FeatureFlagListScreen.js:293` | architecture | Business logic in screen component (485 lines) |
| A-17 | `productController.js:12` | architecture | Regex search reinforces ADR-001 concern |

---

## Cross-mate observations (findings flagged by ≥ 2 agents)

| Issue | Security | Performance | Architecture | Root cause |
|---|---|---|---|---|
| Unauthenticated feature flag endpoints | S-1, S-2 | — | A-6 | Missing middleware |
| Sync file I/O in feature-flag endpoints | — | P-1, P-4 | A-5 | No data layer abstraction |
| Shared file coupling (Express + MCP) | — | P-1, P-4 | A-3 | No coordination protocol |
| Route ordering `/top` vs `/:id` | — | P-5 | A-4 | Route registration order |
| Hardcoded secrets in n8n workflows | S-4 | — | A-12 | No env var usage |
| Client-supplied order prices | — | — | A-2 | Missing server-side validation |

---

## Top-3 для Stage 2

| # | File:Line | Issue | Recommended fix | Effort | Why top-3 |
|---|-----------|-------|----------------|--------|-----------|
| **1** | `backend/routes/featureFlagRoutes.js:14` + `backend/routes/autopilotRoutes.js:49` | Unauthenticated write endpoints — any user can toggle feature flags and trigger AI workflows | Add `protect, admin` middleware to both routers | 15min | **Triple-flagged** (security HIGH + architecture C2 + cross-mate). Simplest high-impact fix. |
| **2** | `backend/routes/productRoutes.js:16` | Route ordering bug breaks homepage carousel (`/top` unreachable) | Move `router.get('/top', ...)` before `router.route('/:id')` | 5min | **Double-flagged** (perf HIGH + arch C1). One-line fix, immediate user-visible result. |
| **3** | `backend/controllers/orderController.js:7` | Client-supplied prices in order creation — no server-side recalculation | Calculate prices server-side from Product DB records | 1.5h | **Architecture C1 + security integrity gap**. Financial correctness issue — orders can have wrong totals. |

---

## Recommended fix order (top 5)

1. 🔴 **Route ordering** (P-5/A-4) — 5min, fixes broken homepage
2. 🔴 **Unauthenticated endpoints** (S-1/S-2/A-6) — 15min, blocks anonymous admin actions
3. 🟡 **Client-supplied prices** (A-2) — 1.5h, financial integrity
4. 🟡 **Hardcoded secrets** (S-3/S-4/S-5) — 30min, credential rotation
5. 🟡 **Sync file I/O** (P-1/P-4/A-5) — 1h, event-loop unblocking

---

## Proposed ADRs (from architecture-mate)

1. **ADR-006: Feature Flag State Ownership** — Move from shared JSON file to MongoDB, eliminating race conditions between Express and MCP processes
2. **ADR-007: API Client Abstraction** — Centralize auth headers, error handling, and 401-logout logic to eliminate ~60% of action file boilerplate

---

## Token usage estimate

- security-mate: ~45K output tokens
- performance-mate: ~50K output tokens
- architecture-mate: ~55K output tokens
- synthesis (this file): ~8K output tokens
- **Total: ~158K output tokens** (~$2.40 at Opus pricing)
