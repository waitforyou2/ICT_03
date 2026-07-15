# 本次实际运行 Repair Plan

- 原始规范语句：108
- 原始候选：26
- 根因簇：17
- 计划变更文件：160

> 补丁来源说明：补丁来源是仓库中既有独立动态 Agent 修复产物；本次在全新原始副本上重新建立基线、先形成计划、再重放并独立验证。

## finding-df5d672b84ee · cart-jpa-storage

- 策略：将临时购物车切换到 Caffeine，并移除生产路径上的 JPA 持久化依赖。
- 候选数：2
- 计划文件数：13
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-1cf44c853b7e · cart-placeholder-pricing

- 策略：使用商品、营销、积分、运费和包装费服务计算购物车预估。
- 候选数：2
- 计划文件数：36
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-55e8f4658202 · cross-module-repository

- 策略：通过 QueryService/Adapter 取代跨模块 Repository 访问。
- 候选数：1
- 计划文件数：55
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-2fa6132f5dcf · fake-stock

- 策略：通过 InventoryQueryService 返回真实库存摘要，删除占位库存值。
- 候选数：1
- 计划文件数：19
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-067f599a3a8c · forbidden-reset-bootstrap

- 策略：移除对外 reset/bootstrap 路由，只保留测试框架隔离能力。
- 候选数：4
- 计划文件数：26
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-33b82c6d24a6 · generic-required-placeholder

- 策略：补齐必需生产路径的占位实现，并复用既有领域边界。
- 候选数：3
- 计划文件数：148
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-613502838c5d · inventory-duplicate-product

- 策略：删除库存模块复制的商品模型，通过 ProductQueryService 跨模块读取。
- 候选数：2
- 计划文件数：18
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-f9c74e149eca · money-half-down

- 策略：统一金额最终舍入为 HALF_UP，并避免中间步骤过早舍入。
- 候选数：1
- 计划文件数：77
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-e1c670784cfa · order-validation-exception

- 策略：订单金额约束统一抛出 OrderValidationException 和冻结错误语义。
- 候选数：1
- 计划文件数：51
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-20036485d135 · paid-direct-cancel

- 策略：已支付订单进入 CANCEL_REVIEWING，审核后再进入退款与取消流程。
- 候选数：1
- 计划文件数：58
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-12f6d5dcb344 · payment-exact-amount

- 策略：支付校验同时拒绝少付和多付，要求与订单应付金额完全一致。
- 候选数：1
- 计划文件数：58
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-6589fe13e5c9 · product-search-default

- 策略：公开搜索默认强制 ON_SHELF，同时保留文档筛选字段。
- 候选数：1
- 计划文件数：8
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-1de28b036363 · promotion-stack-order

- 策略：按满减、优惠券、会员折扣的固定顺序计算。
- 候选数：1
- 计划文件数：39
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-27b34f1bf376 · refund-fixed-fee

- 策略：按实付金额和配置费率计算退款，不额外扣除固定费用。
- 候选数：1
- 计划文件数：26
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-1fd67efda511 · registration-active

- 策略：注册创建 PENDING_ACTIVATION，激活成功后才允许登录。
- 候选数：1
- 计划文件数：6
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-f3015691578d · sensitive-word-equality

- 策略：按包含关系匹配敏感词，并保持审核流程不变。
- 候选数：2
- 计划文件数：7
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

## finding-ed2bc80b7351 · shipment-starts-outbound

- 策略：运单从 CREATED 开始并强制执行完整状态迁移。
- 候选数：1
- 计划文件数：40
- 保持项：冻结 REST URL、HTTP Method、DTO 字段、状态码和错误信封
- 风险：跨模块调用、事务边界、幂等与既有通过行为可能回归
- 回滚条件：编译失败、公开 API 漂移、受保护输入变化或无设计依据的基线回归。

