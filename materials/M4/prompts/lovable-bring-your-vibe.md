# Lovable: bring-your-vibe промпт

> **Когда использовать:** Первый промпт в новом Lovable-проекте — до того, как ИИ успеет нагенерировать дефолтный shadcn. Задаёт визуальное направление, шрифт, палитру, ритм анимаций и логику user journey одним блоком.
> **Inputs:** описание фичи/страницы, выбранный visual direction, референс-скриншот (опционально), 3-5 hex-цветов.
> **Output:** компонент или секция в заданном стиле — не generic shadcn, а с характером.

## Промпт

```
Build [feature description — e.g., "a SaaS pricing page for a developer tool"].

Visual direction: [pick ONE: premium / minimal / cinematic / brutalist / playful].

Style baseline:
- Reference screenshot: [paste screenshot OR describe: "similar to Linear.app dashboard"]
- Font: [specific name — e.g., Manrope / Geist / Space Grotesk / Playfair Display]
  NOT default Inter — it's overused, the result will look generic.
- Color palette: [3-5 hex values, e.g., #0f172a / #6366f1 / #22d3ee / #f1f5f9]
  Use these as semantic tokens: bg / primary / accent / foreground.
- Spacing scale: 8/16/24/32/48/64px only. No arbitrary values.
- Border radius: [e.g., 8px for buttons and inputs, 12px for cards, 9999px for pills]
- Animations: subtle scale(1.02) on hover, elements arrive in sequence with 80ms stagger
  (NOT all-at-once fade-in). Transitions: 150ms ease.

User journey (design follows this order, not aesthetics):
1. [What user sees first — e.g., "headline that states the value prop in 6 words"]
2. [What builds trust — e.g., "3 social proof data points, no logos, real numbers"]
3. [Primary CTA — e.g., "one button: 'Start free trial — no card required'"]

Build component-by-component, not full pages. Start with hero section only.
After I approve the hero, we move to the next section.

Hard constraints:
- No 2-column "with us / without us" comparison blocks.
- No linear-gradient purple/violet on backgrounds.
- No shadow-lg on cards — use background contrast for depth.
- Every interactive element must have hover, focus, and loading states.
- Dark mode via CSS variables only (--background, --foreground, --card).
  Never use Tailwind dark: prefixes.
```

## Объяснение

Lovable (как и любой vibe-coding инструмент) при первом промпте без явного контекста генерирует «среднее по рынку AI-сайтов»: Inter, синяя кнопка, серые карточки с `shadow-lg`, hero + 3 симметричных блока. Это происходит не потому что инструмент плохой — просто у него нет информации о вашем вкусе, и он использует наиболее частые паттерны из своих обучающих данных.

Ключевая идея этого промпта — передать вкус до генерации, а не исправлять результат после. Визуальный direction (`premium / minimal / cinematic / brutalist / playful`) работает как «слайдер»: каждое слово смещает модель в определённую область — у `minimal` меньше теней и больше пространства, `cinematic` даёт translucent surfaces и драматический контраст, `brutalist` убирает скругления и добавляет монострочный шрифт. Конкретный шрифт и palette закрепляют это направление числами.

Блок User Journey критичен: он заставляет модель думать о том, что пользователь делает на странице, а не о том, «как выглядит красивый сайт». Без этого блока ИИ оптимизирует под Dribbble-aesthetics: hero на весь экран, CTA под fold, карточки с иконками без действий. С блоком — сначала ценность, потом доверие, потом действие. Это основа UX.

## Вариации

**Вариация A — ultra-short (если уже есть DESIGN_SYSTEM.md в проекте):**

```
Build [feature]. Follow DESIGN_SYSTEM.md exactly.
Visual direction: minimal. User journey: [what first] → [trust] → [CTA].
Start with hero component only. Don't touch nav or footer yet.
```

**Вариация B — для мобильного приложения (не web):**

```
Build [screen name — e.g., "onboarding flow, 3 steps"].

Platform: mobile app (iOS-first design language).
Visual direction: [premium / minimal / playful].
Font: [e.g., SF Pro equivalent — use system-ui on web preview]
Colors: [3-5 hex] as semantic tokens.
Spacing: 16/24/32/48px. Touch targets: min 44×44px.
Animations: native-feel spring transitions (stiffness 300, damping 25).

User journey through the 3 screens:
1. [Screen 1 goal]
2. [Screen 2 goal]
3. [Screen 3 goal + CTA]

Build one screen at a time. Start with Screen 1 only.
```

**Вариация C — «I am frustrated» restart (когда предыдущие попытки не сработали):**

```
I am frustrated. The previous attempts gave me generic AI-looking output.
Here is specifically what went wrong:
- [e.g., "Used Inter font despite my instructions"]
- [e.g., "Generated 2-column comparison block I explicitly banned"]
- [e.g., "All elements faded in at once, not sequentially"]

Reset. Here is my exact style specification:
[paste full style baseline block from above]

Build hero section ONLY. Nothing else. Stop after hero and wait for feedback.
```

## Контекст

Промпт собирает несколько повторяющихся приёмов из практики Lovable / Bolt / Claude Design 2026: design buzzwords как «слайдеры», user journey в начале промпта, «Build by component, not full pages», pattern «I am frustrated» для сброса контекста. См. [docs.lovable.dev](https://docs.lovable.dev) — Plan Mode и AGENT.md.

## Связь с курсом

Блоки M4 F8 (best practices vibe-coding, пункты 1-7) и F9 (anti-AI guard-rails). Промпт реализует сразу несколько практик из F8: Build by component (#3), Real content (#4), Visual style before function (#5), Guardrails «не трогай X» (#6), Mobile breakpoints явно (#7).
