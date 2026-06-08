# Architecture Mate -- Review Summary

**Reviewer:** architecture-mate (Opus 4.7)
**Scope:** Full repository -- backend/, frontend/src/, mcp-feature-flags/, mcp-rag-search/, scripts/, simulators/, n8n-workflows/, docker-compose.yml, root config files
**Diff / scope size:** ~8,500 lines across 55+ files
**ADRs loaded:** 5 (ADR-001 through ADR-005)

---

## Findings

- **C1 (HIGH):** 4 issues
- **C2 (MEDIUM):** 9 issues
- **C3 (LOW):** 4 issues
- **Total:** 17 findings

---

## Top concerns (C1)

### 1. `backend/controllers/productController.js:7` -- No service layer; business logic in controllers (LAYER_VIOLATION)

All four controller files (product, order, user, featureFlag) directly import Mongoose models and execute DB queries, data transformation, and response formatting within a single function. The convention documented in CLAUDE.md is "controller -> service -> model", but no service layer exists anywhere in the codebase. Every controller is a god function that mixes HTTP deserialization, business rules, ORM access, and HTTP serialization.

**Impact:** Any change to business logic (e.g., price recalculation, stock validation) requires modifying the controller, which also means re-testing the HTTP layer. Controllers cannot be reused from different entry points (CLI, MCP, cron).

### 2. `backend/controllers/orderController.js:7` -- Client-supplied prices trusted for financial data (LAYER_VIOLATION + ADR-001 violation)

The order creation endpoint accepts `itemsPrice`, `taxPrice`, `shippingPrice`, and `totalPrice` from the request body without server-side recalculation. A client can submit arbitrary prices. Combined with ADR-001's documented weakness on "weaker consistency guarantees for financial operations" and the lack of multi-document transactions in the order creation path, this is a correctness and integrity issue.

**Impact:** A malicious or buggy client can create orders with incorrect totals. No transaction wraps the order creation, so a crash between order insert and potential stock decrement leaves inconsistent state.

### 3. `backend/controllers/featureFlagController.js` + `mcp-feature-flags/server.py` -- Shared mutable file as IPC between two processes (COUPLING)

Three independent systems share `backend/features.json` as their coordination mechanism: the Express backend controller reads and writes it synchronously; the Python MCP server reads and writes it (with atomic rename). There is no locking protocol, no event notification, and no coordination layer. A write from one process can race with a read or write from the other.

**Impact:** Under concurrent mutations (e.g., admin changes a flag via frontend while an AI agent changes it via MCP), the last writer wins and the other's change is silently lost. The MCP server uses atomic rename, but the Express controller uses direct `writeFileSync`, which can corrupt the file if interrupted.

### 4. `backend/routes/productRoutes.js:16` -- Route ordering bug makes GET /api/products/top unreachable (API_BREAKING)

The `/top` route is registered after the `/:id` param route. Express evaluates routes in registration order, so `GET /api/products/top` is matched by `router.route('/:id')` first, treating "top" as a MongoDB ObjectId. This causes `getProductById('top')` to execute instead of `getTopProducts`, triggering a CastError. The homepage ProductCarousel depends on this endpoint and is non-functional.

**Impact:** Broken homepage carousel. Every homepage visit generates a wasted DB query and error. This is also documented in CLAUDE.md as a known gotcha: "Route order matters in Express -- specific paths (/top) must be registered before param routes (/:id)."

---

## Medium concerns (C2)

### 5. `backend/controllers/featureFlagController.js:14` -- Synchronous file I/O as data layer (LAYER_VIOLATION)

Every feature-flag endpoint uses `fs.readFileSync` and `fs.writeFileSync` directly in the controller. There is no data-access abstraction. The controller is coupled to the specific file-based storage mechanism, making it impossible to swap storage (e.g., to MongoDB) without rewriting the controller.

### 6. `backend/routes/featureFlagRoutes.js:14` -- Feature flag mutation endpoints unauthenticated (ADR_VIOLATION)

POST endpoints for flag state and traffic changes lack `protect, admin` middleware, unlike every other mutation route in the project. This violates the API route convention in CLAUDE.md and the access-control pattern established in userRoutes, orderRoutes, and productRoutes. (Also security finding A01-1.)

### 7. `frontend/src/actions/productActions.js:73` -- Massive boilerplate duplication across action files (DESIGN_ANTI_PATTERN)

