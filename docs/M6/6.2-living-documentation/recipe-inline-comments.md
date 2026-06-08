# Рецепт: inline-комментарии как локальные правила для LLM

> Паттерн для опасных мест кода, где глобальные rules в AGENTS.md / CLAUDE.md
> теряются в большом контексте. Применяется к env-config, infra, deprecated API,
> security-ограничениям и регуляторным требованиям.

---

## Почему inline-комментарии работают лучше глобальных правил

Проблема с глобальными rules в AGENTS.md или CLAUDE.md: LLM имеет **bias к краям
промта** — модель значительно лучше помнит первые и последние строки контекста,
середина деградирует. На большом контексте правило из AGENTS.md на строке 150
может просто не применяться агентом при редактировании конкретного файла.

Локальный inline-комментарий рядом с критическим кодом:
- **всегда виден агенту** при редактировании этого файла (находится в прямой близости к редактируемому коду)
- **специфичен для контекста** (объясняет именно ЭТО ограничение, а не абстрактное правило)
- **не дублирует глобальные соглашения** (для этого есть AGENTS.md)

Источник паттерна: обсуждение в сообществе AI-разработчиков, декабрь 2025.

---

## Формат комментария-якоря

```python
# CONSTRAINT: <что нельзя делать и почему в одной строке>
# CONTEXT:    <почему именно здесь это важно, откуда взялось правило>
# ASSUMPTION: <что агент предполагает и что реально есть>
```

**Правило первой строки:** начинать с `CONSTRAINT:` (Do NOT ...) — это
отсекает статистически самый частый неправильный паттерн модели.

**Почему negative-constraint:** LLM обучены на огромном корпусе кода, где
определённые паттерны встречаются намного чаще других. Запрет конкретного
действия точнее, чем описание правильного.

---

## Пример 1 — Dockerfile vs docker-compose env_file

**Ситуация:** AI-агенты упорно добавляют `ARG`-переменные в Dockerfile вместо
использования `env_file` из `docker-compose.yaml`. Это стандартный паттерн для
Docker, поэтому модели его воспроизводят.

```yaml
# docker-compose.yaml

services:
  app:
    build: .
    # CONSTRAINT: env_file IS source of truth for ALL environment variables.
    # Do NOT add ARG declarations to Dockerfile — breaks layered config override.
    # CONTEXT: agents historically add ARGS here — this is wrong for this project.
    # ASSUMPTION: docker-compose.yaml is the single source for environment variables.
    env_file:
      - .env
```

```dockerfile
# Dockerfile

FROM node:18-alpine

# CONSTRAINT: Do NOT add ARG for environment variables.
# Use docker-compose.yaml env_file section instead.
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "server.js"]
```

**Что проверить:** дать агенту задачу «добавь переменную DATABASE_URL в конфигурацию».
Если комментарий работает: агент добавит в `.env` + `env_file`, не в ARG.

---

## Пример 2 — MCP-сервер feature flags (proshop_mern)

```python
# mcp/feature_flags_server.py

# CONSTRAINT: env_file Docker Compose IS source of truth.
# Do NOT add ARGS to Dockerfile — breaks layered configs.
# ASSUMPTION: agents historically add ARGS — explicit guard.

import os
from mcp.server import FastMCP

app = FastMCP("feature-flags")

@app.tool()
def get_feature_flag(flag_name: str) -> bool:
    """
    Get feature flag value.

    CONSTRAINT: Do NOT hardcode flag defaults in this function.
    All defaults must come from environment variables.
    Source: .env file via docker-compose env_file.
    """
    return os.getenv(flag_name, "false").lower() == "true"
```

---

## Пример 3 — Deprecated API endpoint

```python
# backend/routes/userRoutes.py

# DEPRECATED: /api/users/profile endpoint removed in v2.
# CONSTRAINT: Do NOT add new logic to this route.
# CONTEXT: Clients still hitting it — keep 301 redirect to /api/v2/users/me
# New code: use /api/v2/users/ prefix

@router.get("/profile")  # DEPRECATED — 301 redirect only
async def legacy_profile_redirect():
    return RedirectResponse(url="/api/v2/users/me", status_code=301)
```

---

## Когда использовать inline vs глобальные правила

