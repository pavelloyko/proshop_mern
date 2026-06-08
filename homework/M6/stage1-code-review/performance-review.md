# Performance Mate -- Review Summary

**Reviewer:** performance-mate (Opus 4.7)
**Scope:** Full repository audit -- backend, frontend, MCP servers, scripts, simulators, infrastructure
**Scope size:** ~12,000 lines across 60+ files
**Hot paths:** GET /api/products, GET /api/orders, GET /api/feature-flags, POST /api/autopilot/feature-control, RAG search MCP

---

## Findings

- **HIGH:** 5 issues (event-loop blocks via sync I/O in hot path)
- **MEDIUM:** 10 issues (unbounded queries, missing indexes, bundle bloat, polling, route ordering bug)
- **LOW:** 4 issues (sequential DB queries, missing cache, unbounded DOM, DevTools in prod)

---

## Top Concerns (HIGH)

### 1. `backend/controllers/featureFlagController.js:15,45,77,114` -- Synchronous file I/O in all feature-flag endpoints

Every feature-flag endpoint uses `fs.readFileSync` (and `fs.writeFileSync` on mutations) directly inside async Express handlers. The GET /api/feature-flags endpoint (called by the frontend dashboard on every load and during polling) reads two files synchronously. The POST endpoints read, parse, modify, serialize, and write -- all synchronously -- blocking the Node.js event loop.

**Impact:** ~1-10ms of event-loop blocking per request. Under load (100 req/s), this compounds to hundreds of milliseconds of cumulative blocking per second, starving all other requests on the same process.

**Intersection with security:** The sync I/O also amplifies the impact of any DoS attempts against the feature-flags endpoint -- a burst of requests will lock the event loop.

### 2. `backend/controllers/orderController.js:112` -- GET /api/orders returns ALL orders with no pagination

The admin orders endpoint fetches every order document with `.populate('user', 'id name')` and returns them all. Each order embeds its orderItems array. No `.limit()`, no `.select()`, no pagination.

**Impact:** At 1K orders: ~500KB response, +200ms p95. At 10K orders: ~5MB response, +2-5s p95. Browser tab may freeze rendering the large table. Memory spike on both server and client.

### 3. `backend/controllers/orderController.js:105` -- GET /api/orders/myorders returns ALL user orders, no pagination

Same pattern as above but scoped to a single user. For active buyers with hundreds of orders, the response is unbounded. No `.select()` to exclude heavy fields.

### 4. `backend/controllers/featureFlagController.js:77,114` -- Triple sync I/O in write endpoints

`setFeatureState` and `adjustTrafficRollout` each perform 3 synchronous file operations: read features.json, write features.json, read descriptions.json. Each write also uses `JSON.stringify(flags, null, 2)` with pretty-printing, adding CPU overhead on top of the I/O block.

**Impact:** ~5-15ms of event-loop blocking per mutation request.

### 5. `backend/routes/productRoutes.js:16` -- Route ordering bug makes GET /api/products/top unreachable

`router.get('/top', getTopProducts)` is registered after `router.route('/:id')`, so Express matches `/top` as an `:id` parameter first. This causes `getProductById('top')` to run instead of `getTopProducts`, triggering a failed MongoDB ObjectId cast. The ProductCarousel on the homepage depends on this endpoint.

**Impact:** Homepage carousel is non-functional. Every homepage visit generates a wasted DB query + error. The product listing with rating sort (`getTopProducts`) is never cached because it never executes.

---

## Medium Concerns

### 6. `backend/controllers/userController.js:111` -- GET /api/users returns ALL users, no pagination, no select

Admin user list fetches all users with `User.find({})`. No field projection (only the model-level `select('-password')` on `getUserById` protects passwords). Returns full documents for all users.

**Impact:** ~500KB at 10K users, grows linearly.

### 7. `backend/models/orderModel.js:6` -- No index on Order.user

The `getMyOrders` query (`Order.find({ user: req.user._id })`) has no index. This is a hot path -- every user profile/order history view triggers it. With 100K orders, full collection scan adds +200-500ms.

### 8. `backend/models/productModel.js` -- No text index on Product.name, category

Product search uses `$regex` with `$options: 'i'` on the `name` field. Without a text index, this is a full collection scan on every search. Case-insensitive regex cannot use standard B-tree indexes efficiently.

**Impact:** +50-500ms on product search at scale (1K+ products).

### 9. `backend/middleware/authMiddleware.js:17` -- DB query on every authenticated request

The `protect` middleware calls `User.findById(decoded.id).select('-password')` on every request with a Bearer token. This is an extra DB roundtrip on top of whatever the actual endpoint does.

**Impact:** +5-15ms per authenticated request. At 100 req/s, this is 100 unnecessary DB queries per second.

### 10. `frontend/src/bootstrap.min.css` -- 176KB full Bootstrap CSS loaded synchronously

