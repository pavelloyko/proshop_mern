# Recipe: Mini-task «Mutation testing на своём коде»

Практическое задание Stage 4 (домашка M6, bonus-уровень). Время: ~75 минут. Цель: лично измерить gap coverage vs MSI на своём Python модуле и поднять MSI выше 70%.

---

## Что потребуется

- Python 3.9+, `pip`, виртуальное окружение.
- Любой Python модуль из вашего проекта (минимум ~30-50 строк с функциями).
- Claude Code или любой AI-ассистент.
- Linux/macOS или WSL на Windows (mutmut требует `fork()` — подробнее в Watch-outs).

---

## Шаг 1 — Генерация тест-кейсов через Claude Code (30 мин)

Откройте Claude Code в директории вашего проекта. Выберите Python файл с бизнес-логикой.

**Вариант A: встроенная команда CC**

```
/test src/your_module.py
```

**Вариант B: явный промпт**

```
Сгенерируй comprehensive pytest тесты для этого файла.
Требования:
- Покрой все публичные функции
- Включи edge cases: пустые входные данные, None, граничные значения
- Включи negative cases: невалидные типы, out-of-range значения
- Каждый тест должен содержать минимум одно явное assertEqual/assert ==
- НЕ используй assert result is not None как единственный assertion
- Сохрани в tests/test_<имя_файла>.py
```

После генерации: запустите тесты и проверьте, что они проходят.

```bash
pytest tests/test_your_module.py -v
pytest tests/test_your_module.py --cov=src/your_module --cov-report=term-missing
```

Зафиксируйте coverage % — это ваш baseline.

---

## Шаг 2 — Mutation baseline с mutmut (30 мин)

### Установка

```bash
pip install mutmut==3.5.0
```

### Запуск

```bash
mutmut run --paths-to-mutate src/your_module.py
```

Прогон займёт 1-5 минут в зависимости от размера модуля.

### Просмотр результатов

```bash
mutmut results
```

Пример вывода:

```
Legend for status codes:
...
Mutation score [28.05 s]: 58/100 killed, 42/100 survived
```

Для просмотра surviving mutants по-отдельности:

```bash
mutmut show <mutant-id>
```

Или сгенерировать HTML-отчёт:

```bash
mutmut html
open html/index.html
```

Зафиксируйте MSI % — это ваш baseline MSI.

Обычный результат AI-generated тестов: **40-65% MSI** при coverage 85-95%.

---

## Шаг 3 — Улучшение assertions (15 мин)

Скопируйте список surviving mutants из отчёта mutmut. Дайте их в Claude Code:

```
Вот surviving mutants из mutation report:

[вставьте список surviving mutants — текст из mutmut results / mutmut show]

Улучши assertions в файле tests/test_your_module.py чтобы убить эти мутанты.
Правила:
- НЕ переписывай тесты с нуля
- НЕ изменяй production-код
- Добавь точечные assertions к существующим тестам
- Каждый surviving mutant должен быть адресован минимум одним новым assert
- Если нужен новый тест — добавь его, но только для непокрытого поведения
```

После: перезапустите mutmut.

```bash
mutmut run --paths-to-mutate src/your_module.py
mutmut results
```

Цель: MSI > 70%.

---

## Целевая метрика

| Метрика | Baseline (AI default) | Цель после улучшений |
|---|---|---|
| Line coverage | ~85-95% | без изменений |
| MSI | ~40-65% | > 70% |
| Gap (coverage - MSI) | ~30-40 пунктов | < 15 пунктов |

---

## Watch-outs (CRITICAL)

### mutmut 3.x не мутирует код вне функций

Это regression от версии 2.x. Если ваш модуль содержит большую часть логики на module level (глобальные переменные, условные блоки на верхнем уровне) — mutmut 3.x пропустит их. Решения:

1. Перенести логику в функции (рекомендуется).
2. Использовать `mutmut==2.5.3` вместо 3.x.
3. Переключиться на `cosmic-ray` (см. ниже).

### Windows: только через WSL

mutmut использует `fork()` — системный вызов недоступный нативно в Windows. Обязательно работать через WSL (Windows Subsystem for Linux).

```
# В PowerShell:
wsl
# Дальше все команды в Linux-окружении
```

### Альтернатива для Windows: cosmic-ray 8.4.6

cosmic-ray — Windows-friendly Python mutation tester с session-based workflow.

```bash
pip install cosmic-ray==8.4.6

# Создать конфиг
cosmic-ray init cosmic-ray.toml src/your_module.py

# Запустить
cosmic-ray exec cosmic-ray.toml

# Посмотреть результаты
cr-report cosmic-ray.toml
```

Сравнение с mutmut (PyCon 2025):

| Инструмент | Mutants/min | Detection rate | RAM |
|---|---|---|---|
| mutmut 3.5.0 | 1 200 | 88.5% | 150 MB |
| cosmic-ray 8.4.6 | 950 | 82.7% | 180 MB |

---

## Ожидаемый результат

После прохождения всех 3 шагов напишите короткий анализ (3-5 предложений):

- Стартовый MSI (из Шага 2): `____%`
- Финальный MSI (из Шага 3): `____%`
- Сколько мутантов выжило изначально / сколько осталось.
- Какой тип assertions был самым слабым (обычно: `is not None`, `len > 0`, `isinstance`).
- Что удивило.

Этот анализ — bonus-часть submission Stage 4 (см. checklist в `homework-spec.md`).

---

## Продвинутый уровень: Property-based testing с Hypothesis

Если основные 3 шага закончены досрочно — попробуйте Hypothesis с командой для Claude Code.

1. Установите Hypothesis:

```bash
pip install hypothesis
```

2. Скачайте `/hypothesis` Claude Code command:
   https://hypothesis.works/articles/claude-code-plugin/

3. Скопируйте `hypo.md` в `~/.claude/commands/`.

4. Запустите в Claude Code:

```
/hypothesis src/your_module.py
```

Hypothesis автоматически генерирует property-based тесты (математические инварианты). Полезно для функций с четкими математическими свойствами: сортировка, агрегация, парсинг.

---

## Ссылки

- mutmut PyPI: https://pypi.org/project/mutmut/
- mutmut docs: https://mutmut.readthedocs.io
- cosmic-ray: https://github.com/sixty-north/cosmic-ray
- cosmic-ray PyPI: https://pypi.org/project/cosmic-ray/
- Hypothesis: https://hypothesis.readthedocs.io
- Hypothesis Claude Code command: https://hypothesis.works/articles/claude-code-plugin/
