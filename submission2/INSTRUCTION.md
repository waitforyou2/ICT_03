# 裁判执行说明

本作品是一个由答题平台模型直接使用的 Skill。它复用 03 方案的规范—代码双向检测、精确证据和 CodeGraph 反证机制，并增加完整的 `Finding → Repair Plan → Patch → Verification` 修复闭环。无需启动常驻服务，也不要求额外无人值守 Agent。

## 1. 准备环境

要求：Linux、Bash、Python 3.10+、npm、JDK 17+、Maven 3.6+。在本提交目录执行：

```bash
bash work/setup.sh
```

脚本会固定安装官方 `@colbymchenry/codegraph@1.4.1`，关闭遥测，检查 Python 脚本并打印：

```text
SETUP_COMPLETE
```

## 2. 加载并使用 Skill

答题平台模型必须完整读取并使用：

```text
work/skills/design-implementation-repair/SKILL.md
```

等价调用意图：

```text
Use $design-implementation-repair to inspect the supplied ShopHub design documents and frozen REST contract, repair the supplied code in place, verify it, and produce the required repair report.
```

平台材料默认位置：

```text
/app/code/judge-assets/02_04_design_implementation_consistency/
├── code/
├── design-docs/
├── test-cases/
├── README.md
├── PLATFORM.md
├── maven-settings.xml
└── maven-repo/
```

如果平台实际路径不同，模型应以同时包含 `code/`、`design-docs/` 和 `README.md` 的目录为 `ASSET_ROOT`，不得硬编码测试用例内容。

## 3. 执行要求

模型按照 Skill 的顺序完成：

1. 建立受保护文件哈希快照。
2. 阅读全部设计文档、冻结 API 契约和工程结构。
3. 运行候选扫描并在准确的 `code/` 根目录初始化 CodeGraph。
4. 对候选执行 03 方案的证据门禁和反证搜索。
5. 每个确认问题先写 Repair Plan，再修改 `code/`。
6. 每组补丁后增量同步 CodeGraph、编译并运行相关测试。
7. 最终运行公开黑盒测试、受保护文件校验和全量设计复审。
8. 生成并校验 `repair-report.json`。

允许修改平台材料中的 `code/`；禁止修改 `design-docs/`、`README.md`、`PLATFORM.md`、`test-cases/`、`maven-settings.xml` 和冻结 REST 契约。

## 4. 修复结果与完成判定

修复后的工程位置：

```text
<ASSET_ROOT>/code/
```

报告建议写入当前工作目录下：

```text
repair-output/
├── candidates.json
├── candidates.md
├── protected-files.json
├── repair-report.json
└── verification/
```

仅当以下条件全部满足才算完成：

- 修复后的 Maven reactor 编译成功；
- 平台公开黑盒测试全部通过；
- 受保护文件哈希校验通过；
- 没有未解决的高置信强制性 Finding；
- 每个已修复 Finding 都包含 Repair Plan、Patch 和成功 Verification；
- `validate_repair_report.py` 返回 0；
- 模型明确返回修复后 `code/` 和报告路径。

不得声称未知隐藏测试已经通过，只报告实际执行的验证。