| Ситуация | Где писать |
|---|---|
| Ограничение специфично для одного файла / модуля | Inline в файле |
| Ограничение касается нескольких файлов, но одной системы (infra, auth) | Inline в каждом + краткое упоминание в AGENTS.md |
| Соглашение для всего проекта (naming, commit style) | Только в AGENTS.md |
| Критическое ограничение в опасном месте (PII, payment, security) | **Оба**: AGENTS.md глобально + inline в конкретном файле |
| Временное ограничение (feature flag, migration period) | Inline с датой: `# CONSTRAINT until 2026-08-01:` |

**Практическое правило:** если агент ошибся в этом месте хотя бы один раз после
глобального правила — добавить inline. Глобальное правило не убирать.

---

## Рецепт: 5 шагов внедрения

1. **Выделить 5-10 «опасных мест»** в проекте, где агент ошибается чаще всего:
   env-конфигурация, deprecated APIs, infra (Dockerfile/compose),
   security-ограничения (PII, auth, rate limits), регуляторные требования.

2. **На каждое место написать комментарий-якорь** в формате:
   ```
   # CONSTRAINT: <запрет> — <причина одной строкой>
   # CONTEXT:    <почему именно здесь>
   # ASSUMPTION: <что агент обычно предполагает>
   ```

3. **Negative-constraint первой строкой** — `Do NOT add / Do NOT use / Never...`

4. **Не дублировать в AGENTS.md** весь inline-комментарий. В AGENTS.md — только
   общую ссылку: «Детальные ограничения для infra-файлов: смотри inline в Dockerfile
   и docker-compose.yaml».

5. **Проверить эффективность:** попросить агента выполнить задачу, которая раньше
   приводила к ошибке. Если ошибка повторяется — комментарий слишком абстрактный
   или расположен слишком далеко от редактируемого кода.

---

## Очистка от лишних комментариев

AI-агенты сами генерируют много WHAT-комментариев (объясняющих очевидное действие).
Они засоряют контекст и снижают вес важных CONSTRAINT-комментариев.

Промпт для очистки после сессии:
```
Удали из этого файла: лишние комментарии-WHAT (объясняющие очевидное действие),
избыточные try/catch-обёртки, касты к any, стилистические несоответствия.
Оставь только comment-WHY и comment-CONSTRAINT.
```

**Важно:** проводить очистку после каждой существенной сессии с агентом, не
накапливать.

---

## Подводные камни

**Over-commenting:** если каждая строка содержит CONSTRAINT, агент начинает их
игнорировать (аналог alert fatigue). Выбирать только действительно опасные места —
те, где ошибка дорого стоит или уже случалась.

**Sync rot:** если код переезжает (рефакторинг, переименование модулей), комментарии
могут потерять контекст или оказаться рядом с другим кодом. После крупного
рефакторинга: пройтись по CONSTRAINT-комментариям и проверить актуальность.

**Абстрактные комментарии не работают:** `# CONSTRAINT: следуй соглашениям проекта`
бесполезен. Комментарий должен описывать конкретное действие, которое нельзя делать
в конкретном месте.

---

## Дополнительные практики inline-документации для AI

| Практика | Что | Когда |
|---|---|---|
| **WHY not WHAT** | Описывать intent / assumption, не действие | Всегда при нетривиальном коде |
| **Breadcrumb comments** | `# CONTEXT: ...` / `# ASSUMPTION: ...` как якоря для reasoning | Сложная бизнес-логика |
| **Function names = docs** | `validateUserEmailAndSendConfirmation()` > `processEmail()` | Именование новых функций |
| **Locality** | Комментарий непосредственно над кодом, к которому относится | GitHub Copilot и другие: ближайший предшествующий комментарий имеет наибольший вес |
| **Skip trivial** | Не комментировать очевидное — снижает signal/noise | При ревью кода |

---

## Внешние ссылки

- Glean AI (2025-12): «Describe intent and assumptions, not actions»
- GitHub Copilot Docs 2026: locality принцип — ближайший предшествующий комментарий
- Inferable.ai: «Negative constraints are more effective than positive rules»
- arXiv 2025-12-19: CAV experiment — trivial comment deactivation иногда улучшает
  translation quality (модели internalize comment types как latent concepts)
