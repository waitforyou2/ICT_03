# Contract Scan Candidates

> Candidates are leads. Apply the evidence gate and CodeGraph counterevidence before accepting a Finding.

Requirements extracted: 108
Candidates: 26

| ID | Severity | Rule | Location | Title |
|---|---|---|---|---|
| `finding-a2c4a387b1bd` | critical | `forbidden-reset-bootstrap` | `ecommerce-app/src/main/java/com/ecommerce/app/SecurityConfig.java:63` | Forbidden reset or bootstrap route is exposed |
| `finding-ff17da359185` | critical | `forbidden-reset-bootstrap` | `ecommerce-app/src/main/java/com/ecommerce/app/SecurityConfig.java:64` | Forbidden reset or bootstrap route is exposed |
| `finding-34723b073228` | high | `cross-module-repository` | `ecommerce-app/src/main/java/com/ecommerce/app/controller/SystemAdminController.java:10` | Module imports another module's Repository |
| `finding-6ef501844b91` | critical | `forbidden-reset-bootstrap` | `ecommerce-app/src/main/java/com/ecommerce/app/controller/SystemAdminController.java:55` | Forbidden reset or bootstrap route is exposed |
| `finding-6ba7644dd1cc` | critical | `forbidden-reset-bootstrap` | `ecommerce-app/src/main/java/com/ecommerce/app/controller/SystemAdminController.java:97` | Forbidden reset or bootstrap route is exposed |
| `finding-3f4fbf5f56fe` | high | `cart-jpa-storage` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:12` | Temporary cart is persisted through JPA repositories |
| `finding-0958c72015d0` | high | `cart-jpa-storage` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:13` | Temporary cart is persisted through JPA repositories |
| `finding-2a79639b479e` | high | `cart-placeholder-pricing` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:189` | Cart pricing contains a required-behavior placeholder |
| `finding-338a24879a49` | medium | `generic-required-placeholder` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:189` | Required production path contains an implementation admission |
| `finding-ddb98779d8ec` | high | `cart-placeholder-pricing` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:230` | Cart pricing contains a required-behavior placeholder |
| `finding-a9f5d486851b` | medium | `generic-required-placeholder` | `ecommerce-cart/src/main/java/com/ecommerce/cart/service/CartService.java:230` | Required production path contains an implementation admission |
| `finding-8d43be083bd0` | high | `money-half-down` | `ecommerce-common/src/main/java/com/ecommerce/common/money/MonetaryUtil.java:32` | Monetary rounding is not HALF_UP |
| `finding-daa8ac03e7cb` | high | `inventory-duplicate-product` | `ecommerce-inventory/src/main/java/com/ecommerce/inventory/entity/Product.java:15` | Inventory duplicates product-owned model |
| `finding-d7f2c4dfdc33` | high | `inventory-duplicate-product` | `ecommerce-inventory/src/main/java/com/ecommerce/inventory/repository/ProductRepository.java:11` | Inventory duplicates product-owned model |
| `finding-13233454337c` | critical | `shipment-starts-outbound` | `ecommerce-logistics/src/main/java/com/ecommerce/logistics/service/ShipmentService.java:81` | Shipment is created in OUTBOUND state |
| `finding-97a0ff21bed0` | critical | `paid-direct-cancel` | `ecommerce-order/src/main/java/com/ecommerce/order/service/OrderStateMachine.java:40` | Paid order can transition directly to CANCELLED |
| `finding-e0cd080f9668` | high | `order-validation-exception` | `ecommerce-order/src/main/java/com/ecommerce/order/service/OrderValidator.java:26` | Order amount validation throws a standard exception |
| `finding-3fc703ab816b` | critical | `payment-exact-amount` | `ecommerce-payment/src/main/java/com/ecommerce/payment/service/PaymentValidator.java:34` | Payment does not compare against order payable amount |
| `finding-c6a399d0221e` | high | `refund-fixed-fee` | `ecommerce-payment/src/main/java/com/ecommerce/payment/service/RefundCalculator.java:38` | Refund subtracts an undocumented fixed fee |
| `finding-a36db60497de` | high | `product-search-default` | `ecommerce-product/src/main/java/com/ecommerce/product/dto/ProductSearchRequest.java:31` | Public product search includes non-shelf products by default |
| `finding-f9731a80ea9e` | high | `fake-stock` | `ecommerce-product/src/main/java/com/ecommerce/product/service/StockInfoFetcher.java:24` | Product stock uses a placeholder value |
| `finding-c706a2b72459` | medium | `generic-required-placeholder` | `ecommerce-promotion/src/main/java/com/ecommerce/promotion/controller/PromotionController.java:116` | Required production path contains an implementation admission |
| `finding-6b816170058f` | high | `promotion-stack-order` | `ecommerce-promotion/src/main/java/com/ecommerce/promotion/service/PromotionCalculationService.java:51` | Promotion stacking order starts with member discount |
| `finding-9e45b27fb9ae` | medium | `sensitive-word-equality` | `ecommerce-review/src/main/java/com/ecommerce/review/service/SensitiveWordFilter.java:35` | Sensitive-word detection uses whole-string equality |
| `finding-2fd38aca46e9` | medium | `sensitive-word-equality` | `ecommerce-review/src/main/java/com/ecommerce/review/service/SensitiveWordFilter.java:55` | Sensitive-word detection uses whole-string equality |
| `finding-ec06513a2110` | high | `registration-active` | `ecommerce-user/src/main/java/com/ecommerce/user/service/UserRegisterService.java:57` | Registration bypasses pending activation |