The entire Bootstrap CSS framework (176KB) is imported in `index.js` and is render-blocking. Only a fraction of the classes are used.

**Impact:** +176KB CSS, ~880ms on 3G connection. Delays first contentful paint.

### 11. `frontend/src/App.js` -- No code splitting, all 16 screens bundled upfront

All screens and components are statically imported. The entire application JS is in a single chunk.

**Impact:** Estimated +200-400KB of JS loaded unnecessarily on initial page load. +1-2s on 3G.

### 12. `frontend/src/screens/FeatureFlagListScreen.js:285` -- Aggressive 2-second polling after flag actions

After any flag mutation, starts a 2-second interval for 10 seconds (5 requests). Each poll triggers the sync-file-read feature-flags endpoint on the backend.

**Impact:** 5 sequential HTTP requests, each triggering 2 sync file reads on the backend. Compounds with finding #1.

### 13. `backend/controllers/productController.js:116` -- O(n) review scan + reduce on every review submission

`createProductReview` loads all reviews into memory, scans with `.find()` for duplicate check, then does a separate `.reduce()` for rating recalculation. Two passes over the array.

**Impact:** Negligible with <100 reviews. +2ms per 100 reviews above that.

### 14. `frontend/src/screens/FeatureFlagListScreen.js:255` -- JSON.parse(JSON.stringify()) deep clone on every Redux update

Deep-clones the entire flags object via JSON round-trip on every flags fetch (including polls).

**Impact:** ~1-2ms main-thread blocking per poll cycle. Unnecessary overhead since Redux state is already immutable.

### 15. `frontend/src/reducers/productReducers.js:30` -- productListReducer resets products to [] on every REQUEST

On `PRODUCT_LIST_REQUEST`, the products array is reset to empty `[]`, causing the product grid to disappear during re-fetches (pagination, search changes). This triggers a full unmount/remount cycle for all Product components.

**Impact:** Visual flash (empty grid -> loader -> grid). Not a perf issue per se but causes unnecessary DOM churn.

---

## Low Concerns

### 16. `backend/controllers/productController.js:20` -- Two sequential DB queries for product listing

`countDocuments` and `find` run sequentially (both with the same filter). Could be parallelized with `Promise.all` or combined with `$facet`.

**Impact:** ~10-20ms extra latency per product listing request.

### 17. `backend/controllers/productController.js:154` -- No caching on getTopProducts

Full sort by rating on every homepage load. The top-3 products rarely change.

**Impact:** ~5-15ms per homepage visit. Could be eliminated with a 5-minute TTL cache.

### 18. `frontend/src/screens/ProductScreen.js:124` -- Unbounded Array creation for quantity selector

`[...Array(product.countInStock).keys()]` creates N option elements. If countInStock is large (admin error), this generates thousands of DOM nodes.

**Impact:** Normal case is fine. Edge case: laggy/freezing dropdown if countInStock is set to a large value.

### 19. `frontend/src/store.js:84` -- Redux DevTools always enabled (including production)

`composeWithDevTools` is applied unconditionally. In production, it retains all dispatched actions and state snapshots in memory.

**Impact:** ~5-10MB memory overhead per session for action history.

---

## Total Estimated Impact

| Category | Estimated Impact |
|---|---|
| API latency p95 (feature-flags) | +10-50ms per request (sync I/O) |
| API latency p95 (orders, unbounded) | +200ms at 1K orders, +2-5s at 10K orders |
| API latency p95 (auth middleware) | +5-15ms on every authenticated request |
| Event-loop blocking (feature-flags) | +1-15ms per request, compounds under load |
| Frontend bundle size | +376KB (176KB CSS + ~200KB JS from no code-splitting) |
| First Contentful Paint (3G) | +1.5-2.5s from bundle bloat |
| Frontend memory (DevTools) | +5-10MB per session |
| DB query overhead (missing indexes) | +200-500ms at 100K orders, +50-500ms product search |

---

## Cross-specialist Collaboration

- **security-mate:** The sync I/O in feature-flags endpoints (finding #1) is also a DoS amplification vector -- a burst of requests to GET /api/feature-flags or POST /api/feature-flags/:name/state will lock the event loop. The admin endpoints for orders/users returning all records without pagination (findings #2, #3, #6) also facilitate data exfiltration.
- **architecture-mate:** The route ordering bug (finding #5) is both a performance and correctness issue. The protect-middleware-per-request DB query (finding #9) stems from the stateless JWT architecture choice documented in ADR-003. The N+1-ish review scan (finding #13) stems from the embedded review sub-schema pattern.

---

## Status

- [x] N+1 scan complete
- [x] Blocking I/O scan complete
- [x] Bundle / asset diff reviewed
- [x] Caching opportunities identified
- [x] Missing index scan complete
- [x] Frontend rendering review complete
- [x] MCP servers reviewed (no perf issues found -- MCP feature-flags uses async file I/O via FastMCP, RAG server lazy-loads model)
