#!/usr/bin/env python3
"""Validate the Finding → Repair Plan → Patch → Verification report chain."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CLASSIFICATIONS = {
    "contract_contradiction",
    "missing_behavior",
    "forbidden_extra_behavior",
    "architecture_boundary",
    "workflow_state",
    "nonfunctional_contract",
}
SEVERITIES = {"low", "medium", "high", "critical"}
STATUSES = {"fixed", "partially_fixed", "suppressed", "unresolved"}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_object(value: object, name: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def require_list(value: object, name: str, errors: list[str]) -> list:
    if not isinstance(value, list):
        errors.append(f"{name} must be an array")
        return []
    return value


def validate_finding(item: object, index: int, errors: list[str]) -> None:
    finding = require_object(item, f"findings[{index}]", errors)
    prefix = f"findings[{index}]"
    finding_id = finding.get("id")
    if not nonempty(finding_id) or not re.fullmatch(r"finding-[0-9a-f]{12}", finding_id):
        errors.append(f"{prefix}.id must match finding-<12 lowercase hex>")
    for field in ("title", "root_cause"):
        if not nonempty(finding.get(field)):
            errors.append(f"{prefix}.{field} must be non-empty")
    if finding.get("classification") not in CLASSIFICATIONS:
        errors.append(f"{prefix}.classification is invalid")
    if finding.get("severity") not in SEVERITIES:
        errors.append(f"{prefix}.severity is invalid")
    confidence = finding.get("confidence")
    if not isinstance(confidence, (int, float)) or not 70 <= confidence <= 100:
        errors.append(f"{prefix}.confidence must be between 70 and 100")
    status = finding.get("status")
    if status not in STATUSES:
        errors.append(f"{prefix}.status is invalid")

    requirement = require_object(finding.get("requirement"), f"{prefix}.requirement", errors)
    for field in ("path", "text"):
        if not nonempty(requirement.get(field)):
            errors.append(f"{prefix}.requirement.{field} must be non-empty")
    if not nonempty(str(requirement.get("section", ""))) and not isinstance(requirement.get("line"), int):
        errors.append(f"{prefix}.requirement needs section or integer line")

    implementation = require_object(
        finding.get("implementation"), f"{prefix}.implementation", errors
    )
    for field in ("path", "symbol", "excerpt", "actual_behavior", "applicability"):
        if not nonempty(implementation.get(field)):
            errors.append(f"{prefix}.implementation.{field} must be non-empty")
    if not isinstance(implementation.get("line_start"), int):
        errors.append(f"{prefix}.implementation.line_start must be an integer")

    counterevidence = require_list(
        finding.get("counterevidence"), f"{prefix}.counterevidence", errors
    )
    if not counterevidence or not all(nonempty(value) for value in counterevidence):
        errors.append(f"{prefix}.counterevidence must contain non-empty checks")

    if status == "fixed":
        plan = require_object(finding.get("repair_plan"), f"{prefix}.repair_plan", errors)
        if not nonempty(plan.get("strategy")):
            errors.append(f"{prefix}.repair_plan.strategy must be non-empty")
        for field in ("files", "preserve", "risks", "verification"):
            values = require_list(plan.get(field), f"{prefix}.repair_plan.{field}", errors)
            if not values:
                errors.append(f"{prefix}.repair_plan.{field} must not be empty")

        patch = require_object(finding.get("patch"), f"{prefix}.patch", errors)
        if not require_list(patch.get("files"), f"{prefix}.patch.files", errors):
            errors.append(f"{prefix}.patch.files must not be empty")
        if not nonempty(patch.get("summary")):
            errors.append(f"{prefix}.patch.summary must be non-empty")

        checks = require_list(finding.get("verifications"), f"{prefix}.verifications", errors)
        if not checks:
            errors.append(f"{prefix}.verifications must not be empty")
        elif not any(
            isinstance(check, dict)
            and check.get("passed") is True
            and check.get("exit_code") == 0
            and nonempty(check.get("command"))
            and nonempty(check.get("evidence"))
            for check in checks
        ):
            errors.append(f"{prefix}.verifications needs a successful evidenced command")


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    root = require_object(payload, "report", errors)
    if root.get("schema_version") != "2.0":
        errors.append("schema_version must be '2.0'")
    if root.get("status") != "complete":
        errors.append("status must be 'complete'")
    for field in ("asset_root", "code_root", "result_code"):
        if not nonempty(root.get(field)):
            errors.append(f"{field} must be non-empty")

    require_list(root.get("authority_conflicts"), "authority_conflicts", errors)
    findings = require_list(root.get("findings"), "findings", errors)
    for index, finding in enumerate(findings):
        validate_finding(finding, index, errors)

    global_checks = require_list(root.get("global_verifications"), "global_verifications", errors)
    if not any(
        isinstance(check, dict)
        and check.get("passed") is True
        and check.get("exit_code") == 0
        and nonempty(check.get("command"))
        for check in global_checks
    ):
        errors.append("global_verifications needs at least one successful command")

    protected = require_object(root.get("protected_inputs"), "protected_inputs", errors)
    if protected.get("passed") is not True:
        errors.append("protected_inputs.passed must be true")
    if not nonempty(protected.get("snapshot")):
        errors.append("protected_inputs.snapshot must be non-empty")

    unresolved = require_list(root.get("unresolved"), "unresolved", errors)
    for index, item in enumerate(unresolved):
        if not isinstance(item, dict) or not nonempty(item.get("reason")):
            errors.append(f"unresolved[{index}] must be an object with a reason")
        if isinstance(item, dict) and item.get("mandatory") is True and item.get("confidence", 0) >= 70:
            errors.append(f"unresolved[{index}] is a high-confidence mandatory Finding")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"REPORT_INVALID: {exc}", file=sys.stderr)
        return 1
    errors = validate(payload)
    if errors:
        print("REPORT_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"REPORT_VALID findings={len(payload.get('findings', []))} "
        f"global_verifications={len(payload.get('global_verifications', []))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
