# Coverage % vs MSI — центральная метрика Synthetic Testing

---

## Что такое coverage %

**Line coverage** — процент строк исходного кода, которые были выполнены в ходе тест-рана.

**Branch coverage** — процент ветвей (`if/else`, `switch`) которые тесты прошли.

Пример:

```python
def discount(price, is_member):
    if is_member:          # ← branch A
        return price * 0.9
    return price           # ← branch B
```

Если тест вызывает только `discount(100, True)`:
- Line coverage: 100% (все строки выполнены)
- Branch coverage: 50% (ветвь `is_member=False` не проверена)

Tools для coverage в Python: `pytest-cov`, `coverage.py`.

---

## Что такое MSI (Mutation Score Index)

MSI — процент мутантов, обнаруженных тестами.

**Мутант** — версия кода с одним намеренно внесённым изменением:

| Тип мутации | Пример |
|---|---|
| Arithmetic operator | `price * 0.9` → `price / 0.9` |
| Relational operator | `price > 100` → `price >= 100` |
| Boolean literal | `return True` → `return False` |
| Statement deletion | удалить строку `return price * 0.9` |

Формула:

```
MSI = (убитые мутанты) / (все мутанты) × 100%
```

Мутант «убит», если хотя бы один тест упал при его наличии. Мутант «выжил», если все тесты остались зелёными, хотя код изменился.

---

## Почему coverage не равно качеству

Рассмотрим пример. AI сгенерировал такой тест:

```python
def test_discount_applied():
    result = discount(100, True)
    assert result is not None   # ← слабый assertion
```

Line coverage: 100% (все строки пройдены).

Теперь мутант вносит изменение: `return price * 0.9` → `return price * 1.1`. Тест **не падает** — `result` по-прежнему не None. Мутант выжил.

Правильный тест:

```python
def test_discount_applied():
    result = discount(100, True)
    assert result == 90.0       # ← сильный assertion
```

Теперь мутант `price * 1.1` даст `110.0`, тест упадёт. Мутант убит.

---

## Реальный разрыв: 35 пунктов

Эксперимент с multi-agent adversarial testing (Generative Specification, DOI 10.5281/zenodo.19073543, март 2026):

- Проект: services layer, Stryker mutation testing, 116 мутантов.
- Baseline AI-generated тесты:
  - Line coverage: **93.1%**
  - MSI: **58.62%**
  - Gap: **34.5 пункта**
  - Выжило: **48 из 116 мутантов**

Причина: тесты заполнены `assert result is not None` вместо `assert result == expected`. Все зависимости замоканы — реальное поведение не тестируется.

После 3 раундов улучшений (replace weak assertions → boundary conditions → error path validation): MSI вырос до **93.10%**, совпав с line coverage.

**Вывод: тот же AI, который написал слабые тесты, может написать сильные — если получить mutation report как контекст.**

---

## Кейс «98% coverage / zero protection»

Паттерн «Claude writes, human reviews, ship» (Engineering Playbook, апрель 2026):

- Week 6: 91% coverage. Week 11: 98% coverage.
- В production ушли три бага:
  1. **Race condition** — задержка read replica 2 сек приводила к двойной регистрации email. Тест проходил, потому что DB была замокана.
  2. **Promo edge case** — невалидный промо-код не возвращал полную цену. Claude никогда не тестировал невалидные входные данные.
  3. **Cache invalidation** — stale reads под нагрузкой.

Root cause: «Claude doesn't know about our infrastructure». AI тестирует код, который ты написал — но не инфраструктуру, на которой он работает.

Infrastructure-aware тесты (transaction boundaries, connection pool exhaustion, cache races, distributed transactions) — это зона ответственности человека.

---

## Анти-паттерн «Generation flood»

Команда даёт команду «Claude, напиши тесты для каждой функции». Через час: 5000 тест-кейсов, 80% дубликаты или тривиальные (`assert True`).

Симптом: coverage 100%, MSI < 30%.

Лечение:
- Квота: не более N тестов на функцию (обычно 3-5).
- Обязательный code review перед merge.
- MSI как gate в CI, а не только coverage.

---

## Конвертация слабых assertions в сильные

**До (AI default):**

```python
def test_calculate_total():
    cart = Cart()
    cart.add_item("book", 500)
    cart.add_item("pen", 50)
    result = cart.total()
    assert result is not None
    assert isinstance(result, (int, float))
```

**После (MSI-driven improvement):**

```python
def test_calculate_total():
    cart = Cart()
    cart.add_item("book", 500)
    cart.add_item("pen", 50)
    assert cart.total() == 550

def test_calculate_total_empty_cart():
    cart = Cart()
    assert cart.total() == 0

def test_calculate_total_with_discount():
    cart = Cart()
    cart.add_item("item", 1000)
    cart.apply_discount(10)  # 10% off
    assert cart.total() == 900
```

---

## Ссылки

- DOI: https://doi.org/10.5281/zenodo.19073543 (Generative Specification white paper, март 2026)
- pytest-cov: https://pypi.org/project/pytest-cov/
- mutmut: https://pypi.org/project/mutmut/
