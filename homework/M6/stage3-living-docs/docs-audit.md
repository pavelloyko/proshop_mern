# Existing docs audit — proshop_mern

> Audited for M6 Stage 3 Phase 1.5. Goal: classify every doc file before building new living docs structure.
> Every existing `docs/<folder>` and each top-level doc-file gets its own verdict.

**Auditor:** `legacy-auditor-mate` (Opus 4.7)
**Audit date:** 2026-06-08
**Repo:** proshop_mern — MERN eCommerce learning project (Brad Traversy course fork)
**Existing docs scanned:** 55 files across 10 locations (2 root md, 1 root data, 6 subfolders, docs/ duplicates + extras)

---

## Verdict legend

| Symbol | Verdict | Action in Phase 4 |
|---|---|---|
| ✅ | **ACCURATE** — matches code, well-maintained | Keep as-is in new docs structure |
| 🔄 | **PARTIALLY ACCURATE** — mostly right, has stale sections | Copy + add `TODO(audit-2026-06-08): <what>` markers in stale parts |
| 📦 | **HISTORICAL** — old but worth preserving (dev-history, past ADRs, post-mortems) | Move to `docs-archived-2026-06-08/`, **never `rm`**; link from new arch overview |
| ❌ | **STALE / REDUNDANT** — outdated and superseded | Archive first (never delete), then ignore going forward |

---

## Inventory

### Root .md files

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `CLAUDE.md` | file (8.5K) | ✅ ACCURATE | AI assistant rules file. Actively maintained. References match codebase (Node v16, port 5001, proxy, ES Modules, routes, Mongoose 5). Feature-flags MCP and RAG sections are current. Only doc that covers autopilotRoutes, featureFlagRoutes, FeatureDashboardScreen. | Keep as-is; this is the source-of-truth for AI collaboration rules |
| `DESIGN.md` | file (7K) | ✅ ACCURATE | Design system spec. Current as of 2026-05-15. CSS variables, spacing scale, component patterns, React-Bootstrap override strategy all match frontend/src/index.css. References Manrope font (correct), not Inter. | Keep as-is; primary reference for all UI work |
| `README.md` | file (6K) | ✅ ACCURATE | Project overview, quick start, troubleshooting. Feature Flags API section is current (GET /api/feature-flags, GET /api/feature-flags/:name). Seed accounts match backend/data/. Node v16 requirement correct. Port 5001 correct. | Keep as-is; entry point for new developers |
| `FINDINGS.md` | file (4K) | 📦 HISTORICAL | Bug audit from 2026-04-27. Finding #3 marked "fixed in commit 28e8613"; rest are "not yet". Superseded by bug_report.md which has more detail. Worth preserving as a compact status tracker. | Archive; reference from new docs if bug-tracking section is added |
| `bug_report.md` | file (6K) | 📦 HISTORICAL | Full code audit dated 2026-04-27. 27 findings with code references, all verified against actual codebase (orderController.js, authMiddleware.js, store.js, etc.). Outdated dependencies table is useful but will age. Finding descriptions are accurate and detailed. | Archive; link from new architecture/tech-debt section |
| `report.md` | file (10K) | 📦 HISTORICAL | M3 homework submission report. Contains MCP test scenarios (search_v2, stripe_alternative), RAG pipeline test results (Q1-Q3), end-to-end scenario. Valuable as institutional context for how MCP/RAG were validated. Not reference documentation. | Archive; reference from M3 history section |

