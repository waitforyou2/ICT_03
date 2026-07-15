# Repair Report Format

Write UTF-8 JSON with this top-level shape:

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

Each Finding must contain:

```json
{
  "id": "finding-0123456789ab",
  "title": "Short root-cause title",
  "classification": "contract_contradiction",
  "severity": "high",
  "confidence": 95,
  "status": "fixed",
  "requirement": {
    "path": "design-docs/08-order.md",
    "section": "6",
    "line": 42,
    "text": "Exact requirement"
  },
  "implementation": {
    "path": "module/src/main/java/example.java",
    "line_start": 10,
    "line_end": 15,
    "symbol": "Example.method",
    "excerpt": "Exact current or pre-patch evidence",
    "actual_behavior": "Reachable behavior",
    "applicability": "Trigger condition"
  },
  "counterevidence": ["Callers, alternate paths, flags, and searches checked"],
  "root_cause": "Why implementation diverged",
  "repair_plan": {
    "strategy": "Smallest design-aligned repair",
    "files": ["relative production path"],
    "preserve": ["Frozen API invariant"],
    "risks": ["Compatibility or transaction risk"],
    "verification": ["Exact planned check"]
  },
  "patch": {
    "files": ["relative production path"],
    "summary": "What changed and why"
  },
  "verifications": [
    {
      "command": "exact command",
      "exit_code": 0,
      "passed": true,
      "evidence": "test or log result"
    }
  ]
}
```

Use `validate_repair_report.py` before completion. The validator enforces the Finding → Repair Plan → Patch → Verification chain for every `fixed` Finding.
