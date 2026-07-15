# 赛题实际运行结果

## 结论

本目录记录的是 2026-07-15 在 ShopHub 原始赛题代码独立副本上完成的一次真实运行，不是格式示例。

运行从原始 `code/` 建立全新副本，先执行失败基线，再依据本次候选和 CodeGraph 证据形成 Repair Plan，随后重放仓库中既有独立动态 Agent 产生的修复变更，并重新执行候选扫描、公开测试、扩展测试、受保护文件校验和报告门禁。补丁来源在 Repair Plan 和修复报告中明确披露，没有把旧结果冒充新生成结果。

## 前后对比

| 阶段 | 结果 |
|---|---|
| 原始规范提取 | 108 条 |
| 原始候选扫描 | 26 个候选，17 个根因簇 |
| 原始 CodeGraph | 493 文件、11,853 节点、23,283 条边 |
| 原始公开测试 | 24 项，5 failures，0 errors |
| Repair Plan | 17 个计划，覆盖 160 个变更文件 |
| Patch | 14 个新增、144 个修改、2 个删除 |
| CodeGraph 增量同步 | 同步 160 个文件 |
| 修复后候选扫描 | 108 条规范，0 个候选 |
| 修复后 CodeGraph | 505 文件、12,385 节点、24,872 条边 |
| 修复后公开测试 | 24/24 通过，0 failures，0 errors |
| 扩展契约测试 | 15/15 通过，0 failures，0 errors |
| 受保护输入 | 43/43 不变 |
| 修复报告门禁 | 17 个 Finding、3 个全局验证，校验通过 |

## 原始基线失败

真实失败用例为：

1. `pub104_orderTotalShouldIncludeShipping`：订单应付金额未正确包含费用和抵扣。
2. `pub101_couponDiscountShouldBeCorrect`：八折券在 100 元商品上的优惠额计算错误。
3. `pub105_unactivatedUserCannotLogin`：未激活用户错误地返回登录成功。
4. `pub001_registerActivateLogin`：注册用户直接成为 `ACTIVE`，而不是 `PENDING_ACTIVATION`。
5. `pub009_createPayment`：支付记录初始状态为 `PENDING`，而不是 `CREATED`。

结构化记录见 [baseline-failures.json](actual-run/baseline-failures.json)。

## 真实结果产物

- [完整修复报告](actual-run/repair-report.json)：17 条 Finding → Repair Plan → Patch → Verification 链。
- [补丁前 Repair Plan](actual-run/repair-plan.md)及其 [JSON](actual-run/repair-plan.json)。
- [160 个文件的补丁应用清单](actual-run/patch-application.json)。
- [基线候选](actual-run/baseline-candidates.md)及其 [JSON](actual-run/baseline-candidates.json)。
- [最终候选](actual-run/final-candidates.md)及其 [JSON](actual-run/final-candidates.json)。
- [基线 Maven 验证摘要](actual-run/baseline-verification.json)。
- [最终 Maven 验证摘要](actual-run/final-verification.json)。
- [扩展测试摘要](actual-run/extra-verification.json)。
- [受保护输入最终校验](actual-run/protected-verify.json)。

## 原始日志

- [本次可审计执行轨迹](../logs/trace/execution-trace.md)
- [基线 Maven install 日志](../logs/trace/actual-run/baseline-install.log)
- [基线公开测试日志](../logs/trace/actual-run/baseline-public.log)
- [修复后 Maven install 日志](../logs/trace/actual-run/final-install.log)
- [修复后公开测试日志](../logs/trace/actual-run/final-public.log)
- [扩展测试文本报告](../logs/trace/actual-run/extra-tests.txt)
- [扩展测试 Surefire XML](../logs/trace/actual-run/extra-tests.xml)

## 平台运行

正式评测仍按根目录 `INSTRUCTION.md` 加载中文 Skill。平台运行期的新结果写入 `result/runtime/`，修复目标为评测材料中的 `<ASSET_ROOT>/code/`。

## 声明

本次实际执行了公开测试和仓库内扩展测试；未知隐藏测试未执行，也未声称通过。
