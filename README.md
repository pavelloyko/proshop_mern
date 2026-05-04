# ProShop

eCommerce платформа на MERN-стеке для онлайн-магазина с админ-панелью. Учебный проект курса Brad Traversy (MERN eCommerce from scratch).

Функционал: каталог товаров с поиском и пагинацией, корзина, оформление заказа, PayPal-оплата (sandbox), отзывы и рейтинги, профили пользователей, админ-панель для управления товарами/пользователями/заказами.

## Tech Stack

| Слои | Технологии | Версия |
|---|---|---|
| Runtime | Node.js | **v16** (обязательно, см. Troubleshooting) |
| Backend | Express, Mongoose, JWT, bcryptjs, multer | Express 4.x, Mongoose 5.x |
| Frontend | React, Redux + Thunk, React-Bootstrap, Axios | React 16.x, React Router 5.x |
| Database | MongoDB | 7.x (Docker) или локальная установка |
| Payments | PayPal (react-paypal-button-v2) | Sandbox mode |

## Project Structure

```
proshop_mern/
├── backend/
│   ├── config/db.js          # MongoDB connection
│   ├── controllers/          # Express route handlers (per resource)
│   ├── data/                 # Seed data (users.js, products.js)
│   ├── middleware/            # auth (JWT + admin check), error handler
│   ├── models/               # Mongoose schemas (Product, User, Order)
│   ├── routes/               # Express routers (per resource)
│   ├── utils/                # generateToken (JWT helper)
│   ├── features.json          # Live feature flags (edited by MCP server)
│   ├── seeder.js             # DB seed script (import/destroy)
│   └── server.js             # Entry point
├── frontend/
│   ├── public/               # Static assets, product images
│   └── src/
│       ├── actions/          # Redux actions (product, user, order, cart)
│       ├── components/       # Reusable UI (Header, Footer, Product card, etc.)
│       ├── constants/        # Redux action type strings
│       ├── reducers/         # Redux reducers
│       ├── screens/          # Page-level components (one per route)
│       ├── App.js            # Router setup
│       ├── store.js          # Redux store (combineReducers + localStorage)
│       └── bootstrap.min.css # Vendored Bootstrap (do not edit)
├── uploads/                  # User-uploaded product images (multer)
├── .env.example              # Environment variables template
├── CLAUDE.md                 # AI assistant rules file
└── package.json              # Backend deps + concurrently/nodemon
```

## Quick Start

### Prerequisites

- **Node.js v16** — проект не работает на Node 18+ (webpack 4 и buffer-equal-constant-time несовместимы). Используйте [nvm](https://github.com/nvm-sh/nvm):
  ```bash
  nvm install 16
  nvm use 16
  ```
- **MongoDB** — любой способ:
  ```bash
  # Вариант 1: Docker (рекомендуется)
  docker run -d -p 27017:27017 --name mongo mongo:7

  # Вариант 2: Homebrew
  brew tap mongodb/brew
  brew install mongodb-community
  brew services start mongodb-community
  ```

### Environment Variables

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `NODE_ENV` | Режим запуска | `development` |
| `PORT` | Порт backend | `5001` (не 5000 — занят AirPlay на macOS) |
| `MONGO_URI` | Строка подключения MongoDB | `mongodb://localhost:27017/proshop` |
| `JWT_SECRET` | Секрет для JWT-токенов | любая строка |
| `PAYPAL_CLIENT_ID` | Client ID из PayPal Developer Sandbox | получить на [developer.paypal.com](https://developer.paypal.com) |

### Install & Run

```bash
# Клонировать
git clone https://github.com/pavelloyko/proshop_mern.git
cd proshop_mern

# Установить зависимости (backend + frontend)
npm install && cd frontend && npm install && cd ..

# Заполнить базу тестовыми данными
npm run data:import

# Запустить (backend :5001 + frontend :3000)
npm run dev
```

Открыть **http://localhost:3000**

### Seed Data Accounts

| Email | Password | Role |
|---|---|---|
| admin@example.com | 123456 | Admin |
| john@example.com | 123456 | Customer |
| jane@example.com | 123456 | Customer |

### Useful Commands

```bash
npm run dev           # Backend + Frontend concurrently
npm run server        # Backend only (nodemon)
npm run client        # Frontend only
npm run data:import   # Seed database
npm run data:destroy  # Wipe all data
```

## Troubleshooting

### `EACCES: permission denied` при npm install

npm cache принадлежит другому пользователю:
```bash
sudo chown -R $(whoami) ~/.npm
npm cache clean --force
```

### `ERR_OSSL_EVP_UNSUPPORTED` или `Cannot read properties of undefined (reading 'prototype')`

У вас Node.js 18+. Проект требует **v16**:
```bash
nvm install 16
nvm use 16
rm -rf node_modules frontend/node_modules package-lock.json frontend/package-lock.json
npm install && cd frontend && npm install && cd ..
```

### `EADDRINUSE: address already in use :::5000`

На macOS порт 5000 занят AirPlay Receiver. Два варианта:
1. Используйте порт 5001 (уже настроено в `.env.example`)
2. Отключите: Системные настройки → Основные → AirDrop и Handoff → выключите AirPlay Receiver

Если порт 5001 тоже занят:
```bash
lsof -ti:5001 | xargs kill -9
```

### MongoDB connection error

Убедитесь что MongoDB запущена:
```bash
# Docker
docker ps                    # проверить статус
docker start mongo            # запустить контейнер

# Homebrew
brew services list            # проверить статус
brew services start mongodb-community
```

### `npm run dev` не запускается после смены Node версии

Удалите node_modules и переустановите:
```bash
rm -rf node_modules frontend/node_modules
npm install && cd frontend && npm install && cd ..
```

### PayPal оплата не работает

1. Зарегистрируйтесь на [developer.paypal.com](https://developer.paypal.com)
2. Dashboard → My Apps & Credentials → **Sandbox** → Create App
3. Скопируйте Client ID в `.env` (`PAYPAL_CLIENT_ID`)
4. Перезапустите сервер
5. Для тестовой оплаты используйте sandbox Personal account (Dashboard → Sandbox → Accounts)

## Feature Flags API

Сервер читает `backend/features.json` на **каждый запрос** (без кеширования), поэтому изменения файла видны сразу — без рестарта.

### Эндпоинты

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/api/feature-flags` | Все фича-флаги |
| `GET` | `/api/feature-flags/:name` | Один флаг по ключу (например `search_v2`) |

### Проверка

```bash
# Запустить сервер
npm run dev

# Все флаги
curl http://localhost:5001/api/feature-flags

# Один флаг
curl http://localhost:5001/api/feature-flags/search_v2
```

Или откройте http://localhost:5001/api/feature-flags в браузере — должен вернуться JSON со списком всех фичей из `backend/features.json`.

## License

MIT © [Traversy Media](https://traversymedia.com)