### project-data/ root files

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/architecture.md` | file (25K) | 🔄 PARTIALLY ACCURATE | Comprehensive architecture doc. **Stale sections:** (1) Section 2 says "Node.js 22" but actual runtime is v16 per CLAUDE.md and .nvmrc; (2) Section 4.2 lists 20 Redux slices but misses feature-flag related slices (featureFlags); (3) Section 4.4 lists 14 screens but actual count is 16 (missing FeatureDashboardScreen, FeatureFlagListScreen); (4) Section 5.2 REST routes missing autopilotRoutes and featureFlagRoutes; (5) Section 4.3 mentions "redux-persist" which is not in the codebase; (6) Section 8.1 mentions `npm run data:import-extra` and `npm run mongo:up` which don't exist in package.json. Otherwise the schema descriptions, middleware chain, PayPal flow, and cross-collection relationships are accurate. | Keep with TODO markers on stale sections; most comprehensive arch doc we have |
| `project-data/dev-history.md` | file (12K) | 📦 HISTORICAL | Fictional but internally consistent project timeline (Jan 2023 - Apr 2026). Release notes reference versions that don't exist in git (v0.1 through v2.7). Claims Redux Toolkit migration in v1.0 but codebase uses classic Redux (combineReducers, hand-written reducers). Claims express-validator, Jest+Supertest tests, rate-limiting, helmet, cors, structured logging — none of which exist in code. Valuable as a "what the project could become" narrative. | Archive; link from new architecture/README.md as background context |
| `project-data/best-practices.md` | file (18K) | ✅ ACCURATE | Generic MERN production guidance. Not codebase-specific (deliberately so — it contrasts proshop's 2020 patterns vs 2026 best practices). References are real URLs. Sections on Mongoose design, PayPal patterns, JWT security, feature flags, RBAC, performance are all technically sound. Section 10 "Concrete Patterns to Apply" lists actionable TODOs. | Keep as-is; reference material for future improvements |
| `project-data/feature-flags-spec.md` | file (large) | ✅ ACCURATE | Authoritative reference for features.json and MCP server. Schema description matches actual features.json format (name, description, status, traffic_percentage, last_modified, targeted_segments, rollout_strategy, dependencies). MCP tool semantics match actual MCP server behavior. Catalog section covers all 25 flags. | Keep as-is; primary source for feature flag system |
| `project-data/features-analysis-ru.md` | file (6K) | 📦 HISTORICAL | Russian-language analysis of feature flags for M3-M7 course navigation. Recommends `multi_step_checkout_v2` as anchor feature. Useful for understanding course design decisions but is a planning document, not technical reference. | Archive; reference from course planning section |
| `project-data/glossary.md` | file (12K) | 🔄 PARTIALLY ACCURATE | Domain and technical glossary. Most terms are accurate. **Stale sections:** (1) "Cart" entry references `frontend/src/slices/cartSlice.js` but actual path is `frontend/src/reducers/cartReducer.js` (no Redux Toolkit); (2) "Checkout" entry references `frontend/src/screens/CheckoutScreen.jsx` but actual file is ShippingScreen.js/PaymentScreen.js/PlaceOrderScreen.js (no CheckoutScreen); (3) "Node.js" entry says "v14+" but CLAUDE.md says v16 required; (4) Feature flag example uses `new_search_filter` but actual flag key is `search_v2`; (5) Missing terms: feature-flags, MCP, RAG, n8n, autopilot (added in M5). | Keep with TODO markers on stale entries; add missing terms |

### project-data/adrs/ (5 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/adrs/adr-001-mongodb-vs-postgres.md` | file | ✅ ACCURATE | MongoDB vs PostgreSQL decision. References match codebase: Mongoose ODM, backend/config/db.js, embedded reviews in Product. Decision rationale is coherent. | Keep, copy to new docs/adr/ |
| `project-data/adrs/adr-002-redux-vs-context.md` | file | 🔄 PARTIALLY ACCURATE | Claims RTK migration happened in v1.0 (Jul 2023) but codebase still uses classic Redux (combineReducers in store.js, hand-written reducers). Status line says "RTK Query migration planned for v3.0" which is aspirational. Otherwise accurate about the original decision context. | Keep with TODO marker: "RTK migration not yet reflected in code" |
| `project-data/adrs/adr-003-jwt-vs-session.md` | file | ✅ ACCURATE | JWT over session cookies. Matches codebase: jsonwebtoken library, Bearer token in Authorization header, protect middleware in authMiddleware.js, 30-day expiry in generateToken.js. | Keep, copy to new docs/adr/ |
| `project-data/adrs/adr-004-paypal-vs-stripe.md` | file | ✅ ACCURATE | PayPal as payment processor with Stripe preference for new projects. Matches codebase: react-paypal-button-v2, PayPal SDK dynamic loading in OrderScreen.js, PAYPAL_CLIENT_ID from /api/config/paypal. References Incident i-001 correctly. | Keep, copy to new docs/adr/ |
| `project-data/adrs/adr-005-bootstrap-vs-tailwind.md` | file | ✅ ACCURATE | Bootstrap 4 via react-bootstrap. Matches codebase: react-bootstrap ^1.3.0, bootstrap.min.css vendored in frontend/src/, Bootstrap components (Container, Row, Col, etc.) used throughout screens. Migration to Tailwind pending. | Keep, copy to new docs/adr/ |