The error-parsing and 401-logout logic (`const message = error.response && error.response.data.message ? ...`) is copy-pasted verbatim ~12 times across productActions.js, userActions.js, and orderActions.js. Each async action repeats the full REQUEST/SUCCESS/FAIL dispatch ceremony. ADR-002 explicitly identifies this as a known pain point.

### 8. `backend/controllers/featureFlagController.js:68` + `mcp-feature-flags/server.py` -- Duplicated business rules across two codebases (DESIGN_ANTI_PATTERN)

The feature flag state machine (valid states, traffic percentage canonical values, dependency warnings) is implemented independently in the Express controller (JavaScript) and the Python MCP server. Two separate codebases enforce the same rules with no shared contract. A rule change in one system may not be reflected in the other.

### 9. `backend/routes/autopilotRoutes.js:8` -- Custom HTTP client reimplements existing dependency (DESIGN_ANTI_PATTERN)

The autopilot route defines a `nodeFetch()` function that wraps Node's `http`/`https` modules in a Promise, reimplementing functionality already available via `axios` (a project dependency). The custom wrapper has no retry, no interceptor support, and no response-type handling beyond manual JSON.parse.

### 10. `frontend/src/actions/userActions.js:53` -- Auth token persistence scattered across multiple actions (COUPLING)

`localStorage.setItem('userInfo', JSON.stringify(data))` appears independently in `login()`, `register()`, and `updateUserProfile()`. The persistence contract for the auth token is duplicated rather than centralized.

### 11. `backend/server.js:42` -- PayPal config endpoint inline in server.js (DESIGN_ANTI_PATTERN)

The `GET /api/config/paypal` endpoint is an inline closure in server.js instead of following the route/controller convention used by all other endpoints. It breaks the project's routing pattern and is not testable.

### 12. `n8n-workflows/wf1-manual-toggle.json:29` -- Hardcoded API URLs and secrets in workflow nodes (COUPLING)

The n8n workflow files hardcode `http://host.docker.internal:5150` and `proshop-secret` in every HTTP Request node. Changing the MCP API host or auth secret requires editing 6+ nodes across 2 workflow JSON files. No environment variable or credential abstraction is used.

### 13. `backend/controllers/orderController.js:60` -- Incorrect HTTP method in JSDoc (API_BREAKING)

The `updateOrderToPaid` function is documented as `@route GET /api/orders/:id/pay` but is actually registered as `PUT` in orderRoutes.js. This creates confusion for API consumers relying on generated documentation.

---

## Low concerns (C3)

### 14. `frontend/src/reducers/productReducers.js:30` -- Reducer resets product list to empty on REQUEST

`productListReducer` sets `products: []` on every `PRODUCT_LIST_REQUEST`, causing the product grid to disappear during re-fetches (pagination, search). This is a side-effect-like data destruction in a reducer that should preserve existing data during loading.

### 15. `backend/controllers/orderController.js:21` -- Unreachable code after throw

`throw new Error('No order items'); return;` -- the `return` on line 22 is dead code because `throw` exits the function.

### 16. `frontend/src/screens/FeatureFlagListScreen.js:293` -- Business logic mixed into screen component

The 485-line FeatureFlagListScreen contains complex API orchestration logic (action mapping, webhook payload construction, fallback routing, response unwrapping) that should live in actions or a custom hook.

### 17. `backend/controllers/productController.js:12` -- Regex search reinforces ADR-001 concern

Product search uses `$regex` with `$options: 'i'` without a text index. ADR-001's retrospective notes that the schema stabilized quickly and PostgreSQL would have served equally well. The regex pattern further confirms that full-text search capabilities are needed.

---

## Proposed ADRs

### ADR-006: Feature Flag State Ownership and Coordination Protocol

**Status:** Proposed (drafted by architecture-mate during full repository review)
**Date:** 2026-06-07
**Deciders:** TBD (tech lead + backend engineer)

#### Context

The project has three independent systems that read and write feature flag state:
1. Express backend (`featureFlagController.js`) -- reads and writes `backend/features.json` via synchronous `fs` calls
2. Python MCP server (`mcp-feature-flags/server.py`) -- reads and writes the same file via atomic rename
3. n8n workflows -- call the MCP REST API to mutate flags

Currently, there is no coordination protocol. Concurrent writes from different processes can silently lose changes. The state machine rules (valid transitions, canonical traffic percentages) are duplicated in JavaScript (Express controller) and Python (MCP server).

#### Decision

Designate a single authority for feature flag state. Two options:

**Option A -- Express backend as authority:** MCP server calls Express API endpoints instead of writing to the file directly. Express owns the file. Simpler but adds HTTP latency to MCP operations.

