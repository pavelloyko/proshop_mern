# Topic 6.2 — Living Documentation

> Модуль 6, Тема 2. Живая документация как infrastructure-задача.

---

## Что в этой папке

| Файл | Что внутри |
|---|---|
| `README.md` | Этот файл. Навигация и главные идеи темы. |
| `agents-md-claude-md-standard.md` | Стандарт AGENTS.md / CLAUDE.md: история, формат, оптимальный размер, примеры. |
| `recipe-inline-comments.md` | Рецепт: inline-комментарии как локальные правила для LLM. Когда работают лучше глобальных rules. |
| `numbers-card.md` | Карточка ключевых цифр и фактов темы (F-N Numbers reference). |

---

## Главные идеи

- **Документация = infrastructure-задача reliability, не writing.** Stale docs производят уверенные галлюцинации. Semantic similarity не видит времени: устаревший документ ранжируется так же, как свежий. 60% RAG-проектов падают из-за stale sources, не из-за слабого retrieval.

- **AGENTS.md / CLAUDE.md / project-index.json — новый стандартный стек 2025-2026.** AGENTS.md под Linux Foundation / Agentic AI Foundation с декабря 2025, 60K+ репозиториев, поддерживается Codex, GitHub Copilot, Cursor, Windsurf, Amp, Devin, Jules, Aider. Claude Code читает CLAUDE.md. Workaround для совместимости: symlink `ln -s AGENTS.md CLAUDE.md`.

- **Multi-level стек (8 слоёв) обязателен для AI-grounded проектов.** Один слой (только README или только OpenAPI) недостаточен. Эффективный setup 2026: code-level XML-doc / docstrings → README → API auto-spec → catalog-info → ADR → runbooks → wiki → AI-context (AGENTS.md / CLAUDE.md / project-index.json). Все слои синхронизируются через PR-триггеры. Реальный enterprise-кейс с 100+ микросервисами: стартовая точка = 0 READMEs, <3% XML-doc, 0 ADR.

- **Event-driven docs update обязателен для AI-сценариев.** Schedule-driven оставляет окно до 24h, в течение которого агент уверенно отвечает по устаревшим данным. Решение: CDC + инкрементальная индексация. Schedule-driven рационален только при малом корпусе (менее тысяч документов) или при допустимом MTTU больше суток.

---

## После урока — что читать первым

1. `agents-md-claude-md-standard.md` — стандарт AGENTS.md: история, формат, размер, примеры на proshop_mern
2. `recipe-inline-comments.md` — конкретный рецепт для опасных мест кода
3. `numbers-card.md` — все ключевые цифры для быстрой ссылки

---

## Дополнительные ссылки

- **agentsmd.com/spec** — официальный сайт стандарта AGENTS.md (Linux Foundation / AAIF)
- **Anthropic CLAUDE.md docs** — https://docs.anthropic.com/en/docs/claude-code/memory
- **Linux Foundation Agentic AI Foundation (AAIF)** — https://agentaiif.org/
- **GitHub: AGENTS.md examples in OSS repos** — поиск `filename:AGENTS.md` на GitHub
- **project-index.json паттерн** — пример в `proshop_mern/project-index.json` (учебный репо курса)
