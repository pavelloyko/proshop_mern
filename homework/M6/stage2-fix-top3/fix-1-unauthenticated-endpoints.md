# Fix #1 — Unauthenticated Feature Flag & Autopilot Endpoints

## Original finding (from synthesis.md)

**S-1 / S-2 / A-6 (triple-flagged):** Feature flag write endpoints (`POST /:name/state`, `POST /:name/traffic`) and autopilot proxy (`POST /feature-control`) lacked authentication middleware. Any anonymous user could toggle feature flags, change traffic percentages, and trigger AI Agent workflows.

## What I changed

### backend/routes/featureFlagRoutes.js
```diff
+ import { protect, admin } from '../middleware/authMiddleware.js'

- router.route('/:name/state').post(setFeatureState)
- router.route('/:name/traffic').post(adjustTrafficRollout)
+ router.route('/:name/state').post(protect, admin, setFeatureState)
+ router.route('/:name/traffic').post(protect, admin, adjustTrafficRollout)
```

### backend/routes/autopilotRoutes.js
```diff
+ import { protect, admin } from '../middleware/authMiddleware.js'

  router.post(
    '/feature-control',
+   protect,
+   admin,
    asyncHandler(async (req, res) => {
```

## Why this approach

- Adds the same `protect, admin` middleware chain used by all other mutation routes in the project (productRoutes, orderRoutes, userRoutes)
- Read-only endpoints (`GET /`, `GET /descriptions`, `GET /:name`) remain public — consistent with the existing pattern (e.g. `GET /api/products` is public)
- Minimal change — 3 lines added total, no business logic touched
- Trade-off: n8n workflows that call these endpoints directly will now need a valid admin JWT. The MCP server already uses its own auth (X-API-Key header), so it's unaffected.

## Test status

Manual verification:
- `POST /api/feature-flags/dark_mode/state` without token → 401 Unauthorized ✅
- `POST /api/autopilot/feature-control` without token → 401 Unauthorized ✅
- `GET /api/feature-flags` without token → 200 OK (still public) ✅

## Behavior change

**Intentional behavior change** — anonymous access to write endpoints is now blocked. This is a security fix, not a refactor.

## Lessons learned

The autopilot route had a comment "should be admin in production" — a common pattern where security debt is acknowledged but never addressed. The fix was trivial once identified by 3 independent agents.
