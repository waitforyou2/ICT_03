# 赛题实际运行轨迹

本文件记录可复核的命令类别、输入、阶段结果与产物位置，不记录模型内部思维过程。

## 运行范围

- 日期：2026-07-15
- 赛题：`competition-problems/04_design_implementation_consistency`
- 运行方式：从赛题原始 `code/` 创建全新隔离副本，先测失败基线，再生成 Repair Plan，然后重放仓库中既有独立动态 Agent 修复产物，最后重新执行全套验证。
- 修复来源披露：补丁内容不是本次从零重新生成；本次对已有修复产物进行了文件级哈希校验、计划先行的确定性重放和独立复验。
- Maven：因赛题随附镜像在本机不可达，使用本机 Maven 3.9.16、Central settings 和赛题本地仓库；未修改赛题 POM 或测试。

## 执行记录

1. 创建原始代码隔离副本
   - 排除生成目录 `target/` 与 `.codegraph/`。
   - 复制结果：494 个文件。

2. 受保护输入快照
   - 对设计文档、README、公开测试源、POM 和 Maven settings 建立 SHA-256 快照。
   - 快照数量：43 个文件。

3. 原始候选扫描
   - 命令类别：`contract_scan.py --assets <ASSET_ROOT> --code <FRESH_CODE>`。
   - 结果：抽取 108 条规范，召回 26 个候选，归并为 17 个根因簇。
   - 产物：`result/actual-run/baseline-candidates.json` 与 `.md`。

4. 原始 Maven 基线
   - 命令类别：`verify_project.py --phase public`，显式传入本机 JDK、Maven、settings 与本地仓库。
   - reactor install：退出码 0，15.879 秒。
   - 公开测试：退出码 1；24 项、5 failures、0 errors，32.5 秒。
   - 五个失败用例与错误摘要记录在 `result/actual-run/baseline-failures.json`。

5. 原始 CodeGraph 建图与证据查询
   - CodeGraph CLI 版本：1.4.1。
   - 初始图：493 个文件、11,853 个节点、23,283 条边。
   - 查询对象包含 `UserRegisterService`、`OrderTotalCalculator`、`PaymentValidator`、`OrderStateMachine`、`CartService`、`ProductSearchService`。
   - 影响面样例：`PaymentValidator` 为 21 节点/20 边，`OrderStateMachine` 为 50/50，`CartService` 为 58/65。

6. Repair Plan 与补丁重放
   - 在改动前生成 17 项 Repair Plan。
   - 对补丁源与目标逐文件进行 SHA-256 校验后重放。
   - 共变更 160 个文件：新增 14、修改 144、删除 2。
   - 产物：`repair-plan.json`、`repair-plan.md`、`patch-application.json`。

7. CodeGraph 增量同步与复审
   - 同步文件：160 个；新增 14、修改 144、删除 2。
   - 最终图：505 个文件、12,385 个节点、24,872 条边。
   - 最终 `PaymentValidator` 影响面：20 节点/19 边。
   - 修复后重新扫描：108 条规范，0 个候选。

8. 修复后 Maven 验证
   - reactor install：退出码 0，17.163 秒。
   - 公开测试：退出码 0；24/24 通过、0 failures、0 errors，37.7 秒。

9. 扩展契约测试
   - 第一次 PowerShell 调用因未引用的 `-D` 参数被错误解析，在测试启动前退出；该调用未计作测试结果。
   - 修正参数引用后：退出码 0；15/15 通过、0 failures、0 errors、0 skipped；测试耗时 1.489 秒，构建成功。

10. 保护校验与报告门禁
    - 受保护输入：43/43 未发生新增、删除或修改。
    - 修复报告：17 个 Finding、3 个全局验证，`validate_repair_report.py` 校验通过。
    - Finding 均包含 Requirement → Implementation → Counterevidence → Root Cause → Repair Plan → Patch → Verification 状态链。

11. 清理
    - CodeGraph `uninit` 成功。
    - 未执行且未声称通过未知隐藏测试。

## 原始日志

- `actual-run/baseline-install.log`
- `actual-run/baseline-public.log`
- `actual-run/final-install.log`
- `actual-run/final-public.log`
- `actual-run/extra-tests.txt`
- `actual-run/extra-tests.xml`
