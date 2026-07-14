# 裁判执行说明

本作品是无人值守 CLI + Skill。代码图能力直接来自官方 npm 包 `@colbymchenry/codegraph@1.4.1`；作品不携带 CodeGraph 二进制，也不执行交互式 `codegraph install`。

## 1. 环境准备

要求 Linux x64/arm64、Bash、Python 3.10+、npm，以及首次安装时可访问 npm registry。Python 部分仅使用标准库。

在本提交目录执行：

```bash
bash work/setup.sh
```

脚本会把固定版本 CodeGraph 安装到 `work/.runtime/`，关闭遥测，验证 CLI 版本并编译检查 Python。成功标志：退出码为 0，最后一行是：

```text
SETUP_COMPLETE
```

不需要 JDK、Joern、Docker、Neo4j、Git 历史或外部大模型 API。

## 2. 执行流程

命令只接收三个位置参数：代码仓路径、设计文档路径、输出目录。

平台基准示例：

```bash
ASSET=/app/code/judge-assets/01_03_ai_implementation_design_difference_detection
bash work/run.sh \
  "$ASSET/code/f-stack" \
  "$ASSET/Difference/benchmark.md" \
  "$PWD/result"
```

`work/run.sh` 会自动完成以下步骤：

1. 若尚未安装，则调用 `work/setup.sh`；
2. 对目标仓执行 CodeGraph `init`（首次）或 `index --force --quiet`（再次运行）；
3. 从本地缓存解析 benchmark 中引用的 RFC，抽取规范强度与段落；
4. 生成候选，执行适用性、反证、重复项和精确源码证据门禁；
5. 对每个已确认候选直接调用 `codegraph explore` 检查调用者、被调用者、替代路径和影响面；
6. 原子化生成结构化 JSON、Markdown 和运行摘要。

执行全程无需人工输入。首次 npm 安装约下载 200–250 MB；本机实测首次完整基准约 4 分钟，远低于 6 小时限制。

## 3. 完成判定

以下条件全部满足即完成：

- 命令退出码为 0；
- 控制台最后出现 `RUN_COMPLETE output=...`；
- 输出目录存在且非空：
  - `findings.json`
  - `output.md`
  - `run-summary.json`
  - `codegraph-evidence.md`
- `run-summary.json.status` 为 `complete`；
- `run-summary.json.codegraph_status` 包含 `indexed`，有问题时包含非零 `explore x/x`。

失败时命令退出非零，并在标准错误输出单行 JSON：`{"status":"failed","error":"..."}`。

## 4. 结果获取

`findings.json` 是自动评分主文件，格式见 `work/specdiff/schemas/findings.schema.json`。每个问题包含：

- 差异类型、严重度、置信度与稳定 ID；
- 设计文档/RFC、章节、规范原文、强度；
- 实际实现行为和适用条件；
- 文件、行范围、符号、带行号源码摘录；
- 证据链、反证检查、CodeGraph 完成标记。

`output.md` 是同一结果的人类可读版；`codegraph-evidence.md` 保存每个候选的图查询及原始上下文；`run-summary.json` 保存数量、耗时状态、输入与告警。

## 5. 可选回归

不读取 `Difference/issues` 的公开基准回归及自建泛化/负向题：

```bash
cd work/specdiff
python3 -m unittest -v tests.test_public_benchmark tests.test_synthetic
```

测试允许 `--codegraph off`，用于隔离验证规范和证据层；正式 `work/run.sh` 强制 CodeGraph 成功。