### project-data/api/ (5 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/api/auth.md` | file | ✅ ACCURATE | Auth endpoints documented: POST /api/users/login, POST /api/users, GET /api/users/profile, PUT /api/users/profile. Request/response shapes match userController.js. JWT 30-day expiry correct. | Keep, copy to new docs/api/ |
| `project-data/api/products.md` | file | ✅ ACCURATE | Product endpoints: GET /api/products (paginated), GET /api/products/top, GET /api/products/:id, POST, PUT, DELETE, POST reviews. Page size 10 correct. Keyword regex search correct. | Keep, copy to new docs/api/ |
| `project-data/api/orders.md` | file | ✅ ACCURATE | Order endpoints: POST /api/orders, GET /api/orders/myorders, GET /api/orders/:id, PUT pay, PUT deliver, GET all. Matches orderController.js and orderRoutes.js. | Keep, copy to new docs/api/ |
| `project-data/api/users.md` | file | ✅ ACCURATE | User management endpoints for admin: GET /api/users, GET /api/users/:id, PUT /api/users/:id, DELETE /api/users/:id. Matches userRoutes.js. | Keep, copy to new docs/api/ |
| `project-data/api/uploads.md` | file | ✅ ACCURATE | Upload endpoint: POST /api/uploads. Multer config (2MB limit, jpg/jpeg/png, image-{timestamp}.{ext} naming) matches uploadRoutes.js. Static serving from /uploads correct. | Keep, copy to new docs/api/ |

### project-data/features/ (6 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/features/auth.md` | file | ✅ ACCURATE | Login, register, profile, JWT mechanics. Screen/action/reducer/references match: LoginScreen.js, userActions.js (login, logout, register), userLoginReducer, POST /api/users/login, authUser controller. | Keep |
| `project-data/features/cart.md` | file | ✅ ACCURATE | Add to cart, remove, qty control, localStorage persistence. addToCart flow through ProductScreen → CartScreen → cartActions → cartReducer → localStorage matches code exactly. | Keep |
| `project-data/features/catalog.md` | file | ✅ ACCURATE | Product list, detail, search, pagination, carousel, reviews. HomeScreen.js, Product.js, ProductCarousel.js, listProducts action, getProducts controller — all match codebase. | Keep |
| `project-data/features/checkout.md` | file | ✅ ACCURATE | 4-step checkout: CheckoutSteps.js, ShippingScreen, PaymentScreen, PlaceOrderScreen. Component props (step1-step4) match code. | Keep |
| `project-data/features/payments.md` | file | ✅ ACCURATE | PayPal SDK dynamic loading, payment confirmation, order status. OrderScreen.js addPayPalScript function, /api/config/paypal endpoint, payOrder action — all match. | Keep |
| `project-data/features/admin.md` | file | 🔄 PARTIALLY ACCURATE | Admin features. Core CRUD operations documented correctly. **Missing:** Feature Dashboard screen (/admin/featuredashboard), FeatureFlagListScreen, AutoPilotControls.jsx — all added in M5. Admin section should be updated with these new screens. | Keep with TODO marker for missing feature-dashboard/autopilot screens |

