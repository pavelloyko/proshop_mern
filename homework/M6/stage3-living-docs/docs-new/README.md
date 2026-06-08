# ProShop Documentation

> Living documentation for proshop_mern — always read `project-index.json` at repo root for machine-readable map.

## Structure

| Folder | Contents |
|---|---|
| `specs/` | Reverse-engineering specs per module (backend, frontend, MCP servers, pipeline+n8n) |
| `adrs/` | Architecture Decision Records (ADR-001 through ADR-005) |
| `api/` | REST API reference — auth, products, orders, users, uploads |
| `features/` | Feature documentation — admin, auth, cart, catalog, checkout, payments |
| `pages/` | Frontend page documentation — all screens with routes and state |
| `runbooks/` | Operational runbooks — setup, deploy, incidents, feature flags |
| `architecture/` | High-level architecture docs |

## Key files

- `feature-flags-spec.md` — Feature flag system design (states, traffic, dependencies)
- `best-practices.md` — Engineering conventions
- `glossary.md` — Project terminology
- `chunking-spec.md` — RAG pipeline chunking strategy
- `features.json` — Current feature flag state

## M6 Additions (Stage 3)

4 new module specs added via 4-step reverse engineering:
- `specs/backend-spec.md` — Express API (30 routes, 3 models, JWT auth)
- `specs/frontend-spec.md` — React SPA (16 screens, Redux store, auth flow)
- `specs/mcp-servers-spec.md` — MCP feature-flags + RAG search servers
- `specs/pipeline-n8n-spec.md` — Data pipeline scripts + n8n automation

## Archived

Historical and stale docs moved to `docs-archived-2026-06-08/`:
- `FINDINGS.md`, `bug_report.md`, `report.md` — historical artifacts
- `dev-history.md` — aspirational timeline (not factual)
- `features-analysis-ru.md` — superseded analysis
- 3 incident reports (`i-001` through `i-003`) — preserved for reference
- `docs/project-data/` — removed duplicate of root `project-data/`
