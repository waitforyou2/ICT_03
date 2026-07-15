# ShopHub Contract Checklist

Use this checklist only for ShopHub or the design-implementation-consistency competition. It summarizes the supplied design set for navigation; always cite the original document in Findings.

## Contents

1. Global and API invariants
2. Module boundaries and storage
3. User and security
4. Product, inventory, and cart
5. Order and pricing
6. Payment, refund, invoice, settlement
7. Promotion
8. Logistics
9. Loyalty and review
10. Events, notification, audit, time, and operations
11. Final negative audit

## 1. Global and API invariants

- Keep Java 17, Spring Boot 3.2.x, the Maven multi-module structure, H2, Caffeine, Spring events, Spring Security, and JWT.
- Preserve every documented `/api/v1/` route, method, authentication requirement, header, request/response field name and type, success status, and error envelope.
- Return business DTOs directly and use `page`, `size`, `total`, and `items` for pagination.
- Use `BigDecimal` for money, retain precision during intermediate work, and round final amounts to two decimals with `HALF_UP`.
- Reject order totals below `0.01` with `OrderValidationException` and the documented error semantics.
- Preserve documented general and business error codes and HTTP mappings.
- Support idempotency for order creation, payment callbacks, refund applications, logistics callbacks, and invoice requests.
- Enforce documented local rate limits for login, payment callback, product search, and order creation.

## 2. Module boundaries and storage

- Keep a modular monolith: modules share a process and database connection but own their repositories and tables.
- Do not inject another module's Repository or duplicate its JPA Entity.
- Use documented QueryService interfaces for cross-module reads, command interfaces for strong commands, and Spring events for weakly coupled post-actions.
- Do not expose JPA entities across modules.
- Keep cart data only in Caffeine using the `cart:{userId}` logical key and a seven-day TTL; do not persist temporary carts in JPA.
- Query product stock through `InventoryQueryService`; query product identity through `ProductQueryService`.
- Query order data from payment, logistics, loyalty, and review through `OrderQueryService` or another documented local contract.

## 3. User and security

- Registration creates `PENDING_ACTIVATION`, generates an activation token, and sends through `LocalNotificationService`.
- Only `ACTIVE` users may log in or create orders. Map pending and frozen states to their documented 403 business errors.
- Preserve JWT issuance and USER/ADMIN authorization.
- Enforce address and resource ownership, not just authentication.
- Format addresses in province, city, district, detail order.
- Audit freeze and unfreeze operations.
- Do not expose reset or bootstrap business endpoints. Test isolation belongs to the harness.
- Validate local payment and logistics callback signatures and reject unknown callback states.

## 4. Product, inventory, and cart

- Default public product search to `ON_SHELF` only and honor documented keyword, category, brand, price, tag, and shelf filters.
- Aggregate real inventory summaries; never return placeholder stock.
- At order creation reserve stock only: increase reserved stock without reducing on-hand stock.
- At payment deduction reduce both on-hand and reserved stock and create the outbound record.
- On cancellation or timeout release reservations without changing on-hand stock.
- Use locking or equivalent atomicity so reservations and seckill cannot oversell.
- Prefer a single warehouse for one SKU, subject to service area, availability, distance, and priority.
- Accumulate quantity when the same SKU is added repeatedly to a cart.
- Enforce 100 cart item kinds and quantity 1 through 999.
- Calculate cart estimates through current product data, promotion calculation, points rules, shipping, packaging, and the documented total formula.

## 5. Order and pricing

- Validate active user, saleable products, price, stock, risk, promotion, points, shipping, and packaging before order completion.
- Use order formula: item total + shipping + packaging - discounts - points deduction.
- Apply full reduction, coupon, then member discount in that order.
- Create orders with HTTP 201 and status `CREATED`.
- Use `externalOrderNo` idempotently.
- Cancel unpaid orders after 60 minutes and release reservations.
- Allow CREATED direct cancellation; require PAID to enter `CANCEL_REVIEWING` before refund processing. Never permit PAID directly to CANCELLED.
- Process batch orders independently; one failed item must not roll back the batch.
- Keep sales statistics and purchase verification consistent with paid and delivered order data.

