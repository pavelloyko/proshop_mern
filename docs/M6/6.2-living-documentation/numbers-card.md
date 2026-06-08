# F-N: Living Documentation — ключевые цифры

> Карточка ключевых чисел и фактов для темы 6.2. Используй для быстрой ссылки
> на уроке и после.

---

## Стандарт AGENTS.md

| Факт | Цифра / дата | Источник |
|---|---|---|
| Дата передачи AGENTS.md в Linux Foundation / AAIF | 9 декабря 2025 | Linux Foundation AAIF announcement |
| Репозиториев с AGENTS.md на момент передачи | 60K+ | agentsmd.com/spec |
| Инструментов, поддерживающих AGENTS.md | 8 (Codex, Copilot, Cursor, Windsurf, Amp, Devin, Jules, Aider) | agentsmd.com |
| AGENTS.md файлов в internal репо OpenAI | 88 | публично раскрытые данные об инфраструктуре |

---

## Оптимальный размер CLAUDE.md / AGENTS.md

| Источник | Рекомендация |
|---|---|
| Nate Herk (практик Claude Code) | ~87 строк |
| Cole Medin (практик multi-agent) | ~233 строки |
| Anthropic официально | < 200 строк |
| Vercel (анти-эталон, bloated) | ~19 000 токенов |

**Правило:** держи в диапазоне 87–233 строк.

Почему: ETH Zurich SRI Lab (2025) — AGENTS.md >200 строк увеличивает inference cost
>20% и в 5 из 8 настроек SWE-bench Lite / AGENTbench снижает % решённых задач.

Chroma Research (2025) — на 18 моделях точность деградирует с 95% до 60-70% по
мере роста длины input.

---

## RAG Freshness Rot

| Факт | Цифра | Источник |
|---|---|---|
| Корпоративных RAG-проектов, падающих из-за stale sources (не из-за слабого retrieval) | ~60% | Stanford AI Group |
| Корпоративных AI-инициатив, провальных из-за RAG | 51% | S&P Global / AIMUG |
| Корпоративных KB, содержащих конфликтующую информацию | 47% | Fini Labs / Gartner 2025 |
| Эскалаций с root cause = stale content | 31% | S&P Global / AIMUG |

---

## MTTU и freshness SLO

| Метрика | Значение | Контекст |
|---|---|---|
| MTTU (Mean Time To Update) target для AI-trust | < 24h | Индустриальный стандарт для AI-grounded систем |
| Schedule-driven окно staleness | до 24h | При cron-обновлении раз в сутки |
| Event-driven (CDC) окно staleness | секунды - минуты | Debezium / RisingWave / Pathway |

**Правило freshness:** «Until freshness is someone's explicit job, it will be
nobody's job» — Glen Rhodes, 2026-03-05.

---

## Масштаб legacy без документации (реальный enterprise-кейс)

Стартовая точка крупного консалтинг-кейса на 100+ микросервисах:

| Метрика | Значение | Industry baseline |
|---|---|---|
| READMEs в сервисных проектах | 0 / 108 | обычно < 50% |
| Файлов с XML-doc | < 3% | target: 100% на public APIs |
| ADR (Architecture Decision Records) | 0 | quarterly cadence для крупных решений |
| Architecture guides | 2 | по одному на bounded context |

Последствия: новые инженеры тратят 1-2 недели чтобы что-то отгрузить,
архитектурные решения живут в tribal memory, AI-инструменты деградируют без
grounding context.

> «AI tools degrade in quality without context to ground them.»

---

## Контекст и длина контекста

| Факт | Цифра | Источник |
|---|---|---|
| Максимальный эффективный контекст для code navigation без RAG | ~4MB кодовой базы | Sourcegraph / Google research 2026 |
| При больших кодовых базах: long context vs code graph + RAG | code graph обязателен | Sourcegraph / Google research 2026 |

**Тезис:** Long context = multiplier на качество RAG, не замена. Для кодовых баз
>4MB code graph + RAG остаются обязательными даже при 1M-token context.

---

## Формула обоснования

Cole Medin (практик multi-agent систем):

> «1 строка плохого PRD = 1000 строк плохого кода»

Инвестиция в качество документации (AGENTS.md, ADR, inline constraints) окупается
через снижение объёма переработок от неправильно написанного кода.

---

## Риски документации: числа

| Риск | Число | Источник |
|---|---|---|
| Bloated AGENTS.md: рост inference cost | > 20% | ETH Zurich SRI Lab 2025 |
| Bloated AGENTS.md: снижение % решённых задач | 5 из 8 настроек SWE-bench | ETH Zurich SRI Lab 2025 |
| Doc overengineering (GitHub Spec Kit): % лимита CC на спеки | 60-80% 5-часового лимита | @the_ai_architect_chat 2025-12-10 |
| Типичный gap между line coverage и MSI у AI-тестов | 30-35 пунктов | Generative Specification whitepaper 2026 |
