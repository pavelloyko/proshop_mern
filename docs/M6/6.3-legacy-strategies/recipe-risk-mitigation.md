# Рецепт: Безопасный AI-рефакторинг — 7 правил + 5 фаз

> **Источник:** синтез production postmortem'ов 2024-2026 (публичные кейсы)
> **Применимость:** любой legacy-модуль, который вы планируете изменить с помощью AI
> **Аудитория:** разработчики, техлиды, PM-ы как процесс-владельцы

---

## 7 правил безопасного AI-рефакторинга

Каждое правило — это постмортем. Нарушение любого из них в реальных кейсах 2024-2026 привело к production-инцидентам.

### Правило 1. Characterization tests ДО изменений

Зафиксируйте текущее поведение системы до того, как AI что-либо тронет.

Characterization test не проверяет «правильно ли это» — он проверяет «это то, что система делает сейчас». Это эталон.

```python
# Пример characterization test (pytest)
def test_order_status_transition_current_behavior():
    """Characterization test: фиксируем текущее поведение, не ideal"""
    result = update_order_status(order_id=123, new_status="shipped")
    # Не assert result == "shipped" (ideal)
    # А assert result == snapshot_of_current_behavior
    assert result == {"status": "shipped", "updated": True, "legacy_flag": None}
```

Запустите тесты на неизменённом коде — они должны проходить. Это ваш эталон.

### Правило 2. Маленькие PR — меньше 200 строк

Меньше строк = меньше когнитивной нагрузки на ревью = меньше пропущенных изменений.

Практическое правило: если нельзя объяснить PR устно за 1-2 минуты — он слишком большой.

AI склонен генерировать «большие cleanup'ы». Это его естественный паттерн. Явно ограничивайте:

```
Do NOT clean up unrelated code. Scope: ONLY the function calculateDiscount().
Keep all changes under 100 lines.
```

### Правило 3. Явные «Do NOT» в промпте

Пишите ограничения, не пожелания. Список что нельзя трогать важнее списка что нужно сделать.

Примеры:

```
Do NOT change public method signatures.
Do NOT touch auth/crypto/payment-related code.
Do NOT rewrite SQL queries — only add the new index logic.
Do NOT remove comments even if they look outdated.
Do NOT rename variables outside the scope of this function.
```

Почему это работает: AI оптимизирует код под то что видит. Tribal knowledge — ограничения которые не видны в коде — нужно передать явно.

### Правило 4. Упаковать контекст (5 блоков)

Структурированный контекст даёт значительно лучший результат чем «свободный» запрос.

```
## Цель
[Что именно нужно изменить и зачем]

## Границы
[Что НЕЛЬЗЯ трогать — файлы, функции, паттерны]

## Форма ответа
[Только изменённый файл / только diff / только объяснение без кода]

## Соседний код
[Прикрепите связанные файлы: middleware, interfaces, tests]

## Правила проекта
[Coding conventions, ADR, важные комментарии из AGENTS.md]
```

### Правило 5. Доменное ревью обязательно

AI ревью — это не доменное ревью. Автоматические проверки (SAST, типы, линтер) — это не доменное ревью.

**Moonwell DeFi (2024, публичный постмортем):** AI-рефакторинг пропустил умножение на курс обмена в одном из методов расчёта позиций. SAST не поймал — код был синтаксически корректным. Результат: $1.78M bad debt.

Доменное ревью — это когда человек, знающий бизнес-логику, читает изменения с вопросом «соответствует ли это тому как работает система?», а не «правильный ли синтаксис?».

### Правило 6. SAST/SBOM/секреты — независимо от AI и human review

Автоматические проверки безопасности должны работать как gate, независимо от того, писал ли код AI или человек. Это не замена ревью — это отдельный слой.

Минимальный набор:
- SAST (статический анализ): Semgrep, SonarQube, CodeQL
- Сканирование секретов: GitLeaks, truffleHog
- SBOM (зависимости): Dependabot, Snyk

AI, в отличие от человека, может уверенно использовать устаревшую или уязвимую библиотеку из training data — не зная что она уже deprecated.

### Правило 7. Откат всегда репетируется

Никогда не деплоите изменения без заранее отрепетированного плана отката.

**Knight Capital 2012 (публичный постмортем):** команда деплоила код без чёткого плана отката. За 45 минут торгов потеряли $460M. Компания потеряла независимость.

Репетиция отката означает: кто делает, как делает, какие метрики-стоп-краны запускают откат автоматически, сколько времени занимает откат. Всё это определяется ДО деплоя.

