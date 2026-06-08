# Модуль 4 — Домашнее задание

> **Тема:** Дизайн-система и редизайн UI с AI.
> **Сложность:** Middle+ (browser-builder путь) / Senior+ (CC + agents путь).
> **Время:** ~4–8 часов (по бюджету токенов и количеству страниц).
> **Дедлайн:** объявляется отдельно перед стартом M5.
> **Куда сдавать:** PR в ваш форк `proshop_mern` + ссылка в LMS / чат курса.

---

## Цель

Применить единую дизайн-систему ко фронтенду `proshop_mern`. Сделать:

1. **Feature Dashboard в админке** — обязательно. Полный редизайн + интерактив (toggle, slider, поиск, фильтр, states).
2. **Редизайн остальных страниц** — сколько успеете / сколько хватит токенов. Минимум 1, идеал — все 16.
3. **`DESIGN.md` в корне репо** — единый источник правды о визуальном языке проекта.

Инструменты — ваш свободный выбор (Cursor / Claude Code / Bolt / v0 / Lovable / Pencil / Figma MCP / любая комбинация). Критерий — работающий результат.

---

## Что сделать

### 1. Feature Dashboard в admin (обязательно)

Страница для управления feature flags из `features.json` (M3). Должна жить **в admin-секции**: роут `/admin/featuredashboard`, проверка `userInfo.isAdmin`, ссылка из admin-dropdown в Header (НЕ в общем nav). Если у вас после M3 она в общем nav — первый шаг M4 это перенести в admin.

**Функционал:**
- Список фич — таблица или карточки с `name`, `status`, `traffic_percentage`, `last_modified`
- Статус-бейджи трёх цветов: Enabled зелёный / Testing синий / Disabled серый
- Toggle (включить / выключить фичу) — меняет цвет бейджа на UI-уровне
- Slider 0–100% для traffic_percentage — обновляет отображаемый процент
- Поиск по имени фичи
- Фильтр по статусу (Enabled / Testing / Disabled / All)

**Состояния (mandatory):**
- Loading skeleton
- Empty state (если фильтр ничего не нашёл)
- Error state (если данные не загрузились)

**Accessibility:**
- ARIA labels на интерактивных элементах
- Keyboard navigation (Tab, Enter, Space)

### 2. Редизайн остальных страниц

Применить `DESIGN.md` к страницам `proshop_mern`. **Сколько страниц — не принципиально**: кто сколько успеет, у кого сколько токенов хватит. Минимум — 1 страница (помимо Feature Dashboard). Идеал — все 16.

В отчёте обязательно укажите **список страниц, которые отредизайнили** (отметьте галочками в таблице ниже). Скриншоты не нужны — мы посмотрим в git diff.

### 3. DESIGN.md в корне репо

Файл `DESIGN.md` (или `DESIGN_SYSTEM.md`) — на выбор студента. В корне репо рядом с `CLAUDE.md` / `AGENTS.md`.

**Минимум 7 секций:**
- Color palette (semantic tokens, CSS variables)
- Typography (шрифт — НЕ Inter, или явное обоснование)
- Spacing scale (только кратные 8)
- Border radius scale
- Elevation / shadow approach
- Component patterns (cards, buttons, inputs, badges)
- Interactive states (hover, focus, loading, empty, error — для каждого элемента)

**Шаблон:** `templates/DESIGN_SYSTEM.md`. Готовый пример: `design-system-pack-example/`.

**Anti-AI-slop guards:** дополнительная секция в `DESIGN.md` с правилами, которые не закрываются стандартными секциями (gradients, 2-col comparison, generic shadcn, UX-first). Готовый блок — в `anti-slop-supplement.md` в этой папке. Скопируйте оттуда.

### 4. Внедрить DESIGN.md в rules-файл вашей IDE

Чтобы AI читал `DESIGN.md` при каждой генерации UI:

| IDE | Куда добавить ссылку |
|---|---|
| Claude Code | `CLAUDE.md`: `## Design rules: see ./DESIGN.md` |
| Codex CLI | `AGENTS.md`: `## Design rules: see ./DESIGN.md` |
| Cursor | `.cursor/rules/design.mdc` (front-matter `applyTo: "**/*"`) |
| Copilot | `.github/copilot-instructions.md`: ссылка на `./DESIGN.md` |
| Windsurf | `.windsurfrules`: ссылка на `./DESIGN.md` |

---

## Список страниц `proshop_mern`

Полный инвентарь — для редизайна и для подтверждения в отчёте (отметьте галочками что сделали):

