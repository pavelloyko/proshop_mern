# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⭐ START HERE — repo navigation

**ALWAYS read `project-index.json` FIRST** at the beginning of every session.

It contains:
- `subprojects` — annotated map of all subprojects (backend, frontend, MCP servers, scripts, n8n)
- `system_folders` — .claude/, project-data/, docs/, uploads/ with purpose
- `hard_rules` — project rules you must follow
- `ai_routing` — which MCP tools to use for which questions
- `filesystem_tree` — full directory tree (auto-updated, depth 4)

This is faster than find/tree/ls, accurate, and machine-readable.

## ⭐ Keeping project-index.json current — MANDATORY

**ALWAYS** update `project-index.json` when you:
- create or delete files/folders
- rename files or folders
- change the purpose of a subproject

How: `python3 .claude/scripts/update_project_index.py`
Or: automatically via PostToolUse hook (see .claude/settings.local.json)

For 4-step analysis of new modules — see examples in project-data/specs/ (or homework/M6/stage3-living-docs/specs/).

## Design rules: see ./DESIGN.md

When generating any UI component or modifying styles:
1. Read DESIGN.md before writing code
2. Use only colors defined as CSS variables — never raw hex
3. Follow spacing scale (multiples of 8px only)
4. Implement all interactive states: hover, focus, loading, empty
5. Font: Manrope (not Inter)

## Overview

ProShop is a full-stack eCommerce platform (MERN: MongoDB, Express, React, Node.js) with Redux state management. It supports product browsing with search/pagination, shopping cart, user auth (JWT), order management, admin CRUD for products/users/orders, product reviews, and PayPal payment integration.

## Commands

```bash
# Install all dependencies (backend + frontend)
npm install && cd frontend && npm install && cd ..

# Run backend (:5001) + frontend (:3000) concurrently
npm run dev

# Run backend only (with nodemon hot-reload)
npm run server

# Run frontend only
npm run client

# Build frontend for production
cd frontend && npm run build

# Seed database with sample data
npm run data:import

# Wipe all database data
npm run data:destroy
```

No test suite is configured. No linter config exists beyond the default `react-app` ESLint preset in frontend.

## Tech Stack

- **Backend**: Node.js (requires v16), Express 4, Mongoose 5, JWT (jsonwebtoken), bcryptjs, multer (file uploads)
- **Frontend**: React 16, React Router 5, Redux 4 + Redux Thunk, React-Bootstrap 1, Axios, react-paypal-button-v2
- **Database**: MongoDB (runs in Docker on localhost:27017, db name: `proshop`)
- **Module system**: ES Modules in backend (`"type": "module"` in package.json), `.js` extension required in imports

## Architecture

### Backend (`backend/`)

- **Entry point**: `backend/server.js` — loads env, connects to DB, mounts JSON parser, routes, static files, error middleware
- **Routes** (`backend/routes/`) — Express routers, each mounted at `/api/<resource>`. Use `protect` and `admin` middleware from `authMiddleware.js` for guarded endpoints
- **Controllers** (`backend/controllers/`) — one file per resource, all wrapped in `express-async-handler`. Each function has a `@desc`, `@route`, `@access` JSDoc comment
- **Models** (`backend/models/`) — Mongoose schemas: `Product` (with embedded `Review` sub-schema), `User`, `Order` (with embedded `OrderItem`)
- **Middleware** (`backend/middleware/`): `authMiddleware.js` (`protect` validates JWT Bearer token, `admin` checks `isAdmin`), `errorMiddleware.js` (404 handler + global error handler)
- **Data** (`backend/data/`) — seed data arrays for `users.js` and `products.js`, consumed by `seeder.js`
- **Config** (`backend/config/db.js`) — MongoDB connection with deprecated option flags

### Frontend (`frontend/`)

- **Entry point**: `frontend/src/index.js` → wraps `App` in `Provider` (Redux store)
- **Routing**: `App.js` uses React Router 5 `<Route>` components (no `Switch`, no lazy loading)
- **Redux store** (`frontend/src/store.js`): `combineReducers` with 20+ reducers. Cart/auth state persisted to `localStorage` as initial state. Middleware: `redux-thunk`. DevTools enabled via `redux-devtools-extension`
- **Actions** (`frontend/src/actions/`) — one file per domain (products, users, orders). Each action follows the `REQUEST / SUCCESS / FAIL` triple pattern. Authenticated requests attach `Authorization: Bearer <token>` header from `getState().userLogin.userInfo`
- **Reducers** (`frontend/src/reducers/`) — standard switch/case on action types
- **Constants** (`frontend/src/constants/`) — action type strings, one file per domain
- **Screens** (`frontend/src/screens/`) — page-level components (one per route)
- **Components** (`frontend/src/components/`) — reusable UI pieces (Header, Footer, Product card, Rating, etc.)
- **Proxy**: `frontend/package.json` has `"proxy": "http://127.0.0.1:5001"` so Axios calls to `/api/*` forward to backend in dev mode

### API Routes

| Route prefix | Resource | Auth |
|---|---|---|
| `/api/products` | Products (CRUD, search, reviews, top-rated) | Public / Admin |
| `/api/users` | Users (auth, profile, admin CRUD) | Public / Private / Admin |
| `/api/orders` | Orders (create, pay, deliver, list) | Private / Admin |
| `/api/upload` | Image upload (multer) | Private / Admin |
| `/api/config/paypal` | Returns PayPal client ID | Public |

