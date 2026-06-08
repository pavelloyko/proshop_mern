# Tools Catalog — AI Code Review (май 2026)

> Сравнение 5 инструментов из темы 6.1. Данные: Signal65 study (Mar 2026) + changelog вендоров май 2026.

---

## 1. GitHub Copilot Code Review

**Что это:** AI code review, встроенный в GitHub Copilot Business/Enterprise. С марта 2026 — agentic-архитектура (читает файлы вне diff, трейсит cross-file зависимости). С мая 2026 — severity labels (High/Medium/Low) + grouped comments.

**Цена:** $10/мес Pro, $19/user Business, $39/user Enterprise.

**Метрики (полный набор):**
- **F1: 44.5%** (Qodo benchmark, самый низкий среди 5 tools)
- **Precision: 37.8%¹** на F1-датасете (выведено) / **64.35%** на Signal65-датасете (10× больше FP, чем у CodeRabbit, 41 FP vs 4)
- **Recall (bug catch rate): 54%** (Qodo benchmark, поймал 54 из 100 багов)
- Интерпретация: ловит много, но 2 из 3 замечаний шум → alert fatigue. См. секцию «Как читать метрики» ниже.

**Сильные стороны:**
- Входит в Copilot Business — ничего не нужно докупать
- Самый быстрый (~30 сек/PR)
- Agentic rewrite (Mar 2026): tool-calling, читает imports, traces deps
- Severity labels (May 12, 2026): удобная приоритизация
- Grouped comments: один комментарий на все occurrences одного паттерна

**Минусы:**
- Только GitHub (не GitLab, не Bitbucket)
- Самый высокий FP rate среди 5 tools
- Поверхностный diff-only без context-aware depth

**Когда использовать:** команда уже на Copilot Business и нужен baseline без доп. затрат. Не как единственный слой — как floor.

**Официальная дока:** https://github.com/features/copilot

---

## 2. CodeRabbit

**Что это:** Специализированный AI reviewer для Pull Requests. Лидер рынка по распространённости (2M+ репо, 13M+ ревью). Глубоко интегрирован в GitHub / GitLab / Bitbucket / Azure DevOps.

**Цена:** $12-24/seat/мес (Pro). Free для OSS.

**Метрики (полный набор):**
- **F1: 51.5%** (Signal65, Mar 2026)
- **Precision: 95.88%** (Signal65: 93 true positives, 4 FP — топ-2 индустрии)
- **Recall: 35.2%¹** (выведено из F1 и Precision; поймал ~35 из 100 багов)
- Интерпретация: топ по чистоте сигнала, но ловит меньше Copilot'а. Trade-off в пользу adoption: разработчики читают каждый комментарий.
- Comments per PR: 14 в среднем (vs Copilot 2-5)

**Сильные стороны:**
- **CodeRabbit Skills (May 2026):** поддержка 35+ coding agents (Claude Code, Cursor, Codex, Gemini CLI). Читает `CLAUDE.md`, `.cursorrules`, `.windsurfrules` — AI reviewer знает контракт команды
- **Change Stack (May 7, 2026):** layer-by-layer walkthrough с auto sequence diagrams + ERD
- **Issue Planner (Feb 2026):** анализирует issue → генерирует план изменений → передаёт в Cursor/CC
- Multi-platform: GitHub, GitLab, Azure DevOps, Bitbucket
- Высокая precision при хорошем recall (лучший баланс среди SaaS-tools)

**Минусы:**
- Не CC-native (нет native integration с Claude Code workflow)
- Больше комментариев, чем Cursor BugBot (может создавать noise при слабом промпт-тюнинге)

**Когда использовать:** default-выбор для команд на GitHub/GitLab, особенно если команда использует несколько AI-инструментов (CodeRabbit Skills читает все их конфиги).

**Официальная дока:** https://docs.coderabbit.ai

---

## 3. Qodo Merge (Qodo 2.0)

**Что это:** Multi-agent AI code review platform с встроенной генерацией тестов. Ранее CodiumAI. Qodo 2.0 (Feb 2026) — multi-agent архитектура: отдельные агенты для bugs / best-practices / performance. Open-source core: PR-Agent (Apache license).

**Цена:** $30/seat/мес (Teams), $19/user Cloud, free для individuals.

