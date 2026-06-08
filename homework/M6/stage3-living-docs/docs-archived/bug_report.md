# Bug Report — ProShop MERN

Полный аудит кодовой базы. Дата: 2026-04-27.

---

## 🔴 Critical

### 1. IDOR — любой юзер может оплатить чужой заказ
- **Где:** `backend/controllers/orderController.js` → `updateOrderToPaid`
- **Что не так:** Нет проверки `order.user.toString() === req.user._id.toString()`. Любой авторизованный пользователь может пометить любой заказ как оплаченный, зная его ID. Также `req.body.payer.email_address` без null-guard на `payer` — крашит сервер при неполном теле запроса (TypeError).
- **Как исправить:** Добавить ownership-проверку и `req.body.payer && req.body.payer.email_address` guard.

### 2. Удалённый юзер с валидным JWT крашит все защищённые эндпоинты
- **Где:** `backend/middleware/authMiddleware.js` → `protect`
- **Что не так:** `User.findById(decoded.id)` может вернуть `null` (юзер удалён, токен ещё жив). `req.user` становится `null`, downstream middleware `admin` крашится на `req.user.isAdmin`.
- **Как исправить:** После `findById` — `if (!req.user) { res.status(401); throw new Error('User not found') }`.

### 3. Повреждённый localStorage крашит приложение при загрузке
- **Где:** `frontend/src/store.js` → initialState (строки 56-66)
- **Что не так:** Три вызова `JSON.parse(localStorage.getItem(...))` без try/catch. Malformed JSON в любой из трёх ключей (`cartItems`, `userInfo`, `shippingAddress`) — необработанное исключение, белый экран.
- **Как исправить:** Обернуть каждое чтение в try/catch, при ошибке возвращать default value.

### 4. `updateProduct` стирает данные при неполном запросе
- **Где:** `backend/controllers/productController.js` → `updateProduct`
- **Что не так:** Все поля (`name`, `price`, `description`, `image`, `brand`, `category`, `countInStock`) слепо перезаписываются из `req.body` без fallback. Пропуск одного поля затирает существующее значение на `undefined`.
- **Как исправить:** Паттерн `product.name = name || product.name` или spread с дефолтами из текущего документа.

### 5. `getOrderById` — любой юзер видит чужие заказы
- **Где:** `backend/controllers/orderController.js` → `getOrderById`
- **Что не так:** Только проверка `protect` (авторизован ли). Нет ownership-проверки — IDOR. Любой авторизованный пользователь может читать чужие заказы перебором ID.
- **Как исправить:** Добавить `order.user.toString() === req.user._id.toString() || req.user.isAdmin`.

### 6. `createProductReview` — нет валидации рейтинга
- **Где:** `backend/controllers/productController.js` → `createProductReview`
- **Что не так:** `rating` не проверяется на диапазон 1-5. Значения 0, -1, или `"abc"` (NaN после Number()) молча принимаются и ломают средний рейтинг продукта.
- **Как исправить:** Добавить `if (!rating || rating < 1 || rating > 5) return res.status(400).json({ message: 'Rating must be 1-5' })`.

### 7. Нет валидации ObjectId в параметрах маршрутов
- **Где:** `backend/controllers/productController.js`, `orderController.js`, `userController.js` — все функции с `req.params.id`
- **Что не так:** Невалидный ObjectId (например `/api/products/abc`) вызывает Mongoose CastError → 500 вместо 400. Затронуто: `getProductById`, `deleteProduct`, `updateProduct`, `getOrderById`, `deleteUser`, `updateUser`.
- **Как исправить:** Добавить middleware `mongoose.Types.ObjectId.isValid(req.params.id)` или использовать `express-validator`.

---

## 🟡 Medium

### 8. Кнопка "Place Order" никогда не блокируется
- **Где:** `frontend/src/screens/PlaceOrderScreen.js` → `placeOrderHandler`
- **Что не так:** `cart.cartItems === 0` — сравнение массива с числом через `===` всегда `false`. Кнопка активна даже при пустой корзине.
- **Как исправить:** Заменить на `cart.cartItems.length === 0`.

### 9. Нет валидации входных данных при регистрации
- **Где:** `backend/controllers/userController.js` → `registerUser`
- **Что не так:** Нет проверки что `name`, `email`, `password` непустые. Нет валидации формата email. Нет минимальной длины пароля.
- **Как исправить:** Добавить проверки или использовать `express-validator`.

