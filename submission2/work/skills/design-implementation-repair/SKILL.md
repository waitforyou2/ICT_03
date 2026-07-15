---
name: design-implementation-repair
description: 对照设计文档、冻结 API 契约与源代码审计设计—实现不一致，制定最小修复方案、修改代码并验证结果。当 Codex 需要使用 CodeGraph 调查缺失或矛盾行为，在不修改设计事实来源和冻结接口的前提下修复 Java、Spring 或类似工程，并输出有证据支撑的 Finding → Repair Plan → Patch → Verification 报告时使用。
---

# 设计—实现一致性修复

把设计文档作为事实来源，交付经过验证的代码修复。复用 SpecDiff 的纪律：从规范和代码两个方向召回候选，要求准确证据与反证，再进入受门禁约束的修复闭环。

本文保留四个报告字段名以兼容机器校验：`Finding` 表示已确认的不一致问题，`Repair Plan` 表示修改前的修复计划，`Patch` 表示实际代码补丁，`Verification` 表示验证证据。

## 输入

修改代码前先确定以下路径：

- `ASSET_ROOT`：包含赛题 README、设计文档、代码、测试和 Maven 配置的目录。
- `CODE_ROOT`：需要修复的代码目录，通常是 `<ASSET_ROOT>/code`。
- `OUTPUT_ROOT`：位于受保护输入之外的报告目录。
- `SKILL_ROOT`：本 Skill 所在目录。
- `CODEGRAPH_BIN`：执行 setup 后生成的 `<submission>/work/.runtime/node_modules/.bin/codegraph`；从 `SKILL_ROOT` 出发，对应 `../../.runtime/node_modules/.bin/codegraph`。

除非 `INSTRUCTION.md` 另有结果路径要求，否则直接修改 `CODE_ROOT`。绝不通过修改设计文档来迁就现有代码。

## 按需读取参考资料

在执行对应动作前读取以下文件：

1. 确定事实来源或开始修改前，读取 [authority-and-scope.md](references/authority-and-scope.md)。
2. 接受 Finding 前，读取 [evidence-gate.md](references/evidence-gate.md)。
3. 初始化或查询 CodeGraph 前，读取 [codegraph-playbook.md](references/codegraph-playbook.md)。
4. 编写 Repair Plan 或补丁前，读取 [repair-policy.md](references/repair-policy.md)。
5. 运行测试或宣布完成前，读取 [verification.md](references/verification.md)。
6. 处理 ShopHub 或“设计与实现一致性”赛题时，还要读取 [shophub-contracts.md](references/shophub-contracts.md)。
7. 编写最终报告前，读取 [report-format.md](references/report-format.md)。

## 执行工作流

### 1. 固定范围并建立基线

1. 将所有输入路径解析为绝对路径。
2. 创建 `OUTPUT_ROOT`，且不得把它放在 `CODE_ROOT` 内。
3. 对受保护输入建立快照：

   ```bash
   python3 "$SKILL_ROOT/scripts/protected_guard.py" snapshot \
     --assets "$ASSET_ROOT" --output "$OUTPUT_ROOT/protected-files.json"
   ```

4. 阅读赛题 README、平台说明、全部设计文档、根 POM、模块 POM 和已有公开测试说明。
5. 记录不同权威来源之间的冲突，不得默默选择更容易实现的行为。公开测试只是行为观测，不是规范。
6. 条件允许时运行基线编译和公开测试，保留失败测试名与日志作为证据。

### 2. 使用 SpecDiff 方法检测不一致

先运行确定性候选扫描：

```bash
python3 "$SKILL_ROOT/scripts/contract_scan.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --json "$OUTPUT_ROOT/candidates.json" \
  --markdown "$OUTPUT_ROOT/candidates.md"
```

在准确的代码根目录建立或刷新 CodeGraph，并使用操作手册中的命令。随后从两个方向检索：

- **规范驱动**：针对每条规范性要求，定位实现它的 Controller、DTO、Service、状态迁移、事件、配置、持久化归属和测试。
- **代码驱动**：检查可疑常量、占位实现、伪造数据、直接 Repository 依赖、过宽异常处理、禁止路由、状态修改、事件监听器和无保护副作用；把每个候选映射回权威要求。

扫描器输出的是线索，不是已确认 Finding。每条线索都必须通过证据门禁；声称行为缺失前，必须搜索替代实现。

### 3. 建立 Finding

只接受同时具备以下内容的 Finding：