**Метрики (полный набор):**
- **F1: 60.1%** (Qodo own benchmark, Feb 2026 — **лучший среди 5 tools**, +9pp к следующему)
- **Precision: ~64%¹** на F1-датасете (выведено) / **81.13%** на Signal65 (Mar 2026, 30 FP)
- **Recall: 56.7%** (Qodo benchmark — больше реальных issues, чем у конкурентов)
- Интерпретация: лучший баланс. Multi-agent архитектура (Feb 2026) даёт depth + recall, precision вытягивается до 81% на чистом dataset.
- Но: 7.5× больше FP, чем у CodeRabbit (30 FP vs 4 на batch)

**Сильные стороны:**
- Лучший F1 — ловит больше реальных проблем
- Multi-agent архитектура (Feb 2026): концептуально совпадает с паттерном «4 специализированных агента»
- **Air-gapped on-premises** — единственный из 5 tools с этой опцией (критично для finance/healthcare/gov)
- **Встроенная test generation** — PR review + unit test gen в одной подписке
- Open-source PR-Agent: можно inspect, contribute, self-host

**Минусы:**
- Дороже ($30 vs $12-24 у CodeRabbit)
- Больше FP при high-recall режиме (нужна настройка threshold)

**Когда использовать:** regulated industries (нельзя слать код в облако) + команды, которым важен recall + команды которым нужна test generation в той же подписке.

**Официальная дока:** https://www.qodo.ai/products/qodo-merge/

---

## 4. Cursor BugBot

**Что это:** AI code reviewer от Cursor, нативно встроенный в Cursor IDE. Уникальная фича — **Cursor Blame:** различает кто написал каждую строку (AI-агент / автодополнение / человек). Лучшая precision среди всех 5 tools.

**Цена:** $40/мес поверх Cursor Pro ($20/мес) = $60/dev total.