### project-data/incidents/ (3 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/incidents/i-001-paypal-double-charge.md` | file | 📦 HISTORICAL | PayPal sandbox double-charge (Nov 2023). Well-structured postmortem: timeline, impact, root cause, fix, lessons. References PUT /api/orders/:id/pay correctly. Valuable for understanding idempotency patterns. | Archive but reference from runbooks/incident-response and ADR-004 |
| `project-data/incidents/i-002-mongo-connection-pool-exhaustion.md` | file | 📦 HISTORICAL | MongoDB connection pool exhaustion (Black Friday 2023). References Render.com deployment (fictional timeline). Useful as a pattern for what could happen. | Archive but reference from runbooks |
| `project-data/incidents/i-003-jwt-secret-leak.md` | file | 📦 HISTORICAL | .env committed to git (Feb 2023 - Jul 2024). Good security incident pattern. References git-secrets pre-commit hook (not actually in repo). | Archive but reference from runbooks |

### project-data/pages/ (15 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/pages/INDEX.md` | file | ✅ ACCURATE | Navigation index for all page docs. Links are valid. Statistics (15 docs, 4543 words) are plausible. | Keep |
| `project-data/pages/home.md` | file | ✅ ACCURATE | HomeScreen routes, components, API calls, edge cases — all verified against code. | Keep |
| `project-data/pages/product.md` | file | ✅ ACCURATE | ProductScreen (/product/:id) — details, reviews, add-to-cart. | Keep |
| `project-data/pages/login.md` | file | ✅ ACCURATE | LoginScreen (/login) — auth flow, redirect parameter. | Keep |
| `project-data/pages/register.md` | file | ✅ ACCURATE | RegisterScreen (/register) — registration flow. | Keep |
| `project-data/pages/cart.md` | file | ✅ ACCURATE | CartScreen (/cart/:id?) — cart management. | Keep |
| `project-data/pages/shipping.md` | file | ✅ ACCURATE | ShippingScreen (/shipping) — address form. | Keep |
| `project-data/pages/payment.md` | file | ✅ ACCURATE | PaymentScreen (/payment) — payment method selection. | Keep |
| `project-data/pages/place-order.md` | file | ✅ ACCURATE | PlaceOrderScreen (/placeorder) — order review and confirmation. | Keep |
| `project-data/pages/order.md` | file | ✅ ACCURATE | OrderScreen (/order/:id) — PayPal payment, delivery tracking. | Keep |
| `project-data/pages/profile.md` | file | ✅ ACCURATE | ProfileScreen (/profile) — user profile, order history. | Keep |
| `project-data/pages/admin-users.md` | file | ✅ ACCURATE | UserListScreen (/admin/userlist). | Keep |
| `project-data/pages/admin-user-edit.md` | file | ✅ ACCURATE | UserEditScreen (/admin/user/:id/edit). | Keep |
| `project-data/pages/admin-products.md` | file | ✅ ACCURATE | ProductListScreen (/admin/productlist). | Keep |
| `project-data/pages/admin-product-edit.md` | file | ✅ ACCURATE | ProductEditScreen (/admin/product/:id/edit). | Keep |
| `project-data/pages/admin-orders.md` | file | ✅ ACCURATE | OrderListScreen (/admin/orderlist). | Keep |