## Conventions

- Backend uses `colors` library for console output (`console.log('msg'.yellow.bold)`)
- Error handling: controllers throw via `express-async-handler`, caught by global `errorMiddleware`
- Error responses in frontend actions use pattern: `error.response?.data?.message || error.message`
- Auth token stored in Redux state + localStorage under key `userInfo`
- Cart stored in localStorage under keys `cartItems` and `shippingAddress`
- Product images served from `/uploads/` directory (multer destination) and `/images/` in `frontend/public/`
- Admin routes prefixed with `/admin/` in frontend URL structure
- Models use `timestamps: true` for automatic `createdAt`/`updatedAt`

## What NOT to Do

- Do not use Node.js newer than v16 — the project's `webpack 4` and `buffer-equal-constant-time` are incompatible with newer Node versions
- Do not remove `.js` extensions from backend imports — ES Modules require explicit extensions
- Do not change the port without updating both `.env` (`PORT`) and `frontend/package.json` (`proxy`) — they must match
- Do not run seeder while the app is live — it wipes and replaces all data
- Port 5000 may be occupied by macOS AirPlay Receiver — use port 5001 or disable AirPlay

## Manual Additions (not inferable from code)

### Environment Setup Gotchas
- MongoDB must be running before `npm run dev` — the server crashes with an unhandled DB connection error if Mongo is unavailable. Docker command: `docker start <mongo_container>` or `docker run -d -p 27017:27017 --name mongo mongo:7`
- After switching Node.js versions (via nvm), delete `node_modules` in both root and `frontend/` and reinstall — native deps won't match otherwise
- npm cache permission errors on macOS: run `sudo chown -R $(whoami) ~/.npm && npm cache clean --force` before installing

### Deployment / Infrastructure Notes
- This project was designed for Heroku deployment (`Procfile` + `heroku-postbuild` script). For modern deployment, the `heroku-postbuild` script handles frontend build automatically
- `react-scripts 3.4.3` (webpack 4) is pinned and cannot be upgraded without migrating to webpack 5, which would require significant config changes across the entire frontend build pipeline

### When Adding New Backend Features
- After adding a new Mongoose model, update `backend/seeder.js` to include it in the `importData`/`destroyData` functions so the seed workflow stays consistent
- After adding a new admin route, remember to chain `.post(protect, admin, ...)` or equivalent — there is no route-level guard, auth is per-handler
- New Redux state slices must be added to `combineReducers` in `store.js` AND corresponding `localStorage` persistence logic if state should survive page refresh

## Manual Review Additions

### Team Conventions
- Branches: `feature/<desc>`, `fix/<desc>`. Commits: imperative mood, English
- PR prefix with scope: `[frontend]`, `[backend]`, `[fullstack]`
- Before PR: `npm run dev` starts clean, no console.log left, no hardcoded URLs

### Local Gotchas
- react-router-dom v5 — use `useHistory()`, NOT v6 `useNavigate`/`<Routes>`
- Route order matters in Express — specific paths (`/top`) must be registered before param routes (`/:id`)
- `mongoose` v5 — `model.remove()` works here, do not "modernize" to v6+ syntax
- `frontend/src/bootstrap.min.css` is vendored — never edit directly, use `index.css` for overrides
- Product image upload writes to `/uploads/` at project root — must exist and be writable

### Deployment Quirks
- `heroku-postbuild` builds frontend automatically. For other hosts: `cd frontend && npm run build`, then set `NODE_ENV=production`
- Production needs MongoDB Atlas (not local Docker) — set `MONGO_URI` to Atlas connection string

## Поиск по документации продукта proshop_mern (search-docs MCP)

- При любых вопросах про функционал, фичи, архитектуру, ADR, runbooks, incidents — СНАЧАЛА использовать `search_project_docs` MCP tool.
- Это быстрее и возвращает релевантные чанки с метаданными (source_file, title, score, snippet).
- ТОЛЬКО если vector search не дал нужных результатов или нужно полное содержимое файла из метаданных найденного чанка → fallback на grep+read.
- НЕ начинать с grep+read по проекту — медленно и дорого по токенам.

## Управление feature flags (feature-flags MCP)

- Когда пользователь спрашивает статус фичи ("какой статус у gift_message?", "включена ли search_v2?") — вызывать feature-flags MCP `get_feature_info`, не читать `features.json` напрямую.
- Когда пользователь хочет изменить статус ("включи фичу X", "переведи Y в Testing", "поставь трафик 25%") — вызывать соответствующие tools (`set_feature_state`, `adjust_traffic_rollout`). Никогда не редактировать `backend/features.json` вручную через Edit/Write.
- Когда пользователь просит список всех фич — использовать `list_features` tool, не grep'ать файл.

### AI Collaboration Preferences
- Explanations in Russian, code and comments in English
- Do not refactor beyond task scope — this is a legacy learning project
- Follow existing patterns (REQUEST/SUCCESS/FAIL triples, folder structure) — consistency over modern practices
- When adding features touching multiple files, list all affected files before writing code
