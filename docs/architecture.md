# Architecture — ProShop MERN

## C4 Container Diagram

```mermaid
graph TB
    subgraph Frontend ["Frontend (React SPA)"]
        direction TB
        Entry["frontend/src/index.js<br/>React DOM root"]
        Router["frontend/src/App.js<br/>React Router v5"]
        Redux["frontend/src/store.js<br/>Redux Store"]
        Screens["frontend/src/screens/<br/>15 page components"]
        Components["frontend/src/components/<br/>12 reusable components"]
        Actions["frontend/src/actions/<br/>productActions · userActions<br/>orderActions · cartActions"]
        Reducers["frontend/src/reducers/<br/>productReducers · userReducers<br/>orderReducers · cartReducers"]
    end

    subgraph Backend ["Backend (Express API)"]
        direction TB
        Server["backend/server.js<br/>Express entry point"]
        Routes["backend/routes/<br/>productRoutes · userRoutes<br/>orderRoutes · uploadRoutes"]
        Controllers["backend/controllers/<br/>productController · userController<br/>orderController"]
        AuthMW["backend/middleware/authMiddleware.js<br/>protect · admin"]
        ErrorMW["backend/middleware/errorMiddleware.js<br/>notFound · errorHandler"]
        Seeder["backend/seeder.js<br/>DB seed CLI"]
    end

    subgraph DataLayer ["Data Layer"]
        direction TB
        MongoDB[("MongoDB<br/>proshop database<br/>Docker :27017")]
        Models["backend/models/<br/>Product · User · Order"]
        LocalStorage[("Browser localStorage<br/>cartItems · userInfo<br/>shippingAddress")]
        Uploads["uploads/<br/>Product images (multer)"]
    end

    subgraph External ["External Services"]
        direction TB
        PayPal["PayPal Sandbox API<br/>Payment processing"]
        PayPalSDK["react-paypal-button-v2<br/>Client-side SDK"]
    end

    %% Frontend internal flow
    Entry --> Router
    Router --> Screens
    Screens --> Actions
    Screens --> Components
    Actions --> Reducers
    Reducers --> Redux
    Redux --> Screens
    Screens <--> LocalStorage

    %% Frontend to Backend
    Actions -->|"Axios /api/*<br/>(proxy :5001)"| Server

    %% Backend internal flow
    Server --> Routes
    Routes -->|"protect / admin"| AuthMW
    Routes --> Controllers
    Controllers --> Models
    Server --> ErrorMW

    %% Backend to Data
    Models -->|"Mongoose CRUD"| MongoDB
    Controllers -->|"multer upload"| Uploads

    %% Backend to External
    Server -->|"/api/config/paypal<br/>Client ID"| PayPalSDK
    PayPalSDK -->|"Payment flow"| PayPal
    Controllers -->|"orderController<br/>updateOrderToPaid"| PayPal

    %% Seeder
    Seeder -->|"import/destroy"| MongoDB
```

## Data Flow — Place Order Scenario

```mermaid
sequenceDiagram
    participant User as Browser (React)
    participant Store as Redux Store
    participant API as Express :5001
    participant Auth as authMiddleware
    participant Ctrl as orderController
    participant DB as MongoDB
    participant PP as PayPal API

    User->>Store: dispatch(addToCart)
    Store->>Store: cartReducer updates cartItems
    Store->>Store: Persist to localStorage

    User->>API: GET /api/config/paypal
    API-->>User: PAYPAL_CLIENT_ID

    User->>User: PayPal SDK renders payment button

    User->>PP: Submit payment
    PP-->>User: Payment result (id, status, payer)

    User->>API: POST /api/orders (orderItems, shipping, payment)
    API->>Auth: protect middleware (verify JWT)
    Auth->>DB: User.findById(decoded.id)
    Auth-->>API: req.user set

    API->>Ctrl: addOrderItems()
    Ctrl->>DB: Order.create(orderData)
    DB-->>Ctrl: saved order
    Ctrl-->>API: 201 + order JSON
    API-->>User: Order created

    User->>API: PUT /api/orders/:id/pay (paymentResult)
    API->>Auth: protect middleware
    API->>Ctrl: updateOrderToPaid()
    Ctrl->>DB: order.isPaid = true, order.paidResult = ...
    DB-->>Ctrl: updated order
    Ctrl-->>User: 200 + updated order

    User->>Store: dispatch(CART_CLEAR_ITEMS)
    Store->>Store: cartReducer resets
    Store->>Store: Persist empty cart to localStorage
```

## Container Responsibilities

| Container | Path | Role |
|---|---|---|
| React SPA | `frontend/src/` | UI rendering, client-side routing, Redux state management |
| Express API | `backend/server.js` | REST API, JWT auth, file upload, serves static in production |
| MongoDB | Docker `:27017` | Persistent storage for products, users, orders |
| localStorage | Browser | Client-side persistence for cart, auth token, shipping address |
| PayPal Sandbox | External | Payment processing in test mode |
| uploads/ | `uploads/` | Server-side image storage (multer destination) |