## 6. Payment, refund, invoice, settlement

- Support full payment only. Reject both underpayment and overpayment relative to order payable amount.
- On callback validate signature and idempotency, update payment and order, deduct reserved inventory, then publish success events.
- Keep non-critical logistics, loyalty, and notification actions from rolling back payment success.
- Require merchant review and warehouse acceptance before financial refund.
- Calculate refund as `paidAmount * (1 - configuredFeeRate)`; do not subtract an extra fixed fee.
- Support multiple partial invoices while cumulative issued amount stays within paid amount.
- Read the tax rate from configuration and round tax with `HALF_UP`.
- Build daily immutable settlement batches from un-settled successful payments, completed refunds, and issued invoices.

## 7. Promotion

- For discount rate `d`, calculate after-price as `price * d` and discount as `price * (1 - d)`.
- Validate coupon existence, time, threshold, applicable products, user ownership/restriction, and unused state.
- Mark consumed coupons with user and order ownership consistently.
- Apply full reduction, coupon, then member discount sequentially.
- Validate seckill window, SKU, per-user limit, stock, and price exclusion from ordinary full reduction.
- Make seckill stock updates atomic and reject sold-out purchases.

## 8. Logistics

- Create a shipment from the paid-order event in `CREATED`, not `OUTBOUND`.
- Enforce `CREATED → PICKING → LABEL_PRINTED → OUTBOUND`; do not allow skipped steps.
- Update order logistics status through the documented updater.
- Authenticate and deduplicate callbacks by tracking number, event time, and status.
- Publish delivered events and reconcile order/loyalty listeners.
- Calculate default shipping as 8 and free shipping at item amount at least 199, subject to templates.

## 9. Loyalty and review

- Award payment points from paid amount, member multiplier, and activity factor.
- Limit redemption to available unexpired points, 10,000 points, and 50 percent of order amount; use 100 points per yuan.
- Expire points after 12 natural months and redeem valid lots consistently.
- Use member thresholds and multipliers NORMAL 1.0, SILVER 1.1, GOLD 1.2, PLATINUM 1.5.
- Obtain annual order spending through an order query contract, not the order Repository.
- Require purchased and delivered/completed order evidence before a review.
- Allow one main review per order item and process append reviews separately.
- Detect sensitive words by containment, not whole-string equality.
- Keep new reviews pending review; approval publishes the reward event.

## 10. Events, notification, audit, time, and operations

- Include common event ID, type, occurrence time, aggregate ID, and trace ID.
- Preserve documented event payloads and listener coverage.
- Run non-critical post-payment listeners after commit and isolate their transaction/failure handling.
- Persist failed event processing and expose only documented authenticated operations interfaces.
- Route all business notifications through `LocalNotificationService`; deduplicate, render, record, and isolate failure.
- Record audit operator, operation, business ID, before/after state, time, and remark for documented sensitive operations.
- Use the controllable system clock where tests and business time rules require it.
- Keep runtime configuration overrides constrained to documented authenticated management APIs.

## 11. Final negative audit

Search for and explain every remaining occurrence of:

- `HALF_DOWN` or early monetary rounding;
- fake values such as stock `999`;
- TODO, FIXME, placeholder, “not yet integrated,” or unsupported admissions in required paths;
- reset/bootstrap public mappings;
- direct cross-module Repository imports or duplicated foreign entities;
- cart JPA persistence;
- direct PAID to CANCELLED transition;
- shipment creation in OUTBOUND or unguarded outbound transition;
- refund fixed-fee subtraction;
- sensitive-word equality matching;
- callback success without signature, idempotency, or known-state validation;
- swallowed exceptions that should be business failures;
- synchronous non-critical listeners capable of rolling back payment.

Do not automatically edit every match. Map it through the evidence gate and authoritative contract first.