- 稳定 ID 和分类；
- 准确的设计文档路径、章节或行号，以及要求原文；
- 准确的当前代码路径、行范围、符号和摘录；
- 实际可达行为和适用条件；
- 根因，而不只是失败测试表现；
- 基于 CodeGraph 或全仓搜索的反证检查；
- 不低于 70% 的置信度；
- 受影响的 API 与必须保持的约束。

使用以下机器可读分类值：

- `contract_contradiction`：实现行为与强制契约冲突；
- `missing_behavior`：完成反证搜索后，仍找不到必需行为的实现；
- `forbidden_extra_behavior`：代码暴露或执行了契约禁止的行为；
- `architecture_boundary`：依赖、存储或数据归属违反模块设计；
- `workflow_state`：状态迁移或操作顺序违反设计流程；
- `nonfunctional_contract`：安全、幂等、并发、事务、事件隔离、审计、时间或限流要求被违反。

如果无法确定文档身份、适用性、可达性或当前源码证据，就抑制该候选，不得把它写成已确认 Finding。

### 4. 修改前先编写 Repair Plan

对每个已确认 Finding，检查准确符号和影响范围：

```bash
"$CODEGRAPH_BIN" node <symbol> --path "$CODE_ROOT"
"$CODEGRAPH_BIN" impact <symbol> --path "$CODE_ROOT" --depth 2 --json
"$CODEGRAPH_BIN" callers <symbol> --path "$CODE_ROOT"
```

Repair Plan 必须说明：

- 目标行为和需要恢复的约束；
- 根因；
- 必须修改的最小生产文件集合；
- 受影响的接口、调用者、事件、持久化和测试；
- 必须保持不变的冻结 API 元素；
- 迁移或兼容性风险；
- 准确的定向验证和回归验证命令；
- 触发回滚的条件。

没有计划就不得修改 Finding。共享同一根因的 Finding 应合并处理，用一个连贯补丁完成修复。

### 5. 应用最小补丁

只实现计划中明确列出的行为：

1. 保持冻结 URL、HTTP Method、Header、请求/响应字段、类型、状态码和错误信封不变。
2. 优先复用已有公开接口和模块边界，不得直接访问其他模块的 Repository。
3. 保持无关且已通过的行为不变。
4. 不得硬编码公开测试 ID、夹具或期望值。
5. 不得通过关闭校验、安全机制或测试来获得通过。
6. 仅在必要时新增或修改生产代码和符合设计的单元测试。
7. 每完成一个连贯补丁簇就重新编译。
8. 修改源码后运行 `codegraph sync "$CODE_ROOT"`。
9. 开始下一个补丁簇前，对变更文件重新运行 `impact` 或 `affected`。

如果补丁超出计划文件范围或改变 API 形态，停止修改，回滚当前补丁并重新制定计划。

### 6. 分层验证并把失败反馈到分析流程

按照 [verification.md](references/verification.md) 使用随附验证器。最低完成阶梯为：

1. 生产代码和测试源码编译；
2. 对修改领域运行可信的定向单元测试；
3. 将修复模块安装到赛题提供的本地 Maven 仓库；
4. 运行公开黑盒测试；
5. 校验受保护输入哈希；
6. 对每条已修复契约重新执行设计到代码审计；
7. 负向扫描禁止路由、占位实现、伪造数据、遗留重复模型和 API 漂移。

把验证失败视为新证据。将它映射到已有 Finding，或建立一条经过门禁的新 Finding；不得只看堆栈信息就直接打补丁。

### 7. 完成报告并清理

按照 [report-format.md](references/report-format.md) 编写 `repair-report.json`，然后执行校验：

```bash
python3 "$SKILL_ROOT/scripts/validate_repair_report.py" \
  "$OUTPUT_ROOT/repair-report.json"
python3 "$SKILL_ROOT/scripts/protected_guard.py" verify \
  --assets "$ASSET_ROOT" --snapshot "$OUTPUT_ROOT/protected-files.json"
```

如果 CodeGraph 索引建立在 `CODE_ROOT` 内，交付前删除索引：

```bash
"$CODEGRAPH_BIN" uninit --force "$CODE_ROOT"
```

只有同时满足以下条件才能结束：

- 修复后的代码可以构建；
- 公开验收测试通过；
- 受保护文件没有变化；
- 每个已修复 Finding 都包含 Repair Plan、补丁记录和成功验证证据；
- 不存在未解决的高置信强制性 Finding；
- 最终报告通过校验；
- 明确给出修复结果位置。

不得声称未知隐藏测试已经通过。只报告实际执行过的检查。
