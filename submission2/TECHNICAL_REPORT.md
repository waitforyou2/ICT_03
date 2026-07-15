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

2026-07-15 从赛题原始 `code/` 建立全新隔离副本，执行了失败基线、Repair Plan、补丁重放和完整复验。补丁来自仓库中既有独立动态 Agent 修复产物，本次通过文件哈希确定性重放；来源已在计划、报告和执行轨迹中明确披露。

- Skill 元数据和目录结构通过 `quick_validate.py`；四个 Python 脚本通过 `compileall`；
- 基线扫描从 108 条规范中召回 26 个候选并归并为 17 个根因簇；基线公开测试实际运行 24 项，出现 5 failures、0 errors；
- CodeGraph 1.4.1 的基线图为 493 个文件、11,853 个节点和 23,283 条边，并对关键服务执行 `query` 与 `impact`；
- 改动前形成 17 项 Repair Plan；哈希校验后重放 160 个文件变更，其中新增 14、修改 144、删除 2；
- CodeGraph 增量同步 160 个文件，最终图为 505 个文件、12,385 个节点和 24,872 条边；修复后扫描为 0 个候选；
- Maven reactor install 成功，公开黑盒测试 24/24 通过；补充的 15 项契约测试全部通过；
- 43 个受保护输入在验证前后无新增、删除或修改；
- 含 17 个完整 Finding 修复链和 3 项全局验证的报告通过 `validate_repair_report.py`。

完整结构化结果位于 `result/actual-run/`，原始 Maven/Surefire 日志位于 `logs/trace/actual-run/`。这些结果不代表预先知道或声称通过未知隐藏测试。

## 交付

```text
submission2/
├── INSTRUCTION.md
├── TECHNICAL_REPORT.md
├── logs/
│   ├── interaction.md
│   └── trace/
│       ├── actual-run/
│       │   ├── baseline-install.log
│       │   ├── baseline-public.log
│       │   ├── final-install.log
│       │   ├── final-public.log
│       │   ├── extra-tests.txt
│       │   └── extra-tests.xml
│       ├── execution-trace.md
│       ├── setup.log
│       └── validation.log
├── result/
│   ├── actual-run/
│   │   ├── baseline-candidates.json/.md
│   │   ├── baseline-failures.json
│   │   ├── baseline-verification.json
│   │   ├── final-candidates.json/.md
│   │   ├── final-verification.json
│   │   ├── repair-plan.json/.md
│   │   ├── patch-application.json
│   │   ├── repair-report.json
│   │   ├── protected-files.json
│   │   ├── protected-verify.json
│   │   └── extra-verification.json
│   ├── output.md
│   └── validation-summary.json
└── work/
    ├── setup.sh
    └── skills/design-implementation-repair/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── references/
        └── scripts/
```

`setup.sh` 会在安装依赖前检查根 `README.md` 规定的全部必选交付项，并创建被 Git 忽略的 `result/runtime/` 作为平台运行期输出目录。真实运行摘要保留在 `result/output.md`，结构化产物保留在 `result/actual-run/`，可审计原始日志保留在 `logs/trace/actual-run/`。