### project-data/runbooks/ (6 files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/runbooks/local-setup.md` | file | 🔄 PARTIALLY ACCURATE | Node.js v14+ listed but CLAUDE.md says v16 required. Steps are otherwise correct (clone, npm install, Docker, seed, run). Missing: Feature flags setup (MCP server), n8n setup. | Keep with TODO markers for Node v16 and M5 additions |
| `project-data/runbooks/deploy.md` | file | 🔄 PARTIALLY ACCURATE | Heroku-focused deployment runbook. Heroku free tier discontinued 2022 — deployment target is aspirational. Environment variables and build steps are technically correct for Heroku pattern. Missing: Render.com alternative, Docker deployment. | Keep with TODO marker: "Heroku free tier gone; update for Render/Docker" |
| `project-data/runbooks/db-seed-and-reset.md` | file | ✅ ACCURATE | Seed operations (npm run data:import, npm run data:destroy). Commands match package.json scripts. Seed data accounts (admin@example.com) match backend/data/users.js. | Keep |
| `project-data/runbooks/feature-flag-toggle.md` | file | ❌ STALE | Describes a MongoDB-backed feature flag system with FeatureFlag model and Mongoose queries. **Actual implementation uses `features.json` file read by MCP server** — completely different architecture. Schema shown (key, enabled, rolloutPercentage, targetUserIds, excludeUserIds, startDate, endDate, metadata) does not match features.json schema at all. | Archive; replace with accurate flag-toggle runbook based on features.json + MCP |
| `project-data/runbooks/ab-test-setup.md` | file | ✅ ACCURATE | Generic A/B testing methodology. Not codebase-specific — statistical concepts, sample size calculation, pre-test checklist are universally valid. References feature flag rollout_percentage correctly. | Keep |
| `project-data/runbooks/incident-response.md` | file | ✅ ACCURATE | Generic incident response procedure (P0-P3 severity, phases, escalation, postmortem template). References Incident i-001 correctly. Phase structure is sound. | Keep |

### docs/ (non-duplicate files)

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `docs/architecture.md` | file (4K) | 🔄 PARTIALLY ACCURATE | C4-style Mermaid diagram of system. Shows 15 screens but actual count is 16 (missing FeatureDashboardScreen). Shows 12 components but actual count is 14 (missing AutoPilotControls.jsx and FeatureFlagListScreen is a screen not component). Routes list missing autopilotRoutes and featureFlagRoutes. Otherwise diagram structure is correct. | Keep with TODO markers for missing routes/screens |
| `docs/chunking-spec.md` | file (2K) | ✅ ACCURATE | RAG pipeline chunking specification. Describes the schema and rules for docs/chunks.jsonl. Schema fields (text, metadata with source_file, file_path, title, parent_headings, type, keywords, summary, language, chunk_index) match actual chunks.jsonl records. Source path `docs/project-data/` is correct. | Keep; RAG pipeline reference |
| `docs/chunks.jsonl` | file (320 lines) | ✅ ACCURATE | 320 pre-computed RAG chunks from project-data/. Verified: line count matches, schema matches chunking-spec.md, first record structure correct. This is a build artifact, not source documentation. | Keep as RAG artifact; regenerate when source docs change |
| `docs/project-data/` | folder (48 files) | ❌ STALE / REDUNDANT | **Exact binary duplicate** of root `project-data/` (verified with diff). Having two copies risks divergence. The root `project-data/` is the canonical source (referenced by CLAUDE.md, chunking-spec.md, RAG scripts). | Archive `docs/project-data/`; all references should point to root `project-data/` |

### project-data/features.json

| Path | Type | Verdict | Reasoning (1-3 lines) | Action |
|---|---|---|---|---|
| `project-data/features.json` | file (data) | ✅ ACCURATE | Read-only snapshot of feature flags data. Matches the schema described in feature-flags-spec.md. Contains all 25 flags. Note: canonical live copy is `backend/features.json` (edited by MCP server); this is a documentation reference copy. | Keep as reference snapshot; note that backend/features.json is the live version |

---

## Summary

- ✅ Keep as-is: **39** items (CLAUDE.md, DESIGN.md, README.md, all 5 ADRs except ADR-002 partial, all 5 API docs, 5 of 6 features docs, all 15 pages docs, 3 of 6 runbooks, chunking-spec, chunks.jsonl, features.json, best-practices.md, feature-flags-spec.md)
- 🔄 Update + keep: **6** items (architecture.md in project-data, glossary.md, ADR-002, features/admin.md, local-setup.md, deploy.md, docs/architecture.md)
- 📦 Archive (historical): **7** items (FINDINGS.md, bug_report.md, report.md, dev-history.md, features-analysis-ru.md, all 3 incidents)
- ❌ Archive (stale): **2** items (docs/project-data/ duplicate folder, runbooks/feature-flag-toggle.md)

