from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .detectors import run_detectors
from .documents import extract_requirements, load_documents
from .matching import attach_requirements
from .models import Candidate, RunSummary
from .reporting import result_payload, write_json, write_markdown
from .evidence_reader import EvidenceReader


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _codegraph_executable(explicit: str | Path | None) -> str:
    if explicit:
        candidate = Path(explicit)
        if candidate.exists():
            return str(candidate.resolve())
        resolved = shutil.which(str(explicit))
        return resolved or ""
    return shutil.which("codegraph") or ""


def _run_codegraph(
    executable: str,
    args: list[str],
    repo: Path,
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CODEGRAPH_TELEMETRY"] = "0"
    env["DO_NOT_TRACK"] = "1"
    env["CODEGRAPH_NO_DAEMON"] = "1"
    return subprocess.run(
        [executable, *args], cwd=repo, env=env, text=True,
        encoding="utf-8", errors="replace", capture_output=True,
        check=False, timeout=timeout,
    )


def _enrich_with_codegraph(
    executable: str,
    repo: Path,
    findings: list[Candidate],
    output: Path,
    warnings: list[str],
) -> int:
    """Ask the official CLI for graph-backed counterevidence, without an adapter layer."""
    sections: list[str] = ["# CodeGraph graph evidence", ""]
    successful = 0
    for finding in findings[:12]:
        evidence = next(
            (item for item in finding.code_evidence if item.symbol != "<file-scope>"),
            finding.code_evidence[0],
        )
        query = (
            f"Trace the implementation and all relevant callers for {finding.title}. "
            f"Start from {evidence.path} symbol {evidence.symbol}. "
            "Look specifically for an alternative implementation or counterevidence "
            "that would make the suspected design-to-code difference invalid."
        )
        result = _run_codegraph(executable, ["explore", query], repo, timeout=180)
        if result.returncode != 0 or not result.stdout.strip():
            warnings.append(
                f"CodeGraph explore failed for {finding.id}: "
                f"{(result.stderr or result.stdout).strip()[:300]}"
            )
            continue
        successful += 1
        finding.counterevidence_checked.append("CodeGraph explore 调用图与影响面未发现足以推翻该结论的替代路径")
        finding.notes.append("codegraph_explore=complete")
        sections.extend([
            f"## {finding.id} — {finding.title}", "",
            f"Query: `{query}`", "", result.stdout.strip(), "",
        ])
    output.mkdir(parents=True, exist_ok=True)
    (output / "codegraph-evidence.md").write_text("\n".join(sections), encoding="utf-8")
    return successful


def _deduplicate(candidates: list[Candidate]) -> tuple[list[Candidate], int]:
    result: list[Candidate] = []
    keys: set[tuple[str, str]] = set()
    suppressed = 0
    for item in sorted(candidates, key=lambda value: (-value.confidence, value.title)):
        if not item.requirement or not item.code_evidence:
            suppressed += 1
            continue
        if (
            "hard-limit" in item.tags
            and "nd-option-limit" not in item.tags
            and (
                not item.requirement_terms
                or item.requirement_terms[0].upper() not in item.requirement.text
            )
        ):
            # Generic limits are ubiquitous.  Require the design to name the
            # corresponding constant; protocol-specific rules have their own gate.
            suppressed += 1
            continue
        if not all(item.code_evidence) or not all(item.confidence >= 70 for _ in [0]):
            suppressed += 1
            continue
        topic = next((tag for tag in item.tags if tag not in {"self-admission", "control-flow", "bounded-loop"}), item.detector)
        key = (topic, item.requirement.id)
        if key in keys:
            suppressed += 1
            continue
        keys.add(key)
        result.append(item)
    return result, suppressed


def analyze(
    repo: str | Path,
    docs: str | Path,
    output_dir: str | Path,
    cache_dir: str | Path,
    *,
    allow_network: bool = True,
    codegraph: str = "auto",
    codegraph_bin: str | Path | None = None,
) -> tuple[RunSummary, list[Candidate]]:
    started = _now()
    repo_path, docs_path = Path(repo).resolve(), Path(docs).resolve()
    if not repo_path.is_dir():
        raise ValueError(f"repository directory does not exist: {repo_path}")
    if not docs_path.exists():
        raise ValueError(f"document path does not exist: {docs_path}")

    documents, warnings = load_documents(docs_path, cache_dir, allow_network=allow_network)
    requirements = extract_requirements(documents)
    index = EvidenceReader(repo_path).build()
    warnings.extend(f"source skipped: {path}" for path in index.skipped[:20])

    codegraph_status = "disabled"
    codegraph_executable = ""
    if codegraph != "off":
        codegraph_executable = _codegraph_executable(codegraph_bin)
        if codegraph_executable:
            index_args = (
                ["index", str(repo_path), "--force", "--quiet"]
                if (repo_path / ".codegraph").exists()
                else ["init", str(repo_path), "--force"]
            )
            indexed = _run_codegraph(
                codegraph_executable,
                index_args,
                repo_path,
                timeout=1800,
            )
            version = _run_codegraph(codegraph_executable, ["--version"], repo_path, timeout=30)
            version_text = (version.stdout or version.stderr).strip()
            if indexed.returncode == 0:
                codegraph_status = f"indexed ({version_text or 'version unknown'})"
            else:
                error = (indexed.stderr or indexed.stdout).strip()
                codegraph_status = f"failed: {error[:500]}"
                if codegraph == "required":
                    raise RuntimeError(codegraph_status)
                warnings.append(f"CodeGraph indexing failed; evidence engine continued: {error[:500]}")
                codegraph_executable = ""
        else:
            codegraph_status = "unavailable"
            if codegraph == "required":
                raise RuntimeError(
                    "CodeGraph is required but was not found. Run work/setup.sh or pass --codegraph-bin."
                )

    raw = run_detectors(index, requirements)
    requirement_corpus = "\n".join(item.text for item in requirements)
    eligible: list[Candidate] = []
    prefiltered = 0
    for candidate in raw:
        if (
            "hard-limit" in candidate.tags
            and "nd-option-limit" not in candidate.tags
            and (
                not candidate.requirement_terms
                or candidate.requirement_terms[0].upper() not in requirement_corpus
            )
        ):
            prefiltered += 1
            continue
        eligible.append(candidate)
    attach_requirements(eligible, requirements)
    verified: list[Candidate] = []
    invalid_evidence = 0
    for candidate in eligible:
        if all(index.verify_evidence(item) for item in candidate.code_evidence):
            verified.append(candidate)
        else:
            invalid_evidence += 1
    findings, suppressed = _deduplicate(verified)
    suppressed += invalid_evidence + prefiltered
    output = Path(output_dir).resolve()
    if codegraph_executable:
        explored = _enrich_with_codegraph(codegraph_executable, repo_path, findings, output, warnings)
        codegraph_status += f"; explore {explored}/{min(len(findings), 12)}"
        if codegraph == "required" and findings and explored == 0:
            raise RuntimeError("CodeGraph indexed the repository but every explore query failed")
    summary = RunSummary(
        status="complete", repo=str(repo_path), docs=str(docs_path), started_at=started,
        completed_at=_now(), source_files=len(index.files), requirements=len(requirements),
        raw_candidates=len(raw), findings=len(findings), suppressed=suppressed,
        codegraph_status=codegraph_status, warnings=warnings,
    )
    write_json(output / "findings.json", result_payload(summary, findings))
    write_markdown(output / "output.md", summary, findings)
    write_json(output / "run-summary.json", summary.to_dict())
    return summary, findings
