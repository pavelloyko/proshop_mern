# Cheatsheet: 12 признаков AI-look в дизайне

> Без guard-rails AI генерирует одно и то же: generic Inter, фиолетовые градиенты,
> толстые границы, двухколоночные блоки. Сообщество называет это «AI slop» или
> «дефолтный shadcn». 12 паттернов диагностируются за 30 секунд.

---

## Магическая фраза

> **"Be a human designer so it doesn't look like AI. With design taste."**

Ставь первой строкой в системный промпт — смещает модель от «среднего по больнице»
к curated примерам с высоким рейтингом.

---

## Таблица: 12 признаков + как избежать

| # | Признак | Что AI генерирует | Guard-rail в DESIGN.md / промпте |
|---|---------|-------------------|----------------------------------|
| 1 | Cringe градиенты | `linear-gradient(135deg, #6366f1, #a855f7)` на hero | `«avoid cringe gradients, use clean white/gray/black/metallic»` |
| 2 | 2-col comparison blocks | «Без нас ❌ / С нами ✅» рядом | `«No 2-column comparison layouts. Use ASCII wireframe FIRST to lock layout.»` |
| 3 | Inter везде | `font-family: 'Inter'` без выбора | `«Font: Manrope / Geist / Space Grotesk — NOT default Inter»` |
| 4 | Cramped layouts | padding 12-16px вместо 48-64px | `«Generous spacing, plenty of whitespace. Units: 8/16/24/32/48/64px only.»` |
| 5 | Heavy borders | `border: 2px solid #374151` на каждой карточке | `«Cards: 1px border at 10% opacity. NEVER heavy 2px borders.»` |
| 6 | `shadow-lg` рефлекторно | box-shadow на каждой карточке, кнопке, попапе | `«NO box shadows. Depth from background contrast only: 3 levels.»` |
| 7 | `dark:bg-gray-900` = dark mode | Tailwind `dark:` prefix на всех компонентах | `«Dark mode via CSS variables only: --bg, --fg, --card. NO dark: prefixes.»` |
| 8 | Random animations | fade-in на всех элементах одновременно | `«Animations: purposeful only — hover, transitions, skeletons. NO decorative fade-in on static.»` |
| 9 | Generic shadcn out-of-box | нейтральный gray + zinc + slate без кастомизации | `«shadcn theme MUST be customized via CSS variables. Use TweakCN for brand tokens.»` |
| 10 | Нет hover/focus/loading | кнопки без hover, инпуты без focus ring | `«EVERY interactive element MUST have: hover, focus, active, loading, empty, error states.»` |
| 11 | UX ≠ journey | hero на весь экран, CTA ниже fold | `«UX-first: define user journey BEFORE visual style. Where is primary CTA?»` |
| 12 | `text-blue-600` как accent | кнопки, ссылки, иконки — всё blue-600 | `«Accent: use --accent from DESIGN.md. NEVER Tailwind color utility as brand color.»` |

---

## Быстрое исправление: блок Design Principles в CLAUDE.md

Скопируй в системный промпт или в `CLAUDE.md` своего проекта:

```markdown
## Design Principles (always apply)
- Generous spacing — plenty of whitespace, never cramped
- Cards — subtle elevation, NEVER heavy borders
- NO box shadows — depth from background contrast (3 levels: page/card/card-alt)
- Interactive states — every element has hover, focus, loading, empty states
- NEVER: 2-col comparison blocks, cringe gradients, default Inter, dark:bg-gray-900
- Be a human designer so it doesn't look like AI. With design taste.
```

Полная версия с токенами: `../prompts/anti-ai-slop-guards.md`

---

## Шрифты вместо Inter

| Контекст | Шрифт |
|----------|-------|
| Modern / tech | Manrope, Geist, Space Grotesk |
| Luxury / премиум | Playfair Display, Fraunces, Cormorant |
| Editorial / медиа | Inter Display (не дефолтный Inter) |
| Mono / код | IBM Plex Mono, JetBrains Mono |

> 80% of all digital design is typography. If you leave your font choice to AI, you'll end up with Inter — overused to the point of invisibility.

---

## Связанные материалы

- `../prompts/anti-ai-slop-guards.md` — полный блок guard-rails
- `../prompts/reverse-design-extract.md` — извлечь DESIGN.md из скриншота
- `../prompts/ascii-wireframe-lock.md` — зафиксировать layout до кода
- `10-vibecoding-best-practices.md` — системные правила работы с AI

---

## Контекст

12 признаков выше — повторяющиеся паттерны generic «AI-look», которые независимо подмечают разные практики vibe-coding 2026 года. Каждый guard-rail в третьей колонке устраняет один конкретный признак.