**Total: 54 items reviewed** (48 unique project-data files + 3 root-only md + 3 docs-only files).

---

## Cross-references to preserve

Things that **must not get lost** in the restructure:

- `dev-history.md` → referenced from `architecture.md` Section 10 and from ADR-001 through ADR-005 (each ADR says "Full ADR in adrs/adr-NNN-*.md").
- Past ADRs → preserve numbering ADR-001 through ADR-005 in `docs-new/adr/` (do **not** restart from 1).
- `feature-flags-spec.md` → primary source for MCP server behavior; referenced from `report.md` M3 submission.
- `best-practices.md` Section 10 → concrete TODOs that should be tracked as tech-debt items.
- All 3 incidents → referenced from `runbooks/incident-response.md` (Phase 7 postmortem template) and from ADR-004.
- `glossary.md` → referenced implicitly by all features/* docs (Russian-language features docs use terms defined in glossary).
- `pages/INDEX.md` → navigation hub for all page docs; links must remain valid.
- `docs/chunks.jsonl` → build artifact tied to `docs/chunking-spec.md`; path references `docs/project-data/` as source (update after archiving docs/project-data/ duplicate).
- `backend/features.json` → live data file; `project-data/features.json` is documentation snapshot. Do not confuse the two.

---

## Notes for Phase 2 planning

1. **`docs/project-data/` is a dangerous duplicate.** It must be archived/removed to prevent future divergence. The root `project-data/` is canonical. If chunking scripts reference `docs/project-data/`, update them to use root `project-data/` instead.

2. **`runbooks/feature-flag-toggle.md` is dangerously wrong.** It describes a completely different architecture (MongoDB FeatureFlag model) from the actual implementation (features.json file + MCP server). This could mislead someone trying to understand the system. Must be replaced, not just updated.

3. **`dev-history.md` describes a fictional timeline.** It claims RTK migration, Jest tests, helmet, cors, rate-limiting, structured logging — none of which exist in the codebase. It is useful as aspirational documentation but must be clearly labeled as non-factual to avoid confusion.

4. **`architecture.md` has a Node version error.** Says "Node 22" in the system diagram but the project requires Node v16. This is a critical factual error that should be fixed.

5. **`architecture.md` and `docs/architecture.md` miss M5 additions.** Both miss FeatureDashboardScreen, FeatureFlagListScreen, AutoPilotControls.jsx, autopilotRoutes.js, featureFlagRoutes.js. These were added in the M5 homework for AI Agent workflows.

6. **`glossary.md` has file path errors.** References Redux Toolkit paths (slices/cartSlice.js) that don't exist; actual code uses classic Redux (reducers/cartReducer.js). Several terms reference wrong file paths.

7. **Incidents should NOT be archived blindly.** `runbooks/incident-response.md` references all three incidents as examples. The postmortem template in Phase 7 explicitly uses i-001 as a template. Archive incidents but preserve cross-references.

8. **`pages/` folder is the cleanest subfolder.** All 15 page docs plus INDEX.md are accurate and match the codebase. They can be copied as-is to the new structure.

9. **API docs are accurate but incomplete.** The 5 API docs cover the original routes (products, users, orders, auth, uploads) but miss M5 additions: `GET /api/feature-flags`, `GET /api/feature-flags/:name`, `POST /api/autopilot/feature-control`. These should be added.

10. **`CLAUDE.md` is the single most accurate document.** It is the only doc that mentions autopilotRoutes, featureFlagRoutes, FeatureDashboardScreen, and the MCP tool integrations. It should be treated as the source of truth when resolving conflicts between documents.
