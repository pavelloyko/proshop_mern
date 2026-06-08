# Honest Risks — AI Code Review в Production

> 5 задокументированных рисков с источниками. Читать перед rollout.

---

## Риск 1: CRA-only PRs — низкий merge rate и высокий abandonment

**Что происходит:**

Исследование MSR 2026 (arXiv 2604.03196) проанализировало 3 109 PRs из AIDev проекта. PRs, открытые Code Review Agent (CRA) без human-oversight, имеют merge rate **45.2%** против **68.4%** у human-authored PRs. Abandonment rate: **34.9% у CRA** против **21.6% у human**. 60.2% закрытых CRA-PRs находились в signal range 0-30 (по принятым в репо метрикам качества).

**Как митигировать:**

AI code review должен дополнять, а не заменять человека-ревьюера. Практический паттерн: AI review — первый слой (быстрый скрининг за секунды), human review — второй слой (domain context, business logic, намеренные «хаки»). Branch protection: минимум 1 human approval даже при наличии AI-ревью. Без human oversight → production risk.

**Источник:** arXiv 2604.03196, MSR 2026

---

## Риск 2: Conservative trap — 0% FP при 80% miss rate

**Что происходит:**

BSWEN benchmark (март 2026): 133 evaluation cycles на Claude Opus 4.6. Результат: zero false positives. Звучит идеально — пока не смотришь на recall: **пропущено 80% реальных issues**. Модель была настолько conservative, что «безопасно» молчала о большинстве реальных проблем.

Аналогичный паттерн — CR-Bench (ICLR 2026): Reflexion-based agent показывает высокий recall, но «catastrophically low SNR». Это фундаментальный trade-off, не баг конкретной версии.

**Как митигировать:**

«Zero FP» в marketing-материалах вендора не означает хорошего recall. При выборе инструмента смотреть на F1, не только precision. Для critical code paths — multi-model strategy: Stage 1 (Claude / Sonnet) = high-confidence findings, Stage 2 (дополнительный model или human) = coverage. Измерять recall на своём репо отдельно.

**Источник:** BSWEN benchmark, Mar 2026; CR-Bench, ICLR 2026

---

## Риск 3: AI noise trains inattention — 400 wasted interruptions/week

**Что происходит:**

Математика от Tianpan (Apr 2026): 20 комментариев × 40% noise × 50 PRs/week = **400 потраченных впустую прерываний в неделю**. При таком уровне шума инженеры вырабатывают dismiss reflex — начинают игнорировать все комментарии, включая реально важные. Через 3-4 месяца tool колапсирует в adoption: команда либо отключает AI review, либо кликает «approve all» не читая.

**Как митигировать:**

Метрика успеха — не FP rate в вакууме, а **comment action rate >60%** (доля комментариев, по которым разработчик что-то сделал: исправил / создал задачу / явно отклонил с причиной). Ниже 40% action rate = net negative. Для достижения >60%: пилот 2-3 команды → 6-8 недель сбора метрик → тюнинг промпта / порогов → только потом expansion. Без этого этапа → adoption collapse за 3-4 месяца.

**Источник:** Tianpan, «AI Code Review as noise that trains inattention», Apr 2026

---

## Риск 4: Diff-only context blindness

**Что происходит:**

Конкретный случай (Jangwook, Apr 2026): Claude в diff-only режиме поставил флаг «нужен `memo()`» на компонент. Проблема: компонент уже был обёрнут в `memo()` на уровень выше в родительском файле, который не входил в diff. False positive из-за отсутствия context.

Более широкая проблема: SWE-PRBench (arXiv 2603.26130, 2026) показывает, что 8 frontier-моделей детектируют только **15-31% human-flagged issues** при работе в diff-only режиме. Принципиальное ограничение подхода.

**Как митигировать:**

Для context-aware review использовать инструменты с codebase indexing: Greptile (precision 86.36%), CodeRabbit Change Stack (May 2026). Явно добавлять в промпт: «check parent components», «check if this pattern already exists in the codebase». При critical findings — human reviewer проверяет broader context вручную. Не полагаться на diff-only review для architectural decisions.

**Источник:** Jangwook blog, Apr 2026; SWE-PRBench, arXiv 2603.26130

---

## Риск 5: Agent Teams — 2.5-4× стоимость + edit conflicts

**Что происходит:**

Anthropic Agent Teams (Feb 2026, экспериментально): каждый mate — полный Claude Code-инстанс с heartbeat. Итог: **2.5-4× токенов и стоимости vs single agent**. Дополнительные проблемы: overlapping scopes → merge conflicts (два агента пишут в один файл); mailbox latency 2-4 сек делает синхронизацию медленнее ожидаемого; reliability ~50% (экспериментальная фича).

Внутри Anthropic Agent Teams дали coverage 16% → 54% — но это на задачах, специально подходящих для multi-agent (adversarial dual-analysis, cross-domain validation). На стандартных PR review задачах разница меньше.

**Как митигировать:**

Agent Teams использовать только для задач, где нужна настоящая inter-agent collaboration (например: Security mate + Architecture mate с peer-to-peer диалогом через mailbox). Для остального — subagents (sequential через `Agent` tool): тот же результат, меньше стоимость, 100% reliability. Строгое разделение scopes между агентами — запрет на запись в общие файлы без lock. Cost guardrails обязательны: `max-turns`, `max-tokens`, `timeout` per mate.

**Источник:** Anthropic Agent Teams docs; internal Anthropic validation data (Feb 2026)

---

## Итог: метрика успеха

Правильная метрика для AI code review:

| Метрика | Целевое значение | Что означает |
|---|---|---|
| Comment action rate | >60% | Доля комментариев, которые реально обработаны |
| Signal ratio | >60% | Доля комментариев, указывающих на реальную проблему |
| Cycle time delta | -10-20% | Сокращение времени от открытия PR до merge |

Ниже 40% comment action rate = net negative инструмент. Срок до adoption collapse без пилотного тюнинга: 3-4 месяца.