**Метрики (полный набор):**
- **Precision: 95.95%** (Signal65, Mar 2026 — **лучшая среди 5 tools**, 71 TP / 3 FP)
- **Recall: ~27%¹** (выведено: 71 TP при ~264 общих багов в датасете)
- **F1: ~42%¹** (выведено: 2×0.9595×0.27 / (0.9595+0.27))
- Интерпретация: maximum precision, минимум шума, но ловит меньше всех. Подходит как «второй слой» поверх более recall-ориентированного tool'а.
- False positives: 3 (минимум среди всех)
- True positives: 71 (−23% к CodeRabbit's 93 — выбирает quality over quantity)

**Сильные стороны:**
- Highest precision — каждый комментарий по делу, минимум шума
- Cursor Blame: знает, какой код AI-сгенерированный (важно — AI-generated код имеет статистически больше дефектов)
- IDE-native: комментарии прямо в Cursor editor, не в GitHub UI

**Минусы:**
- Только Cursor IDE — не для команд на VS Code / IntelliJ
- Заметно меньше coverage, чем CodeRabbit/Qodo (платит coverage за precision)
- $60/dev — дороже всех при учёте Cursor Pro

**Когда использовать:** Cursor-native команды с zero-tolerance на noise (предпочитают 3 точных комментария 30 сомнительным).

**Официальная дока:** https://www.cursor.com/bugbot

---

## 5. Claude Code Action (`anthropics/claude-code-action@v1`)

**Что это:** Официальный GitHub Action от Anthropic: запускает Claude Code в headless-режиме на каждом PR. GA с 2025-08-26. Поддерживает inline-комментарии, issue-to-commit workflow, Bedrock/Vertex.

**Цена:** API tokens (не subscription). Нет фиксированного seat-cost.
- Basic review (400 lines, Sonnet 4.6): ~$0.04
- Deep review (1000 lines): ~$0.12
- Security review: ~$0.08
- 20 PR/day → ~$24/мес

**Метрики (полный набор):**
- **F1: n/a** — Anthropic не публикует benchmark
- **Precision: n/a** — зависит от промпта (правильно настроенный CLAUDE.md + ADR = высокая precision, слабый промпт = шум)
- **Recall: n/a** — зависит от max-turns / max-tokens (мало бюджета → пропустит баги)
- Интерпретация: метрики **в твоих руках** через промпт-инжиниринг. CodeRabbit eval с `/ultrareview` показал +10% recall на Opus 4.7 vs Sonnet 4.6 при stable precision.

**Сильные стороны:**
- **Full prompt control** — можно точно задать что проверять, на что не обращать внимания
- Cheapest per-PR в категории
- Поддержка Bedrock/Vertex — работает с любым планом
- Два официальных action: `claude-code-action` (general) + `claude-code-security-review` (security-focused)
- `/install-github-app` в Claude Code локально: GitHub App setup за 5 минут

**Минусы:**
- Setup ~15 минут + maintenance (vs zero-setup CodeRabbit)
- Billing через Anthropic Console — нужны budget alerts (без `max-turns` легко runaway)
- Нет встроенного dashboard / analytics

**Когда использовать:** команды на CC-stack, которые хотят полный контроль над промптом и прозрачный cost per PR. Хорошо для security-sensitive paths через отдельный `claude-opus-security.yml` workflow.

**Официальная дока:** https://github.com/anthropics/claude-code-action

---

## Как читать метрики F1 / Precision / Recall

### Сводная таблица всех метрик (для F3 Miro)

| Tool | F1 | Precision | Recall | Источник |
|---|---|---|---|---|
| **Cursor BugBot** | ~42%¹ | **95.95%** | ~27%¹ | Signal65 Mar 2026 (Precision = 71 TP / 3 FP). F1 и Recall выведены. |
| **CodeRabbit** | **51.5%** | **95.88%** | 35.2%¹ | Signal65 Mar 2026 (F1, Precision). Recall выведен из формулы F1=2PR/(P+R). |
| **Qodo 2.0** | **60.1%** | ~64%¹ / 81.13%² | **56.7%** | Qodo own bench Feb 2026 (F1, Recall). Signal65² (Precision на их датасете). |
| **GitHub Copilot CR** | 44.5% | 37.8%¹ / 64.35%² | 54% | Qodo bench (F1, Recall=bug catch). Signal65² (Precision на их датасете). |
| **Claude Code Action** | n/a | n/a | n/a | Anthropic не публикует benchmark; метрики зависят от промпта. |

> ¹ Выведено обратной арифметикой из формулы `F1 = 2 × Precision × Recall / (Precision + Recall)`. Не публичная цифра.
>
> ² Precision на Signal65 dataset ≠ precision на vendor own benchmark — это **разные датасеты** с разным составом багов. У Qodo и Copilot precision на Signal65 ВЫШЕ чем на их own F1-benchmark — потому что Signal65 содержит более «лёгкие» баги, на которых tools выдают меньше FP. **Не путать колонки.**

⚠️ **Что в Miro F3 таблице — самые «известные» цифры:** Cursor BugBot precision 95.95%, CodeRabbit F1/Precision 51.5%/95.88%, Qodo F1 60.1%, Copilot F1 44.5%. Они и были там изначально. В этом каталоге — полная картина с источниками.

---

### Откуда берутся эти метрики

Когда AI ревьюит код, он принимает решения **по каждой потенциальной проблеме**: пометить как баг или пропустить. Каждое решение попадает в одну из 4 ячеек:

| | AI сказал «баг» | AI сказал «ок» |
|---|---|---|
| **Реально баг** | TP (true positive) ✅ | FN (false negative) ❌ пропустил |
| **Реально не баг** | FP (false positive) ⚠️ ложная тревога | TN (true negative) ✅ |

Из этой матрицы выводятся **3 метрики**:

### 1. Precision (точность) — насколько чистый сигнал

Формула: `Precision = TP / (TP + FP)`

Из всего, что AI пометил как баг — какой **%** реально баги?

**CodeRabbit Precision = 95.88%** означает: из 100 замечаний 96 настоящие, **4 ложные тревоги**. Топ-показатель индустрии: разработчики не выгорают от шума.

**Copilot CR Precision = 64.35%** означает: из 100 замечаний только 64 настоящие, **36 шум**. Этого достаточно, чтобы разработчики начали игнорировать комментарии (см. `honest-risks.md` → «AI noise trains inattention»).

### 2. Recall / Bug catch rate (полнота) — сколько реально находит

Формула: `Recall = TP / (TP + FN)`

Из **всех реальных багов** в коде — какой **%** AI поймал?

**Copilot CR Bug catch rate = 54%** означает: в benchmark'е было 100 настоящих багов, AI поймал **54**, **46 пропустил**.

«Bug catch rate» = другое название recall в контексте code review benchmark'ов.

### 3. F1 score — баланс между Precision и Recall

Формула: `F1 = 2 × (Precision × Recall) / (Precision + Recall)`

Это **гармоническое среднее**, оно жёстко наказывает дисбаланс. Нельзя получить высокий F1, оптимизируя только одну метрику:

- Precision 100% + Recall 5% → F1 = **9.5%** (AI пишет только когда уверен, ловит почти ничего)
- Precision 5% + Recall 100% → F1 = **9.5%** (AI лает на всё подряд, 95% шум)
- Precision 50% + Recall 50% → F1 = **50%** (сбалансировано)

**F1 = честный показатель.** Производитель не может играть только с одной цифрой.

### Что значат конкретные числа двух главных тулов

**Copilot CR (F1 44.5% / Recall 54%)** обратной арифметикой даёт **Precision ≈ 38%**. То есть:
- Ловит 54 из 100 багов (recall = ОК)
- НО из 100 замечаний только 38 настоящие, **62 ложные тревоги** на каждые 100 комментариев
- F1 средний именно из-за низкой точности

**CodeRabbit (F1 51.5% / Precision 95.88%)** обратной арифметикой даёт **Recall ≈ 35%**. То есть:
- Из 100 замечаний 96 настоящие = **минимум шума**
- НО ловит только 35 из 100 багов (recall ниже Copilot'а)
- F1 выше потому что точность вытягивает баланс

### Trade-off — что выбирать

| Стратегия | Метрика | Когда выбирать |
|---|---|---|
| «Не отвлекать без причины» | Высокий **Precision** (CodeRabbit) | Зрелая команда, AI = вторая линия, важно не вызвать alert fatigue |
| «Лучше шум, чем пропуск» | Высокий **Recall** (Copilot CR) | Молодая команда / критичный код, AI = первая линия, важно ничего не пропустить |
| Баланс | Высокий **F1** (Qodo 2.0 = 60.1%) | Дефолт когда не уверены |

### Про Signal65 как источник

**Signal65** (signal65.com) = независимая аналитическая компания, специализирующаяся на benchmark-исследованиях developer tools и AI products. Их методология: стандартизированный dataset реальных Pull Request'ов с известными багами, прогнанный через каждый tool в одинаковых условиях.

В марте 2026 они опубликовали сравнительное исследование 6+ AI code review tools (Cursor BugBot, CodeRabbit, Greptile, Qodo Merge, Copilot CR + others).

⚠️ **Нюанс:** часть исследований Signal65 спонсируется vendor'ами (CodeRabbit ссылается на это study на своём сайте). Однако методология открыта и dataset воспроизводим, поэтому цифры обычно держатся при peer review. Источник публичный, можно цитировать.

---

## Signal/Noise ranking (Signal65 study, Mar 2026)

Рейтинг по precision (% комментариев, которые реально указывают на проблему):

| # | Инструмент | Precision | FP count | True Positives |
|---|---|---|---|---|
| 1 | **Cursor BugBot** | **95.95%** | 3 | 71 |
| 2 | **CodeRabbit** | **95.88%** | 4 | 93 |
| 3 | Greptile | 86.36% | — | — |
| 4 | Qodo Merge | 81.13% | 30 | — |
| 5 | **GitHub Copilot CR** | **64.35%** | 41 | — |

По F1 (баланс precision + recall):

| # | Инструмент | F1 |
|---|---|---|
| 1 | **Qodo 2.0** | **60.1%** |
| 2 | CodeRabbit | 51.5% |
| 3 | GitHub Copilot CR | 44.5% |

> Нет одного «лучшего» инструмента: Cursor BugBot топ-precision, Qodo топ-recall. Выбор зависит от того, что дороже — шум или пропущенные баги.

---

## Industry shift 2026

До 2025 вендоры соревновались за «больше findings». В 2026 — за **signal-to-noise**: кто найдёт меньше, но точнее. CodeRabbit и Cursor BugBot показывают 95%+ precision при разном уровне coverage. Copilot CR с 64% precision создаёт в 10× больше шума — и именно шум убивает adoption (см. `honest-risks.md`).
