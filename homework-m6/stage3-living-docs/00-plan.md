# Audit Plan — proshop_mern (M6 Stage 3)

**Date:** 2026-06-08
**Auditor:** legacy-auditor-mate workflow in main CC session

---

## Project shape (from Phase 1)

- **Project type:** Fullstack monorepo (backend + frontend + MCP servers + n8n infra)
- **Tech stack:** Node 16 + Express 4 + Mongoose 5 + React 16 + Redux 4 + Python (MCP/RAG via FastMCP + Qdrant + BGE-M3)
- **Subprojects discovered:**
  - `backend/` — Express API (controllers, routes, middleware, models, utils)
  - `frontend/` — React SPA (Redux, React-Bootstrap, ~16 screens)
  - `mcp-feature-flags/` — Python MCP server (FastMCP, reads/writes backend/features.json)
  - `mcp-rag-search/` — Python RAG MCP server (FastMCP, Qdrant, BGE-M3 embeddings)
  - `scripts/` — Data pipeline (chunk.py, vectorize.py, query.py, enrich_chunks.py, combine_chunks.py)
  - `simulators/` — Load testing (simulate_wf1.py, traffic_simulator.py, threshold_test.py)
  - `n8n-workflows/` — 2 n8n workflow JSON files
  - `n8n-data/` — n8n persisted data
  - `n8n-mcp/` — External cloned repo (OUT OF SCOPE)
- **Existing docs surface:** `project-data/` (48 files), `docs/project-data/` (duplicate), `docs/architecture.md`, `docs/chunking-spec.md`, root .md files
- **Tests surface:** NONE (no test files in scope — only n8n-mcp has tests, but it's out of scope)
- **Legacy markers:** No TODO/FIXME/HACK found in backend/frontend/MCP code

## Existing docs audit (from Phase 1.5)

- ✅ Keep: 39 items (all ADRs, API docs, page docs, most features, CLAUDE.md, DESIGN.md, README.md)
- 🔄 Update + keep: 6 items (architecture.md, glossary, ADR-002, admin features, local-setup, deploy runbook)
- 📦 Archive (historical): 7 items (FINDINGS.md, bug_report.md, report.md, dev-history.md, features-analysis-ru.md, 3 incidents)
- ❌ Archive (stale): 2 items (docs/project-data/ duplicate, runbooks/feature-flag-toggle.md wrong architecture)
- Full table: `homework-m6/stage3-living-docs/docs-audit.md`

## Audit scope

- **IN scope:** backend/, frontend/src/, mcp-feature-flags/, mcp-rag-search/, scripts/, simulators/, n8n-workflows/, docker-compose.yml, project-data/, docs/, root .md files
- **OUT of scope:** n8n-mcp/, M3/, M4-materials/, docs/M6/, node_modules/, frontend/build/

---

## Phase 3 — REVERSE-ENG (specialist sub-agents, serial)

Reuse Stage 1 findings from `homework-m6/stage1-code-review/synthesis.md` — NO re-run of security/performance/architecture mates.

- [ ] 3.1 4-step reverse engineering: `backend/` module (controllers + routes + middleware + models)
- [ ] 3.2 4-step reverse engineering: `frontend/` module (screens + actions + reducers + components)
- [ ] 3.3 4-step reverse engineering: `mcp-feature-flags/` module
- [ ] 3.4 4-step reverse engineering: `mcp-rag-search/` module
- [ ] 3.5 4-step reverse engineering: `scripts/` + `simulators/` (data pipeline)
- [ ] 3.6 4-step reverse engineering: `n8n-workflows/` (automation layer)

Each spec → `docs-new/specs/<module>-spec.md` with: Overview / Decision Table / Sequence Diagram / Edge Cases / Open Questions / Suggested Tests

## Phase 4 — AGGREGATE

- [ ] 4.1 Synthesize Stage 1 findings + reverse-eng specs → `homework-m6/stage3-living-docs/stage3-synthesis.md`
- [ ] 4.2 Build `project-index.json` at repo root (machine-readable map)
- [ ] 4.3 Assemble new docs structure:
  - Copy ✅ items as-is from project-data/ (ADRs, API docs, page docs, features, runbooks)
  - Copy 🔄 items with TODO markers (architecture.md, glossary, etc.)
  - Add new specs from reverse engineering
  - Add README.md as index
- [ ] 4.4 Move 📦 + ❌ items to `docs-archived-2026-06-08/`
- [ ] 4.5 Remove duplicate `docs/project-data/` (it's an exact copy of root `project-data/`)

## Phase 5 — AUTOMATE

- [ ] 5.1 Install `update_project_index.py` to `.claude/scripts/`
- [ ] 5.2 Adapt WATCH_PATHS to: backend/, frontend/src/, mcp-feature-flags/, mcp-rag-search/, scripts/
- [ ] 5.3 Test standalone: `python3 .claude/scripts/update_project_index.py`
- [ ] 5.4 (Optional) Configure PostToolUse hook in `.claude/settings.local.json`
- [ ] 5.5 Update CLAUDE.md with two sections:
  - "⭐ START HERE — repo navigation"
  - "⭐ Keeping project-index.json current — MANDATORY"
- [ ] 5.6 Copy all Stage 3 artifacts to `homework-m6/stage3-living-docs/`

## Time estimate

- Phase 3: ~40-60 min (6 modules × 4-step reverse eng)
- Phase 4: ~20-30 min
- Phase 5: ~15-20 min
- **Total: ~75-110 min**

## Open questions for the user

- The duplicate `docs/project-data/` — should I just remove it or archive it?
- `docs/M6/` (course materials we downloaded) — leave as-is or exclude from new docs structure?
- `homework/`, `M3/`, `M4-materials/` — these are course artifacts, not project code. Exclude from project-index.json?