---

## «Do NOT» промпт-шаблоны для разных сценариев

### Сценарий A: Рефакторинг платёжного модуля

```
You are refactoring calculateDiscount() in PaymentProcessor.java.

Do NOT change the method signature (public BigDecimal calculateDiscount).
Do NOT touch any code outside of this single method.
Do NOT remove the $999,999 transaction limit check — it exists for a business reason.
Do NOT modify synchronized blocks.
Do NOT add new imports.

Scope: only the internal implementation of calculateDiscount().
```

### Сценарий B: Миграция Python 2 → Python 3

```
Migrate this file from Python 2 to Python 3.

Do NOT change business logic — only syntax modernization.
Do NOT replace print statements with logging — only convert to print().
Do NOT change variable names or function signatures.
Do NOT remove type comments (# type: ignore) — they are intentional.
Do NOT optimize or refactor — mechanical migration only.
```

### Сценарий C: Очистка от «dead code»

```
Identify potentially dead code in this file.

Do NOT delete anything. Output only a list of candidates with:
- function/variable name
- why you think it might be dead
- what you are NOT sure about

I will review each candidate manually before any deletion.
```

---

## 5-фазный фреймворк модернизации

Подходит для любого legacy-проекта: от одного модуля до enterprise-программы.

### Phase 0: Контекст для AI

Создайте `AGENTS.md` (и/или `CLAUDE.md`) в корне проекта или модуля:
- Что делает система
- Какие модули нельзя трогать и почему
- Coding conventions
- Критические бизнес-ограничения

Без этого у AI нет контекста. Tribal knowledge не в коде — вам нужно его зафиксировать.

### Phase 1: Пилотный поток — ExecPlan (4-6 недель)

Не годовая инициатива — короткий пилот на одном модуле. Формат ExecPlan (4 секции):
- **Scope:** что именно мигрируем
- **Why:** бизнес-обоснование
- **Steps:** пошаговый план с acceptance criteria
- **Acceptance:** как определяем что готово

### Phase 2: Инвентаризация + characterization tests

- Карта зависимостей: какой код что вызывает
- Characterization tests на критические участки
- Определение acceptance criteria: что сравниваем поэлементно, что агрегированно

### Phase 3: План валидации

Определите ДО начала рефакторинга:
- Что именно будет сравниваться (output'ы, метрики, поведение в edge cases)
- Допустимый порог расхождения (error rate <0.01%, distribution ±X%)
- Go/no-go критерии — автоматические, не ручные

### Phase 4: Реализация + теневой режим

- Маленькие PR <200 строк (правило 2)
- Явные ограничения в каждом промпте (правила 3-4)
- Deploy за feature flag на 0% трафика
- Parallel run / shadow mode: новый код принимает трафик, не применяет side effects, сравниваете output'ы с legacy

### Phase 5: Канарейка + вывод legacy в резерв

- Канарейный деплой: 1% → 10% → 50% → 100%
- На каждом шаге: метрики-стоп-краны с автоматическим откатом (error rate >2% за 5 мин = автоматический rollback без обсуждения)
- 100% трафика на новый код: legacy остаётся в горячем резерве 1-3 месяца
- Только после подтверждения стабильности: удаление старого кода + удаление feature flag

---

## Где этот фреймворк проваливается

**Тонкие characterization tests** — 60-80% line coverage почти ничего не гарантирует в legacy. Нужны тесты на поведение, не на синтаксис.

**Silent model drift** — AI-модели получают обновления. То что работало в версии A может давать другой результат в версии B. Фиксируйте версию модели явно в конфигурации, не вызывайте floating alias (`gpt-4o`, `claude-sonnet` без версии).

**Cascading dependencies** — если изменения в нескольких модулях деплоятся одновременно, откатывайте атомарно. Последовательный откат создаёт новые промежуточные состояния, которые могут быть хуже исходной проблемы.

---

## Дополнительные ресурсы

- Knight Capital 2012 postmortem: поиск «Knight Capital August 2012 trading loss SEC»; публичный отчёт SEC
- Moonwell DeFi incident: [docs.moonwell.fi/moonwell/protocol/security](https://docs.moonwell.fi/moonwell/protocol/security)
- IBM CodeConcise white paper: поиск «IBM CodeConcise COBOL modernization»
- Strangler Fig pattern (Martin Fowler): [martinfowler.com/bliki/StranglerFigApplication.html](https://martinfowler.com/bliki/StranglerFigApplication.html)