| # | Page | Route | File | Видимость | Сделал? |
|---|------|-------|------|-----------|---------|
| 1 | Home / Search results | `/`, `/search/:keyword`, `/page/:n` | `HomeScreen.js` | public | [ ] |
| 2 | Product details | `/product/:id` | `ProductScreen.js` | public | [ ] |
| 3 | Cart | `/cart/:id?` | `CartScreen.js` | public | [ ] |
| 4 | Login | `/login` | `LoginScreen.js` | public | [ ] |
| 5 | Register | `/register` | `RegisterScreen.js` | public | [ ] |
| 6 | Profile | `/profile` | `ProfileScreen.js` | auth | [ ] |
| 7 | Shipping | `/shipping` | `ShippingScreen.js` | auth | [ ] |
| 8 | Payment | `/payment` | `PaymentScreen.js` | auth | [ ] |
| 9 | Place Order | `/placeorder` | `PlaceOrderScreen.js` | auth | [ ] |
| 10 | Order details | `/order/:id` | `OrderScreen.js` | auth | [ ] |
| 11 | Admin: Users list | `/admin/userlist` | `UserListScreen.js` | admin | [ ] |
| 12 | Admin: User edit | `/admin/user/:id/edit` | `UserEditScreen.js` | admin | [ ] |
| 13 | Admin: Products list | `/admin/productlist` | `ProductListScreen.js` | admin | [ ] |
| 14 | Admin: Product edit | `/admin/product/:id/edit` | `ProductEditScreen.js` | admin | [ ] |
| 15 | Admin: Orders list | `/admin/orderlist` | `OrderListScreen.js` | admin | [ ] |
| 16 | **Admin: Feature Dashboard** | `/admin/featuredashboard` | `FeatureDashboardScreen.js` | admin | [x] **обязательно** |

Приоритеты при дефиците бюджета: high-traffic public (Home, Product, Cart, Checkout) → auth (Login, Register, Profile) → admin.

---

## Формат сдачи

```
proshop_mern/
├── DESIGN.md                   ← в корне репо рядом с CLAUDE.md / AGENTS.md
├── CLAUDE.md (или AGENTS.md / .cursor/rules/design.mdc) — со ссылкой на DESIGN.md
├── frontend/src/screens/
│   ├── FeatureDashboardScreen.js   ← редизайн (обязательно)
│   ├── HomeScreen.js               ← если редизайнили
│   └── ...                          ← остальные
└── homework/M4/
    └── README.md               ← краткий отчёт
```

Скриншоты не нужны — будем проверять через git (diff + локальный запуск).

В `README.md` отчёта обязательно:
- Список редизайненных страниц (галочками по таблице ниже)
- Какой инструмент(ы) использовали
- Component decisions (что взяли готовым, что кастомно)

---

## Чеклист (бинарно — пройдитесь ПЕРЕД PR)

### Feature Dashboard (обязательно)

- [ ] Страница в admin: роут `/admin/featuredashboard`, проверка `isAdmin`, ссылка в admin-dropdown в Header (НЕ в общем nav)
- [ ] Список фич из `features.json` отображается
- [ ] Статус-бейджи трёх цветов: Enabled / Testing / Disabled
- [ ] Toggle меняет цвет бейджа при клике
- [ ] Slider 0–100 обновляет процент traffic_percentage
- [ ] Поиск по имени фичи работает
- [ ] Фильтр по статусу работает
- [ ] Loading skeleton, Empty state, Error state — присутствуют
- [ ] ARIA labels + Keyboard navigation

### Редизайн остальных страниц

- [ ] Минимум 1 страница (помимо Feature Dashboard) редизайнена
- [ ] В README указан список редизайненных страниц (по таблице выше)

### DESIGN.md

- [ ] `DESIGN.md` в корне репо рядом с `CLAUDE.md` / `AGENTS.md`
- [ ] Минимум 7 секций (color / typography / spacing / radius / elevation / components / states)
- [ ] Шрифт — не Inter (или явное обоснование почему Inter)
- [ ] Spacing scale — только числа кратные 8
- [ ] Anti-AI-slop guards секция добавлена (из `anti-slop-supplement.md`)
- [ ] В rules-файле IDE добавлена ссылка `## Design rules: see ./DESIGN.md`

### Anti-AI-slop визуальный аудит

- [ ] Нет cringe-градиентов (фиолетовые / радужные)
- [ ] Нет 2-column comparison blocks
- [ ] Нет heavy borders на карточках
- [ ] Hover state есть на кнопках
- [ ] Focus state виден при keyboard navigation
- [ ] Loading state — skeleton, не просто спиннер
- [ ] Все отступы кратны 8
- [ ] shadcn (если используете) — кастомизирован, не дефолтный slate/zinc

### Финал

- [ ] PR создан
- [ ] Ссылка отправлена в LMS / чат курса

---

## Полезные ресурсы

| Что | Где |
|-----|-----|
| Шаблон DESIGN.md | `templates/DESIGN_SYSTEM.md` |
| Готовый пример пакета | `design-system-pack-example/` |
| Anti-AI-slop supplement | `anti-slop-supplement.md` |
| 12 признаков AI-look | `cheatsheets/12-signs-of-ai-look.md` |
| Промпт reverse-design | `prompts/reverse-design.md` |
| Данные: features.json | `M3/project-data/features.json` |
| Агенты UX / shadcn / a11y | `agents/` |
| TweakCN (визуальный редактор shadcn-тем) | https://tweakcn.com |

---

*M4 — HSS AI-dev L1. Дедлайн и способ сдачи — в чате курса.*
