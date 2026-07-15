# Design Implementation Repair 技术说明

## 方案

作品采用“平台模型 + Skill + CodeGraph + 确定性辅助脚本 + Maven 验证”的最终形态。平台模型从 `INSTRUCTION.md` 加载 Skill；Skill 负责完整修复工作流，不依赖常驻服务或预计算补丁。

从 03 方案复用：

- 设计/RFC 与代码的双向候选召回；
- 精确文档和源码证据；
- 适用性、可达性与反证门禁；
- CodeGraph 的 query、node、callers、callees、impact、affected、explore；
- 稳定 Finding ID、根因去重和结构化报告。

新增：

- 权威来源和冻结 API 分级；
- Finding 到 Repair Plan 的强制转换；
- 修改前影响面分析和最小补丁纪律；
- 编译、定向测试、公开黑盒、受保护哈希、契约复审的分层验证；
- 修复报告状态链校验。

## 工作流

```text
设计文档/README ──> 需求与契约候选 ─┐
                                     ├─> Evidence Gate ─> Finding
源码 ─> 静态扫描 + CodeGraph ────────┘                         │
                                                               v
CodeGraph impact/affected ───────────────────────────> Repair Plan
                                                               │
                                                               v
                                                     Minimal Patch
                                                               │
                                                               v
                         Compile/Test/Hash/Re-audit <─ Verification
                                      │ fail                │ pass
                                      └─────> re-plan       └─> report
```

## 辅助脚本

- `contract_scan.py`：从设计文档提取规范性语句，并对源码执行通用和 ShopHub 高价值候选扫描；输出只是候选，仍必须通过证据门禁。
- `protected_guard.py`：快照和校验设计文档、README、公开测试源、POM 与 Maven 设置，排除生成的 `target/`。
- `verify_project.py`：始终显式使用平台 Maven settings 和本地仓库，支持 compile、unit、install、public、acceptance、all。
- `validate_repair_report.py`：验证每个 fixed Finding 都具有 requirement、implementation、counterevidence、root cause、Repair Plan、Patch 和成功 Verification。

## 安全与泛化

- 不包含预计算补丁、源码哈希或测试 ID 分支。
- ShopHub 检查表只总结设计文档，用于导航；Finding 必须引用评测时提供的原始文档。
- 公共测试只用于验证，不能覆盖设计权威。
- 禁止通过修改公开测试、降低安全性、返回假成功或吞异常获得通过。
- CodeGraph `explore` 必须带行为锚点并限制文件数量，减少无关源码和 Token 消耗。
- 在无 Git 的评测材料上使用哈希快照和补丁报告建立可追溯性。

## 交付前验证

本地以赛题原始工程和既有完整修复样例做了前向验证：

- Skill 元数据和目录结构通过 `quick_validate.py`；四个 Python 脚本通过 `compileall`；
- 固定版本 CodeGraph 1.4.1 成功索引修复样例的 505 个文件、12,385 个节点和 24,842 条边，并完成 `query`、`impact` 与清理；
- 候选扫描从原始工程的 108 条规范语句中召回 26 个高价值候选；同一扫描在修复样例上剩余 0 个候选；
- 修复样例的 Maven reactor 编译成功，公开黑盒测试 24/24 通过；
- 43 个受保护输入在验证前后无新增、删除或修改；
- 含一个完整 Finding 修复链的样例报告通过 `validate_repair_report.py`。

这些结果验证的是 Skill 工具链和工作流，不代表预先知道或声称通过未知隐藏测试。

## 交付

```text
submission2/
├── INSTRUCTION.md
├── TECHNICAL_REPORT.md
└── work/
    ├── setup.sh
    └── skills/design-implementation-repair/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        └── scripts/
```
