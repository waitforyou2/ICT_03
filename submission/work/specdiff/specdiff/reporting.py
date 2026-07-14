from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Candidate, RunSummary


def result_payload(summary: RunSummary, findings: list[Candidate]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "summary": summary.to_dict(),
        "findings": [item.to_dict() for item in findings],
    }


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_markdown(summary: RunSummary, findings: list[Candidate]) -> str:
    lines = [
        "# SpecDiff 审计结果", "",
        f"- 状态：`{summary.status}`",
        f"- 代码仓：`{summary.repo}`",
        f"- 设计文档：`{summary.docs}`",
        f"- 源文件：{summary.source_files}",
        f"- 规范条目：{summary.requirements}",
        f"- 已确认差异：{summary.findings}",
        f"- CodeGraph：`{summary.codegraph_status}`", "",
    ]
    if summary.warnings:
        lines.extend(["## 运行告警", ""] + [f"- {warning}" for warning in summary.warnings] + [""])
    for number, finding in enumerate(findings, start=1):
        req = finding.requirement
        lines.extend([
            f"## {number}. {finding.title}", "",
            f"- ID：`{finding.id}`",
            f"- 分类：`{finding.finding_type}`；严重度：`{finding.severity}`；置信度：{finding.confidence}%",
            f"- 标签：{', '.join(f'`{tag}`' for tag in finding.tags)}",
            f"- 适用条件：{finding.applicability}", "",
            "### 规范证据", "",
        ])
        if req:
            lines.extend([
                f"> {req.text}", "",
                f"来源：`{req.document}` §{req.section}，`{req.source_path}:{req.line}`；强度 `{req.strength}`。", "",
            ])
        else:
            lines.extend(["> 未通过规范证据门禁（该候选不应出现在正式结果）。", ""])
        lines.extend(["### 实现行为", "", finding.actual_behavior, "", "### 代码证据", ""])
        for evidence in finding.code_evidence:
            lines.extend([
                f"- `{evidence.path}:{evidence.line_start}`，符号 `{evidence.symbol}`：{evidence.purpose}", "",
                "```text", evidence.excerpt, "```", "",
            ])
        lines.extend(["### 证据链与反证", ""])
        lines.extend([f"1. {step}" for step in finding.evidence_chain])
        lines.extend([""] + [f"- 已检查：{item}" for item in finding.counterevidence_checked] + [""])
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(path: str | Path, summary: RunSummary, findings: list[Candidate]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(summary, findings), encoding="utf-8")
