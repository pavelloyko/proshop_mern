# Report

## Primary IDE
VS Code + Claude Code (CLI)

## Local Launch Confirmation
Запустил локально через Docker MongoDB + npm run dev (Node v16, backend :5001, frontend :3000).

## Rules Diff

Что добавлено вручную поверх auto-generated CLAUDE.md:

- **Environment Setup Gotchas** — автоген не мог знать, что на macOS порт 5000 занят AirPlay Receiver, что npm cache ломается правами доступа, и что node_modules нужно удалять после смены версии Node через nvm. Всё это выяснилось в процессе запуска проекта.

- **Deployment / Infrastructure Notes** — автоген увидел Procfile, но не мог infer, что проект привязан к Heroku и что react-scripts 3.4.3 намертво привязан к webpack 4, что делает апгрейд нетривиальной задачей.

- **When Adding New Backend Features** — автоген не мог знать конвенцию о том, что при добавлении новой модели нужно обновить seeder.js, что auth middleware подключается вручную к каждому роуту, и что новые Redux-слайсы требуют регистрации в combineReducers + localStorage.

- **Node.js v16 constraint** — автоген увидел package.json, но не мог узнать из кода, что Node v25 ломает и backend (buffer-equal-constant-time), и frontend (webpack 4 crypto hash). Это выяснилось только при запуске.

- **Port sync requirement** — автоген не мог вывести связь между PORT в .env и proxy в frontend/package.json. Это неочевидная зависимость, которую легко сломать, меняя только одно значение.

- **Team Conventions** — правила работы с git и PR (именование веток, scope-префиксы, чеклист перед PR). Автоген не имеет доступа к командным процессам.

- **Local Gotchas** — react-router-dom v5 vs v6, порядок роутов в Express, vendored bootstrap.min.css. Автоген не может отличить "работает" от "работает случайно из-за порядка регистрации".

- **AI Collaboration Preferences** — язык объяснений (русский), запрет на рефакторинг вне задачи, требование списка затронутых файлов до написания кода. Это личные предпочтения, которые невозможно вывести из кода.