### 10. Нет проверки уникальности email при обновлении профиля
- **Где:** `backend/controllers/userController.js` → `updateUserProfile`, `updateUser`
- **Что не так:** `user.email = req.body.email || user.email` — если новый email уже занят, MongoDB вернёт duplicate-key error как 500 вместо понятного 400.
- **Как исправить:** Перед сохранением проверить `User.findOne({ email: req.body.email, _id: { $ne: user._id } })`.

### 11. Возврат всех пользователей/заказов без пагинации
- **Где:** `backend/controllers/userController.js` → `getUsers`, `backend/controllers/orderController.js` → `getOrders`
- **Что не так:** `User.find({})` и `Order.find({})` без limit/skip — при росте БД будет расти нагрузка и время ответа.
- **Как исправить:** Добавить пагинацию аналогично `getProducts`.

### 12. Hardcoded строка ошибки auth дублирована 15 раз
- **Где:** `frontend/src/actions/productActions.js`, `userActions.js`, `orderActions.js`
- **Что не так:** Строка `'Not authorized, token failed'` захардкожена в каждом catch-блоке (15 раз). Хрупкая связь с сервером — если текст ошибки на бэкенде изменится, все 15 мест молча перестанут ловить logout.
- **Как исправить:** Вынести в константу `AUTH_ERROR_MESSAGE` в constants, или проверять статус 401 вместо текста.

### 13. `addDecimals` пересоздаётся каждый рендер
- **Где:** `frontend/src/screens/PlaceOrderScreen.js`
- **Что не так:** Функция `addDecimals` определена внутри тела компонента — пересоздаётся на каждый рендер. Магические числа: налог 15% (`0.15`), порог бесплатной доставки `$100`, стоимость доставки `$100`.
- **Как исправить:** Вынести `addDecimals` и константы (`TAX_RATE`, `SHIPPING_COST`, `FREE_SHIPPING_THRESHOLD`) за пределы компонента.

### 14. Dead code — закомментированный Stripe
- **Где:** `frontend/src/screens/PaymentScreen.js` (строки 43-50)
- **Что не так:** Закомментированный блок Stripe payment. Мёртвый код в репозитории.
- **Как исправить:** Удалить или вынести в отдельную feature-ветку.

### 15. `console.log` в продакшн-коде
- **Где:** `frontend/src/screens/OrderScreen.js` → `successPay` handler (строка 80)
- **Что не так:** `console.log(paymentResult)` — debug-лог оставлен в продакшн-коде.
- **Как исправить:** Удалить.

### 16. Ошибка загрузки изображения молча проглатывается
- **Где:** `frontend/src/screens/ProductEditScreen.js` → `uploadFileHandler`
- **Что не так:** `console.error(error)` — юзер не получает уведомления если загрузка изображения не удалась. `e.target.files[0]` без проверки — cancel диалога выбора файла отправит `undefined` в formData.
- **Как исправить:** Добавить `setUploadError('Upload failed')` и проверку `if (!e.target.files[0]) return`.

### 17. Несогласованное имя константы
- **Где:** `frontend/src/constants/cartConstants.js` → `CART_CLEAR_ITEMS`
- **Что не так:** Имя константы `CART_CLEAR_ITEMS`, значение `'CART_RESET'`. Несоответствие — выглядит как баг после переименования.
- **Как исправить:** Унифицировать: либо `CART_CLEAR_ITEMS = 'CART_CLEAR_ITEMS'`, либо `CART_RESET = 'CART_RESET'`.

### 18. Нет rate limiting на auth-эндпоинтах
- **Где:** `backend/routes/userRoutes.js` → POST `/login`, POST `/`
- **Что не так:** Нет ограничения на количество попыток входа/регистрации. Уязвимость к brute-force атакам на пароли.
- **Как исправить:** Добавить `express-rate-limit` на auth-маршруты.

### 19. Deprecated `model.remove()` в Mongoose
- **Где:** `backend/controllers/productController.js` → `deleteProduct`, `backend/controllers/userController.js` → `deleteUser`
- **Что не так:** `product.remove()` и `user.remove()` — deprecated в Mongoose 6+. При обновлении Mongoose перестанет работать.
- **Как исправить:** Заменить на `await Product.findByIdAndDelete(req.params.id)` или `await product.deleteOne()`.

