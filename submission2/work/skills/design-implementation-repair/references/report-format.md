# 修复报告格式

使用 UTF-8 JSON，顶层结构如下：

```json
{
  "schema_version": "2.0",
  "status": "complete",
  "asset_root": "/absolute/assets",
  "code_root": "/absolute/assets/code",
  "authority_conflicts": [],
  "findings": [],
  "global_verifications": [],
  "protected_inputs": {"passed": true, "snapshot": "..."},
  "unresolved": [],
  "result_code": "/absolute/assets/code"
}
```

每条 Finding 必须包含：

```json
{
  "id": "finding-0123456789ab",
  "title": "简短的根因标题",
  "classification": "contract_contradiction",
  "severity": "high",
  "confidence": 95,
  "status": "fixed",
  "requirement": {
    "path": "design-docs/08-order.md",
    "section": "6",
    "line": 42,
    "text": "准确的要求原文"
  },
  "implementation": {
    "path": "module/src/main/java/example.java",
    "line_start": 10,
    "line_end": 15,
    "symbol": "Example.method",
    "excerpt": "准确的当前实现或补丁前证据",
    "actual_behavior": "实际可达行为",
    "applicability": "触发条件"
  },
  "counterevidence": ["已检查的调用者、替代路径、开关与搜索"],
  "root_cause": "实现偏离设计的原因",
  "repair_plan": {
    "strategy": "符合设计的最小修复",
    "files": ["生产代码相对路径"],
    "preserve": ["必须保持的冻结 API 约束"],
    "risks": ["兼容性或事务风险"],
    "verification": ["计划执行的准确检查"]
  },
  "patch": {
    "files": ["生产代码相对路径"],
    "summary": "修改内容及其原因"
  },
  "verifications": [
    {
      "command": "准确命令",
      "exit_code": 0,
      "passed": true,
      "evidence": "测试或日志结果"
    }
  ]
}
```

完成前运行 `validate_repair_report.py`。校验器会强制要求每个 `fixed` Finding 具备完整的 Finding → Repair Plan → Patch → Verification 状态链。
