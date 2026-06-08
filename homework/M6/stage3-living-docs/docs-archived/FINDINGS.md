# FINDINGS — proshop_mern

| # | Риск | Где | Что | Как фиксить | Статус |
|---|------|-----|-----|-------------|--------|
| 1 | 🔴 | backend/controllers/orderController.js::updateOrderToPaid | Нет проверки владельца заказа — любой юзер может оплатить чужой (IDOR). Также req.body.payer без null-guard крашит сервер | Добавить ownership-проверку и null-guard на payer | 🔴 not yet |
| 2 | 🔴 | backend/middleware/authMiddleware.js::protect | User.findById возвращает null если юзер удалён — req.user=null крашит downstream admin middleware | Добавить if (!req.user) после findById | 🔴 not yet |
| 3 | 🔴 | frontend/src/store.js::initialState | JSON.parse(localStorage) без try/catch — malformed JSON крашит приложение при загрузке | Обернуть каждое чтение в try/catch | ✅ fixed in commit 28e8613 |
| 4 | 🔴 | backend/controllers/productController.js::updateProduct | Все поля слепо перезаписываются из req.body — пропуск поля затирает значение на undefined | Использовать fallback pattern: name \|\| product.name | 🔴 not yet |
| 5 | 🔴 | backend/controllers/orderController.js::getOrderById | Нет ownership-проверки — любой авторизованный юзер видит чужие заказы (IDOR) | Добавить проверку order.user === req.user._id \|\| isAdmin | 🔴 not yet |
| 6 | 🔴 | backend/controllers/productController.js::createProductReview | Нет валидации rating на диапазон 1-5 — значения 0/NaN ломают средний рейтинг | Добавить guard: if rating < 1 \|\| rating > 5 return 400 | 🔴 not yet |
| 7 | 🔴 | backend/controllers/*.js — все функции с req.params.id | Невалидный ObjectId вызывает Mongoose CastError → 500 вместо 400 | Добавить ObjectId validation middleware | 🔴 not yet |
| 8 | 🟡 | frontend/src/screens/PlaceOrderScreen.js | cart.cartItems === 0 — сравнение массива с числом всегда false, кнопка никогда не блокируется | Заменить на cart.cartItems.length === 0 | 🔴 not yet |
| 9 | 🟡 | backend/controllers/userController.js::registerUser | Нет валидации name/email/password на непустоту, нет проверки формата email и длины пароля | Добавить express-validator или ручные проверки | 🔴 not yet |
| 10 | 🟡 | backend/controllers/userController.js::updateUserProfile | Нет проверки уникальности email — duplicate-key error как 500 вместо 400 | findOne по email с исключением текущего _id | 🔴 not yet |
| 11 | 🟡 | backend/controllers/userController.js::getUsers, orderController.js::getOrders | Возврат всех записей без пагинации — рост БД = рост нагрузки | Добавить pagination по аналогии с getProducts | 🔴 not yet |
| 12 | 🟡 | frontend/src/actions/*.js (15 мест) | Hardcoded 'Not authorized, token failed' — хрупкая связь с сервером, дублирование 15 раз | Вынести в константу или проверять HTTP 401 | 🔴 not yet |
| 13 | 🟡 | backend/routes/userRoutes.js::POST /login | Нет rate limiting — уязвимость к brute-force | Добавить express-rate-limit на auth-маршруты | 🔴 not yet |
| 14 | 🟡 | frontend/src/screens/ProductEditScreen.js::uploadFileHandler | e.target.files[0] без проверки — cancel диалога отправляет undefined в formData | Добавить if (!e.target.files[0]) return | 🔴 not yet |
| 15 | 🟡 | backend/controllers/productController.js::deleteProduct, userController.js::deleteUser | model.remove() deprecated в Mongoose 6+ | Заменить на findByIdAndDelete или deleteOne | 🔴 not yet |
| 16 | 🟡 | backend/config/db.js::connectDB | Deprecated mongoose options: useUnifiedTopology, useNewUrlParser, useCreateIndex | Удалить options object | 🔴 not yet |
| 17 | 🟡 | frontend/src/constants/cartConstants.js | CART_CLEAR_ITEMS = 'CART_RESET' — несоответствие имени и значения | Унифицировать имя константы и значение | 🔴 not yet |
| 18 | 🟡 | frontend/src/screens/PlaceOrderScreen.js | Магические числа: налог 15%, порог доставки $100. addDecimals пересоздаётся каждый рендер | Вынести в named constants вне компонента | 🔴 not yet |
| 19 | 🟡 | frontend/src/screens/OrderScreen.js::addPayPalScript | fetch PayPal SDK без error handling | Обернуть в try/catch | 🔴 not yet |
| 20 | 🟡 | frontend/src/screens/PaymentScreen.js | Dead code — закомментированный Stripe payment | Удалить | 🔴 not yet |
| 21 | 🟢 | frontend/src/components/Meta.js | Typo: 'cheap electroincs' | Исправить на 'electronics' | 🔴 not yet |
| 22 | 🟢 | frontend/src/screens/OrderScreen.js | console.log(paymentResult) — debug-лог в продакшн | Удалить | 🔴 not yet |
| 23 | 🟢 | frontend/src/screens/ProfileScreen.js | Пустой JSX-блок {} — мёртвый код | Удалить | 🔴 not yet |
| 24 | 🟢 | backend/utils/generateToken.js | expiresIn '30d' — magic string | Вынести в env var или named constant | 🔴 not yet |
| 25 | 🟢 | backend/controllers/productController.js::getProducts | pageSize = 10 — magic number | Вынести в constant | 🔴 not yet |
| 26 | 🟢 | frontend/src/store.js::initialState | localStorage.getItem вызывается дважды для каждого ключа | Сохранить в переменную | 🔴 not yet |
| 27 | 🟢 | backend/server.js | Нет cors/helmet middleware | Добавить cors + helmet | 🔴 not yet |
