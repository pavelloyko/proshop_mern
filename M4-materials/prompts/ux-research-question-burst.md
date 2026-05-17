# UX Research: Question Burst

> **Когда использовать:** На старте проекта, когда требования размытые — есть идея или бизнес-описание, но не понятно кто пользователь, какой сценарий, где CTA. Запускай до того как дать задачу дизайн-агенту или открыть Lovable.
> **Inputs:** Описание продукта или фичи (1-3 предложения) — может быть очень черновым.
> **Output:** 8-10 уточняющих вопросов, которые нужно ответить перед началом дизайна. БЕЗ каких-либо ответов, решений или предложений.

## Промпт

```
You are a product design consultant running a Question Burst session.

I will describe a product or feature I want to build.
Your ONLY job: generate 8-10 specific clarifying questions that must be answered
before any design or development begins.

Rules:
- Do NOT suggest solutions
- Do NOT answer your own questions
- Do NOT describe what the interface could look like
- Output ONLY the numbered list of questions

Focus your questions on:
- Who exactly are the users and what is their level of sophistication?
- What is the single most important action a user should take on this screen?
- What does success look like for the user (not the business)?
- What edge cases will definitely happen (errors, empty states, scale, permissions)?
- What similar products has the user seen that they like or dislike?
- What happens AFTER the main action — what is the next step?
- What data/content will be missing or unavailable at launch?
- Who else is involved in this flow (admins, approvers, other roles)?

Product idea: [DESCRIBE YOUR PRODUCT OR FEATURE HERE]
```

## Объяснение

Большинство AI-инструментов и большинство разработчиков — over-confident generators. Дашь им "сделай dashboard для управления задачами" — получишь generic карточки с синими кнопками, потому что нейронка заполнила пробелы своими предположениями.

Question Burst переворачивает паттерн: агент не пытается угадать что ты хочешь — он вытаскивает информацию, которая нужна, чтобы сделать правильный выбор. Это не слабость агента, это его сила.

**Почему 8-10 вопросов, а не 3-5:** меньше вопросов — агент выбирает "безопасные" (очевидные). 8-10 вопросов вынуждают копать глубже: edge cases, разные роли, post-action flow.

**Почему "Output ONLY questions" в промпте:** без этого ограничения LLM начинает отвечать на свои же вопросы ("You might consider..."), что убивает суть паттерна.

**5-10 раундов:** один раунд вопросов часто порождает следующий. После ответов на первый раунд — запусти снова с контекстом. За 2-3 итерации требования кристаллизуются настолько, что дизайн-агент получает реальное ТЗ, а не фантазию.

## Вариации / Tips

**Вариация для студента, который не может сформулировать задачу:**
Вместо описания фичи — попроси студента описать проблему которую он решает. Question Burst сам вытащит из этого фичу.

**Вариация для MVP-контекста:**
Добавь в промпт: `Also ask: what is the absolute minimum that would make this useful for the first 10 users?`

**Tip: комбинируй с ASCII Wireframe.**
Question Burst кристаллизует ЧТО. ASCII Wireframe фиксирует КАК расположено на экране. Запускай их последовательно: сначала вопросы, потом wireframe на основе ответов.

**Tip: не пропускай edge cases.**
Самые ценные вопросы про состояния: пустая БД, ошибка сети, нет прав доступа, контент слишком длинный. AI по умолчанию проектирует happy path — Question Burst это исправляет.

## Контекст

Question Burst — паттерн из «UX/UI brainstorming agents» практик 2026: вместо того, чтобы сразу генерить UI, агент сначала задаёт фиксированный набор вопросов о пользователе, контексте использования и edge cases. Без этого шага AI проектирует happy path и пропускает empty/error/loading-состояния.

## Связь с курсом

**M4, блок F4 (0:21-0:27):** "UX ≠ UI. Это два разных шага."

Этот промпт — практическая реализация главного тезиса блока: нельзя идти сразу в Lovable с "сделай красиво". Question Burst — это инструмент для UX-шага, который студенты чаще всего пропускают.

Используй вместе с агентами из `M4/agents/ux-designer/` и `M4/agents/ux-designer-basic/` — они подхватывают работу после того, как Question Burst кристаллизовал требования.
