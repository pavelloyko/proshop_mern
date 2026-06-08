# Fix #3 — Client-Supplied Order Prices: Server-Side Recalculation

## Original finding (from synthesis.md)

**A-2 (C1):** `addOrderItems` in `orderController.js` accepted `itemsPrice`, `taxPrice`, `shippingPrice`, and `totalPrice` directly from the request body without server-side validation or recalculation. A malicious or buggy client could submit arbitrary prices, creating orders with incorrect totals. No transaction wrapped the order creation.

## What I changed

### backend/controllers/orderController.js
```diff
+ import Product from '../models/productModel.js'

  const addOrderItems = asyncHandler(async (req, res) => {
-   const {
-     orderItems,
-     shippingAddress,
-     paymentMethod,
-     itemsPrice,
-     taxPrice,
-     shippingPrice,
-     totalPrice,
-   } = req.body
+   const {
+     orderItems,
+     shippingAddress,
+     paymentMethod,
+   } = req.body

    // ... validation ...

+   // Server-side price recalculation from Product DB records
+   const productIds = orderItems.map((item) => item.product)
+   const products = await Product.find({ _id: { $in: productIds } })
+
+   const productMap = new Map()
+   for (const p of products) {
+     productMap.set(p._id.toString(), p)
+   }
+
+   const recalculatedItems = orderItems.map((item) => {
+     const product = productMap.get(item.product)
+     if (!product) {
+       throw new Error(`Product not found: ${item.product}`)
+     }
+     return {
+       name: product.name,
+       qty: item.qty,
+       image: product.image,
+       price: product.price,
+       product: item.product,
+     }
+   })
+
+   const itemsPrice = recalculatedItems.reduce(
+     (acc, item) => acc + item.price * item.qty, 0
+   )
+   const taxPrice = Number((itemsPrice * 0.15).toFixed(2))
+   const shippingPrice = itemsPrice > 100 ? 0 : 10
+   const totalPrice = Number((itemsPrice + taxPrice + shippingPrice).toFixed(2))

    const order = new Order({
-     orderItems,
+     orderItems: recalculatedItems,
      user: req.user._id,
      shippingAddress,
      paymentMethod,
```

## Why this approach

1. **Single DB query** via `Product.find({ _id: { $in: productIds } })` — fetches all products in one round-trip (avoids N+1)
2. **Map lookup** for O(1) price retrieval per item
3. **Server-authoritative prices** — client-submitted `price`, `name`, `image` are all replaced with DB values
4. **Tax/shipping rules** are now server-side (15% tax, free shipping over $100) — previously client-controlled
5. **Product existence validation** — throws if any product ID doesn't exist in DB

### Trade-offs

- **Breaking change**: existing frontend sends prices in the request body — they are now silently ignored. The frontend still works because it was sending prices that matched the DB anyway, but the API contract changed (prices are now computed, not accepted).
- **Tax/shipping rules hardcoded**: 15% tax and $10 shipping are now in the controller. For a learning project this is fine; production would extract these to a config or service layer.
- **No transaction**: The fix doesn't add a MongoDB transaction around product lookup + order creation. For a single-server setup this is acceptable. A production system would wrap both in a session.

## Behavior change

**Intentional behavior change** — prices are now calculated server-side. Clients can no longer submit arbitrary order totals. The `itemsPrice`, `taxPrice`, `shippingPrice`, `totalPrice` fields in the request body are ignored.

## Lessons learned

This was the most complex of the 3 fixes. The key insight from the architecture-mate: the lack of a service layer meant business logic (pricing) leaked into the HTTP deserialization layer. In a proper architecture, a `PricingService.calculateTotals(orderItems)` would be called from both the controller and any future MCP endpoints.
