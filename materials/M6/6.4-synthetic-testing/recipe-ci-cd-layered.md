# Recipe: CI/CD Layered Strategy для Synthetic Testing

Пятиуровневая стратегия запуска тестов: от pre-commit до weekly. Каждый уровень балансирует скорость с глубиной.

---

## Ключевой принцип: Coverage vs MSI gate split

- **Coverage threshold = gate verification.** CI падает если ниже порога. Дефолт: 70%.
- **MSI = quality signal.** Трекается как тренд. Целевой разрыв: MSI не ниже (coverage - 10pp).

Пример: если coverage 85% → MSI должен быть > 75%. Если MSI < 75% — это warning в отчёте, но не block (за исключением явно настроенного hard gate).

---

## 5 уровней

### Уровень 1 — Pre-commit (секунды)

| Параметр | Значение |
|---|---|
| Что запускается | Linters (ruff, eslint), форматирование, unit-тесты только для изменённых файлов |
| Время | < 30 секунд |
| Failure policy | Block commit |
| Инструмент | pre-commit, husky |

Опционально: AI test gen для изменённого файла (Qodo Cover, до 5 мин — только если не блокирует workflow).

### Уровень 2 — PR validation (10-15 минут)

| Параметр | Значение |
|---|---|
| Что запускается | Full unit + integration tests, coverage gate ≥ 70%, Level 1 PBT (structural + schema validation) |
| Время | 10-15 минут |
| Failure policy | Block merge если coverage < 70% или unit-тесты упали |
| Инструмент | pytest, jest, hypothesis (structural tests) |

Level 1 PBT — быстрые property-based тесты: schema validation, structural invariants (acyclic plans, idempotency), базовые type contracts.

### Уровень 3 — Merge to main (15-30 минут)

| Параметр | Значение |
|---|---|
| Что запускается | Incremental mutation testing (только на изменённых строках), Level 2 PBT (LLM-as-judge / embedding similarity, 10-50 runs), load smoke test |
| Время | 15-30 минут |
| Failure policy | Warn-only для mutation; block если Level 2 PBT < 80% success rate |
| Инструмент | mutmut `--use-coverage`, Stryker incremental, Tautest |

Tautest workflow: запускает mutation только на `git diff` строках → если выжили мутанты, генерирует `.tautest/fix-prompt.md` с инструкцией для Claude Code: «не меняй production-код, добавь тесты на мутированное поведение» → sticky PR comment.

### Уровень 4 — Nightly (часы)

| Параметр | Значение |
|---|---|
| Что запускается | Full mutation testing (все файлы), ELFUZZ/Atheris fuzzing критических парсеров, chaos engineering на staging |
| Время | 2-6 часов |
| Failure policy | Report-only, создать Issue при MSI < 60% |
| Инструмент | mutmut, cosmic-ray, Atheris, Harness chaos |

MSI tracking: сохранять в `reports/mutation/` с датой, трекать тренд.

### Уровень 5 — Weekly (день+)

| Параметр | Значение |
|---|---|
| Что запускается | Adversarial ML sweep, performance regression с synthetic load, аудит synthetic datasets |
| Время | Часы до суток |
| Failure policy | Report + team review |
| Инструмент | ELFUZZ long runs, AIPerf/LLMPerf, Gretel audit |

---

## Three-level PBT CI (Anthropic PBT-agent паттерн)

Отдельная стратегия для property-based тестов:

| Уровень | Что запускается | Когда |
|---|---|---|
| Commit-level | Hypothesis тесты на изменённых модулях | При каждом push |
| Merge-level | Полный PBT suite, все модули с property-тестами | При merge в main |
| Weekly | Long-running PBT прогоны, 100K+ примеров на модуль | Воскресенье ночью |

Источник: Anthropic blog https://red.anthropic.com/2026/property-based-testing/ — именно long-running прогоны находят редкие баги типа `numpy.random.wald` (catastrophic cancellation, обнаружен PR #29609, исправлен в NumPy v2.3.4).

---

## GitHub Actions YAML пример

Пример commit-level pytest + hypothesis для Python проекта:

```yaml
name: Synthetic Testing — Commit Level

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  unit-and-hypothesis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # нужен Tautest для git diff

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov hypothesis

      - name: Run unit tests with coverage
        run: |
          pytest tests/ \
            --cov=src \
            --cov-fail-under=70 \
            --cov-report=xml \
            -v

      - name: Run Hypothesis tests (structural)
        run: |
          pytest tests/property/ \
            --hypothesis-seed=12345 \
            -x \
            -v

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

Nightly mutation testing:

```yaml
name: Nightly Mutation Testing

on:
  schedule:
    - cron: "0 2 * * *"  # каждую ночь в 02:00 UTC

jobs:
  full-mutation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install mutmut
        run: pip install mutmut==3.5.0 pytest

      - name: Run full mutation testing
        run: |
          mutmut run --paths-to-mutate src/
          mutmut results

      - name: Generate HTML report
        run: mutmut html

      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: mutation-report-${{ github.run_id }}
          path: html/
          retention-days: 30
```

---

## Когда что включать

| Размер команды | Минимальный набор |
|---|---|
| 1 человек, pet project | Pre-commit (unit) + PR (coverage gate) |
| 2-5 человек, стартап | + Nightly mutation testing |
| 5+ человек, production | Все 5 уровней + MSI trend tracking |

---

## Ссылки

- Hypothesis docs: https://hypothesis.readthedocs.io
- mutmut CI examples: https://mutmut.readthedocs.io/en/latest/ci.html
- Tautest: https://tautest.dev
- Anthropic PBT-agent: https://red.anthropic.com/2026/property-based-testing/
- OpenCode issue #18108: https://github.com/opencode-ai/opencode/issues/18108