### 20. Deprecated Mongoose connection options
- **Где:** `backend/config/db.js` → `connectDB`
- **Что не так:** `useUnifiedTopology`, `useNewUrlParser`, `useCreateIndex` — deprecated в Mongoose 6+, генерируют warnings.
- **Как исправить:** Удалить options object, оставить только `mongoose.connect(process.env.MONGO_URI)`.

---

## 🟢 Cosmetic / Low Priority

### 21. Магические числа
- `backend/controllers/productController.js:getProducts` → `pageSize = 10`
- `backend/controllers/productController.js:getTopProducts` → `limit(3)`
- `backend/models/userModel.js` → bcrypt salt rounds `10`
- `backend/utils/generateToken.js` → `expiresIn: '30d'`
- `frontend/src/components/Rating.js` → star color `'#f8e825'`
- **Как исправить:** Вынести в named constants или env vars.

### 22. Hardcoded brand name
- `frontend/src/components/Header.js` → `ProShop`
- `frontend/src/components/Footer.js` → `Copyright ProShop`
- `frontend/src/components/Meta.js` → default title/description/keywords
- **Как исправить:** Вынести в config/constant.

### 23. Typo в keywords
- **Где:** `frontend/src/components/Meta.js` → default keywords
- **Что не так:** `'cheap electroincs'` вместо `'cheap electronics'`.
- **Как исправить:** Исправить опечатку.

### 24. Двойное чтение localStorage
- **Где:** `frontend/src/store.js` → initialState
- **Что не так:** `localStorage.getItem('cartItems')` вызывается дважды для каждого ключа — в условии и в JSON.parse. Избыточно.
- **Как исправить:** `const raw = localStorage.getItem('cartItems'); const cartItemsFromStorage = raw ? JSON.parse(raw) : []`.

### 25. Пустой JSX-блок
- **Где:** `frontend/src/screens/ProfileScreen.js` → строка 61
- **Что не так:** `{}` — пустой JSX-блок, не рендерит ничего. Мёртвый код.
- **Как исправить:** Удалить.

### 26. Нет CORS middleware
- **Где:** `backend/server.js`
- **Что не так:** Не импортирован `cors`. Работает только потому что frontend proxy подставляет тот же origin. При отдельном деплое фронтенда запросы будут блокироваться.
- **Как исправить:** `npm install cors` → `app.use(cors({ origin: 'http://localhost:3000' }))`.

### 27. Нет security headers (helmet)
- **Где:** `backend/server.js`
- **Что не так:** Отсутствует `helmet` — нет заголовков безопасности (X-Content-Type-Options, Strict-Transport-Security и др.).
- **Как исправить:** `npm install helmet` → `app.use(helmet())`.

---

## Outdated Dependencies

Актуально на дату аудита. Текущая → последняя стабильная:

| Package | Current | Latest | Notes |
|---|---|---|---|
| `mongoose` | 5.10.6 | 8.x | Breaking: remove deprecated options, `remove()` → `deleteOne()` |
| `react` / `react-dom` | 16.13.1 | 19.x | Breaking: hooks API changes, concurrent features |
| `react-scripts` | 3.4.3 | 5.x | Webpack 4 → 5, требует Node 16+ |
| `react-router-dom` | 5.2.0 | 7.x | Breaking: `<Switch>` → `<Routes>`, `useHistory` → `useNavigate` |
| `redux` | 4.0.5 | 5.x / Redux Toolkit | Legacy pattern — class-style createStore, manual triple actions |
| `axios` | 0.20.0 | 1.x | Critical CVE fix в 0.21.1 |
| `jsonwebtoken` | 8.5.1 | 9.x | |
| `express` | 4.17.1 | 5.x | |
| `multer` | 1.4.2 | 2.x | CVE-2022-24434 в текущей |
| `eslint` | 6.8.0 | 9.x | End-of-life |
| `@babel/plugin-proposal-*` | various | renamed | Все proposal-плагины переименованы в `plugin-transform-*` |
| `core-js` | 2.6 / 3.6 | 3.39+ | Старые версии вызывают slowdown до 100x в V8 |

Апгрейд всего стека — отдельная задача, требует поэтапного подхода (сначала Node 16 + react-scripts 5, затем React 18, затем Redux Toolkit, затем Mongoose 8).
