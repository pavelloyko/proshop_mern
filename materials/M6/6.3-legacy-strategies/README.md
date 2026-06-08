# Topic 6.3 — Стратегии работы с Legacy

> Модуль 6, Тема 6.3 — «AI-Конвейер и Legacy: Промышленный стандарт»

---

## Что в этой папке

| Файл | Что внутри |
|---|---|
| `recipe-cc-reverse-engineering.md` | 4-шаговый рецепт reverse engineering через Claude Code (P22 workflow). Промпт-шаблоны, пример на реальном файле, ограничения по размеру контекста |
| `recipe-risk-mitigation.md` | 7 правил безопасного AI-рефакторинга + 5-фазный фреймворк модернизации. «Do NOT» промпт-шаблоны. Кейсы Knight Capital и Moonwell DeFi |
| `legacy-incidents.md` | 3 реальных production-инцидента + 3 анти-паттерна: что произошло, чему учит, как обнаружить раньше |

---

## Главные идеи

### 1. Инверсия продуктивности по типу кодовой базы

| Стек / контекст | Реальный прирост AI |
|---|---|
| Greenfield + 100% AI-код | +50× ускорение |
| Mainstream migration (Py2→3, JS→TS) | 40-70% сокращение времени |
| Enterprise legacy 25+ лет | **−20% продуктивности** у senior-разработчиков |
| C / embedded / industrial | +10-15% (training data dominated by web/JS/Python) |
| COBOL через generic LLM | 40-60% accuracy vs 85-95% у специализированных transpilers |
| AS400 / DB2 / 1С (без API) | AI-агенты «просто не работают» |

Спрашивайте у вендора показывать ROI на ВАШЕМ типе кода, не на median.

### 2. 70% переписываний проваливаются — AI не меняет цифру

AI меняет **состав рисков**, не их вероятность. Без правильного процесса AI не сокращает риск, а маскирует его.

**Почему переписывания проваливаются с AI:**
- AI убирает код который выглядит как дублирование, но несёт намеренное поведение
- AI не знает tribal knowledge: Slack-треды за полгода, post-mortems, institutional memory
- AI тестирует code coverage, не correctness; 40% AI PR fails потому что agent stays in own layer

### 3. Где AI реально работает в 2025-2026

- **Генерация документации** для undocumented legacy: результат за минуты
- **Characterization tests**: быстро покрывает happy paths (но пропускает production edge cases)
- **Механические миграции** на mainstream target stack (Py2→3, JS→TS, React class→hooks): 40-70% сокращение времени
- **Reverse engineering через Claude Code**: 4-шаговый workflow (P22) для модулей до 250K токенов
- **DB schema migration**: Expand-Contract pattern + auto-rollback + L1-L2-L3 валидация

### 4. Где AI системно проваливается

- **Endless fix-cycling**: производственный инцидент — один и тот же ответ 58 раз подряд
- **Silent feature deletion**: копирует код, переписывает, grep'ает частичные ссылки, не удаляет старый файл, рапортует «готово»
- **Fake test coverage**: 100% coverage тестами без assert / `2+2=4` / удаление падающих тестов

---

## Порядок чтения

1. **Начни с `legacy-incidents.md`** — 3 реальных инцидента дают интуицию о том, что может пойти не так
2. **Читай `recipe-cc-reverse-engineering.md`** — базовый workflow для изучения незнакомого кода
3. **Читай `recipe-risk-mitigation.md`** — правила и фреймворк для безопасного рефакторинга

---

## Связанные материалы этой темы

- **Strangler Fig pattern**: [martinfowler.com/bliki/StranglerFigApplication.html](https://martinfowler.com/bliki/StranglerFigApplication.html) — поэтапная замена legacy-компонентов без остановки системы
- **Moonwell DeFi incident ($1.78M)**: [docs.moonwell.fi/moonwell/protocol/security](https://docs.moonwell.fi/moonwell/protocol/security) — кейс пропущенного domain review
- **Knight Capital 2012 postmortem**: публичный разбор $460M потерь за 45 минут (поиск "Knight Capital 2012 trading loss")
- **IBM CodeConcise / Thoughtworks**: AST + knowledge graph + LLM для кодовых баз 500k+ LOC; специализация на COBOL/Java monolith
- **Claude Code official docs**: [docs.anthropic.com/en/docs/claude-code](https://docs.anthropic.com/en/docs/claude-code)