**Option B -- MongoDB as the store:** Move feature flags from `features.json` to a MongoDB collection. Both Express and MCP read/write through the database, which provides atomic operations. Aligns with ADR-001 (MongoDB as primary database).

Recommended: **Option B** for consistency with the existing data layer and atomicity guarantees.

#### Consequences

**Positive:**
- Eliminates race conditions between Express and MCP processes
- Enables proper transactions and atomic read-modify-write
- Single source of truth for flag state
- No more synchronous file I/O in Express handlers

**Negative / trade-offs:**
- Requires MongoDB to be available for feature flag operations (currently, Express can start without DB and still serve flags from the JSON file)
- Migration effort: move data, update both Express controller and MCP server

**Risks:**
- MCP server currently starts independently of MongoDB; adding a DB dependency changes its failure mode

#### Alternatives considered
- **Keep JSON file with file-locking:** Adds complexity without solving the duplication of business rules
- **Adopt a dedicated feature flag service (Unleash, LaunchDarkly):** Overkill for the current scale; adds an external dependency

---

### ADR-007: API Client Abstraction for Redux Actions

**Status:** Proposed (drafted by architecture-mate during full repository review)
**Date:** 2026-06-07
**Deciders:** TBD (frontend engineer)

#### Context

The frontend has ~15 async action creators across 4 files (productActions, userActions, orderActions, featureFlagActions). Each repeats the same boilerplate:
1. Dispatch REQUEST action
2. Extract auth token from `getState().userLogin.userInfo`
3. Construct axios config with Authorization header
4. Make the API call
5. Dispatch SUCCESS or FAIL
6. On 401, dispatch `logout()`

The error-parsing pattern (`error.response && error.response.data.message ? error.response.data.message : error.message`) appears 15 times identically. ADR-002 documents this ceremony as a known pain point and notes RTK Query as the planned solution for v3.0.

#### Decision

Before the full RTK migration, introduce a lightweight `apiClient` wrapper that:
1. Auto-attaches the Authorization header from Redux state
2. Auto-dispatches `logout()` on 401 responses
3. Normalizes error responses to a consistent shape

Each action creator would shrink from ~30 lines to ~5-8 lines. The wrapper is compatible with the existing Redux-thunk architecture and does not block the eventual RTK Query migration.

#### Consequences

**Positive:**
- ~60% reduction in action file boilerplate
- Single place to add interceptors (logging, request dedup, retry)
- Consistent error handling across all API calls
- Easier RTK Query migration later (replace apiClient calls with hooks)

**Negative / trade-offs:**
- One more abstraction layer to understand
- Slight deviation from the "standard Redux" tutorial pattern the project follows

**Risks:**
- If RTK Query migration happens soon, the apiClient becomes throwaway code

#### Alternatives considered
- **Wait for RTK Query migration:** Valid, but the duplication is already causing maintenance issues
- **Custom middleware:** More invasive than an apiClient wrapper; harder to reason about

---

## Cross-reference with security-review.md

| Architecture finding | Security finding | Intersection |
|---|---|---|
| #3 (shared file coupling) | MCP concurrent write concern | Same root cause: no coordination protocol |
| #6 (unauthenticated flag endpoints) | A01-1, A01-2 | Same issue, different lenses |
| #1 (no service layer) | A03-1 (regex injection) | Service layer would centralize input validation |
| #2 (client-supplied prices) | A07 (JWT staleness) | Both are integrity gaps in the order flow |
| #8 (duplicated validation) | A02-6 (hardcoded secret) | n8n workflows bypass the Express auth layer entirely |

## Cross-reference with performance-review.md

| Architecture finding | Performance finding | Intersection |
|---|---|---|
| #3 (shared file coupling) | #1, #4 (sync I/O blocking) | Same root cause: synchronous file reads in hot path |
| #4 (route ordering bug) | #5 (route ordering bug) | Identical finding |
| #7 (boilerplate duplication) | #12 (2s polling) | Polling logic would be cleaner with a centralized apiClient |

---

## Status

- [x] All 5 loaded ADRs cross-referenced against the scope
- [x] Layer boundaries scanned (backend: controller -> model direct; frontend: action -> API direct)
- [x] API contract stability checked (route ordering bug, wrong JSDoc method)
- [x] Coupling analysis complete (shared file, duplicated validation, scattered persistence)
- [x] Design patterns reviewed (god controllers, boilerplate duplication, anaemic models)
- [x] Security and performance reviews cross-referenced
