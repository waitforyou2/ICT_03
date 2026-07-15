#!/usr/bin/env python3
"""Run reproducible Maven verification with supplied settings and repository."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def resolve_maven(explicit: str | None) -> str:
    candidates = [explicit, os.environ.get("MAVEN")]
    maven_home = os.environ.get("MAVEN_HOME")
    if maven_home:
        candidates.extend(
            [str(Path(maven_home) / "bin" / "mvn"), str(Path(maven_home) / "bin" / "mvn.cmd")]
        )
    candidates.extend([shutil.which("mvn"), shutil.which("mvn.cmd")])
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError("Maven was not found; put mvn on PATH or pass --maven")


def command_for(
    executable: str, project: Path, settings: Path, repository: Path, goals: list[str]
) -> list[str]:
    return [
        executable,
        "-B",
        "-ntp",
        "-s", str(settings),
        f"-Dmaven.repo.local={repository}",
        "-Dproject.build.sourceEncoding=UTF-8",
        "-Dproject.reporting.outputEncoding=UTF-8",
        "-f", str(project),
        *goals,
    ]


def parse_surefire(project_root: Path) -> dict:
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    reports = []
    for report in project_root.rglob("target/surefire-reports/TEST-*.xml"):
        try:
            root = ET.parse(report).getroot()
        except (ET.ParseError, OSError):
            continue
        values = {
            key: int(float(root.attrib.get(key, "0")))
            for key in totals
        }
        for key, value in values.items():
            totals[key] += value
        reports.append(str(report))
    totals["reports"] = reports
    return totals


def run_step(
    name: str,
    command: list[str],
    cwd: Path,
    output: Path,
    test_root: Path,
    java_home: Path | None,
) -> dict:
    log_path = output / f"{name}.log"
    started = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("COMMAND " + " ".join(command) + "\n\n")
        environment = {**os.environ, "MAVEN_OPTS": os.environ.get("MAVEN_OPTS", "")}
        if java_home:
            environment["JAVA_HOME"] = str(java_home)
            environment["PATH"] = str(java_home / "bin") + os.pathsep + environment.get("PATH", "")
        process = subprocess.run(
            command,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            env=environment,
        )
    tests = parse_surefire(test_root)
    return {
        "name": name,
        "command": command,
        "exit_code": process.returncode,
        "passed": process.returncode == 0,
        "elapsed_seconds": round(time.time() - started, 3),
        "log": str(log_path),
        **tests,
    }


def phase_steps(phase: str) -> list[tuple[str, str, list[str]]]:
    compile_step = ("compile", "code", ["test", "-DskipTests"])
    unit_step = ("unit", "code", ["test"])
    install_step = ("install", "code", ["install", "-DskipTests"])
    public_step = ("public", "tests", ["test"])
    mapping = {
        "compile": [compile_step],
        "unit": [unit_step],
        "install": [install_step],
        "public": [install_step, public_step],
        "acceptance": [compile_step, install_step, public_step],
        "all": [unit_step, install_step, public_step],
    }
    return mapping[phase]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--maven", help="Explicit Maven executable when mvn is not on PATH")
    parser.add_argument("--java-home", type=Path, help="Explicit JDK home when JAVA_HOME is unset")
    parser.add_argument(
        "--settings",
        type=Path,
        help="Maven settings override; defaults to <assets>/maven-settings.xml",
    )
    parser.add_argument(
        "--repository",
        type=Path,
        help="Local Maven repository override; defaults to <assets>/maven-repo",
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=("compile", "unit", "install", "public", "acceptance", "all"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assets = args.assets.resolve()
    code = args.code.resolve()
    output = args.output.resolve()
    maven = resolve_maven(args.maven)
    java_home = args.java_home.resolve() if args.java_home else None
    if java_home and not (java_home / "bin" / ("java.exe" if os.name == "nt" else "java")).is_file():
        raise SystemExit(f"Invalid --java-home: {java_home}")
    settings = args.settings.resolve() if args.settings else assets / "maven-settings.xml"
    repository = args.repository.resolve() if args.repository else assets / "maven-repo"
    tests = assets / "test-cases"
    code_pom = code / "pom.xml"
    test_pom = tests / "pom.xml"

    for required in (settings, code_pom):
        if not required.is_file():
            raise SystemExit(f"Required file does not exist: {required}")
    if args.phase in {"public", "acceptance", "all"} and not test_pom.is_file():
        raise SystemExit(f"Public test POM does not exist: {test_pom}")

    repository.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for name, project, goals in phase_steps(args.phase):
        pom = code_pom if project == "code" else test_pom
        test_root = code if project == "code" else tests
        command = command_for(maven, pom, settings, repository, goals)
        result = run_step(name, command, assets, output, test_root, java_home)
        results.append(result)
        print(
            f"VERIFY_STEP name={name} exit={result['exit_code']} "
            f"tests={result['tests']} failures={result['failures']} errors={result['errors']}"
        )
        if not result["passed"]:
            break

    payload = {
        "schema_version": "1.0",
        "phase": args.phase,
        "assets": str(assets),
        "code": str(code),
        "passed": len(results) == len(phase_steps(args.phase)) and all(item["passed"] for item in results),
        "steps": results,
    }
    summary = output / f"verification-{args.phase}.json"
    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VERIFY_COMPLETE phase={args.phase} passed={str(payload['passed']).lower()} summary={summary}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
