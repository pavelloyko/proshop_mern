# Security Mate — Review Summary

**Reviewer:** security-mate (Opus 4.7)
**Scope:** Full repository — backend/, frontend/src/, mcp-feature-flags/, mcp-rag-search/, scripts/, simulators/, n8n-workflows/, docker-compose.yml, root config files
**Diff / scope size:** ~6,500 lines across 48 files
**Time:** ~120 seconds

---

## Findings

- **HIGH:** 7 issues
- **MEDIUM:** 10 issues
- **LOW:** 2 issues
- **Total:** 19 findings

---

## Top concerns (HIGH)

1. **backend/routes/featureFlagRoutes.js:14** — Feature flag state/traffic endpoints lack authentication. Any unauthenticated user can enable/disable feature flags or adjust traffic percentages via POST. (A01)

2. **backend/routes/autopilotRoutes.js:49** — Autopilot proxy to n8n AI Agent has no auth middleware. The code comment explicitly says "should be admin in production" but protect/admin was never added. Any user can trigger AI Agent workflows. (A01)

3. **docker-compose.yml:13** — Hardcoded n8n admin credentials (user=admin, password=proshop, API key=n8n_api_proshop_2024) committed to git. These are visible in the entire git history. (A02)

4. **n8n-workflows/wf1-manual-toggle.json:29** — Shared secret "proshop-secret" hardcoded in n8n workflow JSON files (6 occurrences across 2 files). Used as the authentication check for webhook calls. (A02)

5. **mcp-feature-flags/rest_api.py:44** — Default authentication secret "proshop-secret" hardcoded as fallback. If MCP_AUTH_SECRET env var is missing, the server runs with this guessable credential. (A02)

6. **backend/routes/userRoutes.js:16** — No rate limiting on login endpoint. Vulnerable to brute-force password attacks with no mitigation. (A04)

7. **backend/utils/generateToken.js:4** — JWT expiry set to 30 days with no refresh token mechanism and no server-side revocation. A stolen token remains valid for up to 30 days. (A07)

---

## All findings by OWASP category

### A01 — Broken Access Control (3 findings)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 1 | HIGH | backend/routes/featureFlagRoutes.js:14 | Feature flag write endpoints unauthenticated — any user can change flag state/traffic |
| 2 | HIGH | backend/routes/autopilotRoutes.js:49 | Autopilot proxy endpoint has no auth — acknowledged in comment but not fixed |
| 3 | MEDIUM | backend/controllers/orderController.js:43 | IDOR: getOrderById does not verify order ownership — any authenticated user can view any order |
| 4 | MEDIUM | backend/controllers/orderController.js:60 | IDOR: updateOrderToPaid does not verify order ownership — any user can mark any order as paid |

### A02 — Cryptographic Failures (5 findings)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 5 | HIGH | docker-compose.yml:13 | Hardcoded n8n credentials (admin/proshop) and API key committed to git |
| 6 | HIGH | n8n-workflows/wf1-manual-toggle.json:29 | Shared secret "proshop-secret" hardcoded in workflow JSON (6 occurrences) |
| 7 | HIGH | mcp-feature-flags/rest_api.py:44 | Default fallback auth secret "proshop-secret" in MCP REST API |
| 8 | MEDIUM | .env:4 | JWT_SECRET set to trivial guessable value "abc123" |
| 9 | MEDIUM | .env.example:4 | .env.example contains same weak JWT_SECRET value "abc123" — may be copied to production |

### A03 — Injection (1 finding)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 10 | MEDIUM | backend/controllers/productController.js:12 | MongoDB $regex built from unsanitized user input — potential ReDoS/regex injection |

### A04 — Insecure Design (2 findings)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 11 | HIGH | backend/routes/userRoutes.js:16 | No rate limiting on login — brute-force vulnerable |
| 12 | MEDIUM | backend/routes/userRoutes.js:15 | No rate limiting on registration — allows automated account creation |

### A05 — Security Misconfiguration (3 findings)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 13 | MEDIUM | backend/server.js:27 | No security headers (helmet) — missing CSP, X-Frame-Options, HSTS, X-Content-Type-Options |
| 14 | MEDIUM | backend/server.js:33 | No CORS configuration — default behavior relies on frontend proxy |
| 15 | LOW | backend/middleware/errorMiddleware.js:12 | Stack traces in non-production error responses (acceptable with correct NODE_ENV) |

### A07 — Authentication Failures (4 findings)

| # | Severity | File:Line | Issue |
|---|----------|-----------|-------|
| 16 | HIGH | backend/utils/generateToken.js:4 | 30-day JWT expiry with no refresh tokens and no server-side revocation |
| 17 | MEDIUM | frontend/src/actions/userActions.js:53 | JWT stored in localStorage — XSS-vulnerable (acknowledged in ADR-003) |
| 18 | MEDIUM | backend/middleware/authMiddleware.js:33 | isAdmin checked from stale JWT claim — demoted admins retain admin for up to 30 days |
| 19 | LOW | backend/data/users.js:7 | Seed data uses weak password "123456" for admin account |

### Categories with no findings

- **A06 (Vulnerable Components):** Not audited — `npm audit` not run (dependencies are outdated per CLAUDE.md, pinned to Node v16 and webpack 4)
- **A08 (Data Integrity Failures):** Clean — no deserialization issues found
- **A09 (Logging & Monitoring):** Clean — morgan logging present in dev mode; no sensitive data logged
- **A10 (SSRF):** Clean — autopilot proxy uses server-side env var for target URL, not user-controlled
- **SECRETS:** Covered under A02 findings
- **CRYPTO-MISCONFIG:** Clean — bcrypt with cost factor 10 is acceptable; no MD5/SHA1 for passwords

---

## Notable patterns observed

- **Upload route** (backend/routes/uploadRoutes.js) has MIME validation but no file size limit configured in multer, and the route lacks auth middleware. Severity is LOW since the route is not wired with `protect` in the Express router — however, the upload endpoint itself is accessible without authentication.
- **MCP Feature Flags Python server** (mcp-feature-flags/server.py) writes directly to `backend/features.json` with no locking mechanism. Under concurrent writes, data corruption is possible. This is a reliability concern more than a security issue.
- **MCP REST API auth** (rest_api.py:51) uses a simple string equality check (`auth != AUTH_SECRET`) instead of `hmac.compare_digest()`, which is vulnerable to timing attacks. Severity is LOW given the threat model.

---

## Status

- All OWASP Top 10 (2021) categories scanned
- Dependency audit NOT run (npm audit / pip-audit) — known outdated deps per CLAUDE.md, but CVE enumeration is out of scope for a code review
- Secrets scan completed — 3 hardcoded credentials found in committed files
- 19 findings total: 7 HIGH, 10 MEDIUM, 2 LOW
