# Tools Landscape — Synthetic Testing 2026

7 инструментов для AI-assisted testing: мутации, property-based testing, fuzzing, enterprise test generation.

---

## 1. Anthropic PBT-agent

**Что это:** Агентный подход к property-based testing на базе Claude Opus. Агент читает код и docstrings, выводит математические инварианты, пишет Hypothesis тесты, запускает их и анализирует результаты.

**Когда применять:** Функции с чёткими математическими или алгоритмическими свойствами: сортировка, агрегация, парсинг, криптография, численные вычисления. Не подходит для функций с side effects, I/O, сетевых вызовов.

**5-step workflow:**

1. Read & understand (код + docstrings + связанные модули).
2. Propose properties (grounded findings — только то, что следует из кода).
3. Write Hypothesis tests.
4. Run & reflect (упал → реальный баг? прошёл → тривиально?).
5. Write bug report если уверен в баге.

**Реальный результат:** 100 популярных Python пакетов → 56% valid bugs overall, 86% в top-21. Найден и исправлен баг `numpy.random.wald`: catastrophic cancellation, ошибка на 10 порядков величины. PR #29609, выпущен в NumPy v2.3.4.

**Как попробовать:**
- Скачать `/hypothesis` Claude Code command: https://hypothesis.works/articles/claude-code-plugin/
- Скопировать `hypo.md` в `~/.claude/commands/`
- Запустить: `/hypothesis your_module.py`

**Официальные ссылки:**
- Blog: https://red.anthropic.com/2026/property-based-testing/
- arXiv: https://arxiv.org/abs/2510.09907
- Code: https://github.com/mmaaz-git/agentic-pbt
- Hypothesis command: https://hypothesis.works/articles/claude-code-plugin/

**Цена:** бесплатно (open source), стоимость Claude API вызовов.

---

## 2. mutmut 3.5.0

**Что это:** Python mutation tester. Вносит мутации в исходный код → запускает тест-сьют → считает MSI.

**Когда применять:** Python проекты, baseline measurement для AI-generated тестов, CI/CD quality gate на nightly.

**Ключевые числа (PyCon 2025 benchmark):**
- 1 200 мутантов в минуту
- 88.5% detection rate
- 150 MB RAM
- ~5 мин CI на 10K LOC

**Watch-outs:**
- 3.x не мутирует код вне функций (regression от 2.x) — логику нужно оборачивать в функции.
- Требует `fork()` → на Windows только через WSL.
- Mutmut 3.x добавил async coroutine support (снижает surviving мутантов на 22%).

**Быстрый старт:**

```bash
pip install mutmut==3.5.0
mutmut run --paths-to-mutate src/your_module.py
mutmut results
mutmut html
```

**Официальные ссылки:**
- PyPI: https://pypi.org/project/mutmut/
- Docs: https://mutmut.readthedocs.io

**Цена:** бесплатно, MIT.

---

## 3. cosmic-ray 8.4.6

**Что это:** Python mutation tester — Windows-friendly альтернатива mutmut с session-based workflow.

**Когда применять:** Windows без WSL, нужны сохраняемые сессии (можно прервать и продолжить), нужны более детальные отчёты по типам мутаций.

**Ключевые числа (PyCon 2025 benchmark):**
- 950 мутантов в минуту
- 82.7% detection rate
- 180 MB RAM
- ~7 мин CI на 10K LOC

**Быстрый старт:**

```bash
pip install cosmic-ray==8.4.6

# Создать конфиг (TOML файл)
cosmic-ray init cosmic-ray.toml src/your_module.py

# Запустить сессию
cosmic-ray exec cosmic-ray.toml

# Отчёт
cr-report cosmic-ray.toml
cr-html cosmic-ray.toml > report.html
```

**Официальные ссылки:**
- GitHub: https://github.com/sixty-north/cosmic-ray
- PyPI: https://pypi.org/project/cosmic-ray/
- Docs: https://cosmic-ray.readthedocs.io

**Цена:** бесплатно, MIT.

---

## 4. Diffblue Cover

**Что это:** Enterprise AI test generation для Java. Анализирует байт-код, генерирует JUnit тесты автономно без промптов.

**Когда применять:** Java legacy codebase (Spring Boot, Java EE), нужно быстро поднять coverage в унаследованном коде, команда не хочет писать тесты вручную. Применение в крупном enterprise консалтинг-кейсе (100+ микросервисов, Java monolith) показало автоматическое покрытие до 80%+ без участия команды.

**Ключевые числа:**
- 80.7% line coverage автоматически (vs 32.3% у Claude Code на том же коде — 2.5x разница)
- Анализирует байт-код, не требует исходников
- Работает как IntelliJ plugin или CLI

**Важно:** Diffblue Cover использует Claude Code как sub-agent внутри своего pipeline — это не конкуренты, а интеграция.

