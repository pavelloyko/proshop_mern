# shadcn-components — shared config для shadcn-агентов

Папка содержит общие справочные файлы, которые используют ВСЕ 4 shadcn-агента
(`shadcn-requirements-analyzer`, `shadcn-component-researcher`,
`shadcn-implementation-builder`, `shadcn-quick-helper`).

## Файлы

### `components.json`

Shadcn project config с **35+ registries** — каталог всех доступных источников
готовых компонентов и блоков. Положи этот файл в корень своего проекта рядом
с `package.json`.

**Что внутри (выборочно):**
- `@aceternity` — анимированные компоненты (Aceternity UI)
- `@cult-ui` — современные паттерны
- `@magicui` — премиум-эффекты
- `@kibo-ui`, `@kokonutui`, `@originui`, `@reui` — production-ready блоки
- `@blocks` — каталог готовых hero / pricing / dashboard секций
- `@motion-primitives` — анимация-компоненты
- `@nativeui` — мобильные компоненты
- `@formcn` — формы
- + 25+ других registries

**Как использовать:**

1. Скопируй `components.json` в корень своего проекта.
2. Установи компоненты через shadcn CLI:
   ```bash
   npx shadcn@latest add @aceternity/glow-card
   npx shadcn@latest add @magicui/animated-button
   npx shadcn@latest add @blocks/hero-section
   ```
3. Shadcn-агенты читают этот файл и понимают какие registries доступны.

## Связанный пример

Файл `shadcn-component-researcher/library-rule-example.mdc` — Cursor-правило,
описывающее пошаговый workflow работы с библиотекой готовых компонентов
(анализ ТЗ → список компонентов → исследование документации → стилизация →
реализация). Это эталонный пример того, как Component Researcher должен
действовать.

