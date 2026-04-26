# Report

## Primary IDE
VS Code + Claude Code (CLI)

## Rules Diff

Что добавлено вручную поверх auto-generated CLAUDE.md:

- **Environment Setup Gotchas** — автоген не мог знать, что на macOS порт 5000 занят AirPlay Receiver, что npm cache ломается правами доступа, и что node_modules нужно удалять после смены версии Node через nvm. Всё это выяснилось в процессе запуска проекта.

- **Deployment / Infrastructure Notes** — автоген увидел Procfile, но не мог infer, что проект привязан к Heroku и что react-scripts 3.4.3 намертво привязан к webpack 4, что делает апгрейд нетривиальной задачей.

- **When Adding New Backend Features** — автоген не мог знать конвенцию о том, что при добавлении новой модели нужно обновить seeder.js, что auth middleware подключается вручную к каждому роуту, и что новые Redux-слайсы требуют регистрации в combineReducers + localStorage.

- **Node.js v16 constraint** — автоген увидел package.json, но не мог узнать из кода, что Node v25 ломает и backend (buffer-equal-constant-time), и frontend (webpack 4 crypto hash). Это выяснилось только при запуске.

- **Port sync requirement** — автоген не мог вывести связь между PORT в .env и proxy в frontend/package.json. Это неочевидная зависимость, которую легко сломать, меняя только одно значение.
