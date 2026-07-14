from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return f"{prefix}-{sha256(payload.encode('utf-8')).hexdigest()[:12]}"


@dataclass(slots=True)
class Requirement:
    id: str
    document: str
    source_path: str
    section: str
    text: str
    strength: str
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Requirement":
        return cls(**value)


@dataclass(slots=True)
class CodeEvidence:
    path: str
    line_start: int
    line_end: int
    symbol: str
    excerpt: str
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CodeEvidence":
        return cls(**value)


@dataclass(slots=True)
class Candidate:
    id: str
    detector: str
    title: str
    finding_type: str
    severity: str
    confidence: int
    requirement_terms: list[str]
    actual_behavior: str
    evidence_chain: list[str]
    applicability: str
    code_evidence: list[CodeEvidence]
    counterevidence_checked: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    requirement: Requirement | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Candidate":
        copied = dict(value)
        copied["code_evidence"] = [
            CodeEvidence.from_dict(item) for item in copied.get("code_evidence", [])
        ]
        requirement = copied.get("requirement")
        copied["requirement"] = Requirement.from_dict(requirement) if requirement else None
        return cls(**copied)


@dataclass(slots=True)
class RunSummary:
    status: str
    repo: str
    docs: str
    started_at: str
    completed_at: str
    source_files: int
    requirements: int
    raw_candidates: int
    findings: int
    suppressed: int
    codegraph_status: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

