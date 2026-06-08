# Topic 6.4 — Synthetic Testing

Материалы к теме 6.4 «Synthetic Testing» курса AI-Driven Development Level 1, Module 6.

---

## Что в этой папке

| Файл | Что содержит | Когда читать |
|---|---|---|
| `README.md` | Навигатор, главные идеи, ссылки | Сначала |
| `coverage-vs-msi.md` | Объяснение центральной метрики: coverage % vs MSI | Перед практикой |
| `tools-landscape.md` | Ландшафт 7 инструментов с decision-матрицей | При выборе инструмента |
| `recipe-mini-task.md` | Рецепт mini-task ~75 мин на своём Python модуле | Stage 4 домашки |
| `recipe-ci-cd-layered.md` | CI/CD layered strategy, 5 уровней, YAML пример | При настройке CI |

---

## Главные идеи

### 1. Synthetic тест-кейсы vs synthetic данные — разные вещи

Путаница встречается постоянно.

**Synthetic тест-кейсы** (Diffblue Cover, Claude Code `/test`):
- AI генерирует сами `pytest`/`jest` тесты — то, что запускается в CI.
- Результат: файл `test_*.py` с функциями `def test_...`.

**Synthetic данные** (Faker, SDV, Gretel):
- AI или библиотека генерирует входные данные для тестов — CSV, JSON, строки.
- Используется, когда нельзя применять реальные данные пользователей (GDPR, HIPAA, PCI-DSS).

Оба инструмента полезны и не заменяют друг друга.

### 2. Coverage % vs MSI: реальный разрыв 35 пунктов

Типичный результат AI-generated тестов на production-проекте:

```
Line coverage:  93%
MSI:            58%
Gap:            35 points
```

93% coverage означает, что тесты прошли по 93% строк кода. MSI 58% означает, что только 58% намеренно внесённых ошибок (мутантов) были обнаружены тестами.

Тест `assert result is not None` даёт coverage, но не даёт MSI. Мутация `return True` → `return False` через такой тест не проходит.

Данные: Generative Specification white paper, DOI 10.5281/zenodo.19073543, март 2026.

### 3. Mutation testing — единственная честная метрика качества AI-тестов

MSI (Mutation Score Index) считается так:

```
MSI = (число убитых мутантов) / (общее число мутантов) × 100%
```

Инструмент вносит мутации (меняет `>` на `>=`, `True` на `False`, удаляет строки) и запускает тест-сьют. Если тесты не падают — мутант «выжил». Чем меньше выживших, тем сильнее тесты.

Порог для AI-generated тестов: MSI > 70% считается приемлемым.

### 4. Tester + MutationSmith — РАЗНЫЕ sub-agents

Если один агент пишет тесты и сам же их оценивает через мутацию — он оптимизирует тесты под метрику, а не под обнаружение багов. Паттерн AgentForge разделяет: `Planner → Coder → Tester → Debugger → Critic`. Каждый агент имеет ограниченный доступ и не видит полный контекст других.

---

## Pre-read order

1. `coverage-vs-msi.md` — понять, почему coverage недостаточно (10 мин)
2. `recipe-mini-task.md` — пройти mini-task на своём коде (75 мин)
3. `tools-landscape.md` — выбрать инструмент под задачу (по необходимости)
4. `recipe-ci-cd-layered.md` — настроить CI/CD pipeline (по необходимости)

---

## Дополнительные ссылки

| Ресурс | URL |
|---|---|
| mutmut docs | https://mutmut.readthedocs.io |
| mutmut PyPI | https://pypi.org/project/mutmut/ |
| cosmic-ray docs | https://cosmic-ray.readthedocs.io |
| Anthropic PBT-agent blog | https://red.anthropic.com/2026/property-based-testing/ |
| Anthropic PBT-agent paper | https://arxiv.org/abs/2510.09907 |
| Hypothesis `/hypothesis` Claude Code command | https://hypothesis.works/articles/claude-code-plugin/ |
| ELFUZZ paper | https://arxiv.org/abs/2506.10323 |
| ELFUZZ GitHub | https://github.com/OSUSecLab/elfuzz |
| Diffblue Cover docs | https://docs.diffblue.com |
| Generative Specification white paper (DOI) | https://doi.org/10.5281/zenodo.19073543 |