**Decision guide:**
- Python → mutmut/cosmic-ray + Claude Code
- Java legacy, enterprise, coverage gap > 40% → Diffblue Cover
- Java + уже есть приличные тесты → Claude Code достаточно

**Официальные ссылки:**
- Docs: https://docs.diffblue.com
- Product: https://www.diffblue.com/products/cover/

**Цена:** commercial (enterprise pricing), есть community edition.

---

## 5. PromptFuzz

**Что это:** Prompt-based fuzzing для LLM-приложений. Тестирует security уязвимости через автоматически генерируемые атаки.

**Когда применять:** Приложение использует LLM (chatbot, RAG, agent) и нужно проверить на: jailbreak, prompt injection, system prompt leak, toxic content generation.

**Что делает:**
- Плагины атак: `jailbreak.dan`, `injection.system_prompt_leak`, `toxic.hate_speech`
- Выводит SARIF-отчёт → интеграция в GitHub Security tab
- Non-zero exit code при обнаружении уязвимостей → блокирует CI

**Быстрый старт:**

```bash
pip install promptfuzz

# Запустить базовый scan
promptfuzz run --target http://localhost:8000/chat \
               --plugins jailbreak.dan,injection.system_prompt_leak \
               --output sarif > security-report.sarif
```

**Официальные ссылки:**
- GitHub: https://github.com/rahiemb/promptfuzz

**Цена:** бесплатно, open source.

---

## 6. ELFUZZ

**Что это:** LLM-guided code fuzzer для C/C++ программ. LLM анализирует код, генерирует начальные seeds, управляет мутациями для максимального покрытия.

**Когда применять:** Security-critical C/C++ код: парсеры, протоколы, криптография. Не для Python/JS/Java.

**Ключевые числа (USENIX Security 2025):**
- +434.8% branch coverage vs традиционный AFL++
- +216.7% найденных багов
- 5 zero-day уязвимостей в cvc5 за 14 дней
- Масштабируется до 1.79M LoC

**Workflow:**
1. Atheris/AFL++ + Claude генерирует 50 валидных seed-файлов.
2. Запуск 24 часа → сбор новых coverage paths.
3. Claude генерирует дополнительные мутации для непокрытых веток.
4. Повтор → окупается за неделю на средне-сложном парсере.

**Официальные ссылки:**
- GitHub: https://github.com/OSUSecLab/elfuzz
- arXiv: https://arxiv.org/abs/2506.10323

**Цена:** бесплатно, academic open source.

---

## 7. Tautest

**Что это:** Workflow-инструмент (май 2026): Stryker mutation testing + AI-fix prompt для Claude Code/Cursor. Запускает mutation только на `git diff` строках, генерирует промпт для починки слабых тестов.

**Когда применять:** JavaScript/TypeScript проекты, CI/CD integrated mutation feedback, команда использует Claude Code или Cursor как IDE assistant.

**Workflow:**
1. Tautest запускает Stryker только на строках из `git diff`.
2. Если есть surviving мутанты — генерирует `.tautest/fix-prompt.md`.
3. Промпт содержит: «не меняй production-код, добавь тесты на мутированное поведение».
4. Sticky PR comment с ссылкой на промпт.
5. Разработчик открывает `.tautest/fix-prompt.md` в Claude Code → `/fix`.

**GitHub Actions требования:** `fetch-depth: 0` + `pull-requests: write` permission.

**Официальные ссылки:**
- Site: https://tautest.dev

**Цена:** уточняется (выпущен май 2026).

---

## Decision matrix

| Ситуация | Инструмент |
|---|---|
| Python, нужна baseline MSI | mutmut 3.5.0 |
| Python + Windows без WSL | cosmic-ray 8.4.6 |
| Java legacy, нужен быстрый coverage lift | Diffblue Cover |
| Есть LLM-приложение, нужна security проверка | PromptFuzz |
| C/C++, security critical, нужен fuzzing | ELFUZZ |
| JS/TS + CI + Claude Code/Cursor в команде | Tautest |
| Математические/алгоритмические Python функции | Anthropic PBT-agent |
| Нужен И mutation score И property-based | mutmut + Hypothesis |

---

## Комбинирование инструментов

Типичный Python production stack:

```
Pre-commit:    pytest (unit, изменённые файлы)
PR:            pytest --cov (coverage gate) + hypothesis structural
Merge:         mutmut --use-coverage (incremental)
Nightly:       mutmut full + Hypothesis long-runs (100K+ examples)
Security:      PromptFuzz (если есть LLM-компоненты)
```

Важно: mutmut и Hypothesis не заменяют друг друга. mutmut проверяет, насколько хорошо тесты ловят изменения. Hypothesis проверяет инварианты на широком пространстве входных данных.
