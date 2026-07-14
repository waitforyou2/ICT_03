---
name: specdiff-review
description: Audit a source repository against design documents or RFCs and produce evidence-backed implementation differences. Use for unattended spec-to-code consistency review, protocol compliance analysis, missing behavior detection, control-flow misrouting, hard-limit contradictions, and verification of candidate findings with CodeGraph call paths and exact source locations.
---

# SpecDiff Review

Run a reproducible specification-to-code audit. Treat CodeGraph as the structural code index, the bundled Python engine as the requirement/evidence layer, and your reasoning as the semantic reviewer.

## Inputs

Require three paths:

- source repository or source tree;
- design document file or directory;
- output directory.

Do not use a benchmark answer, issue list, expected-output folder, or prior finding report as analysis input. It is acceptable to use such material only after the run for isolated regression scoring.

## Workflow

1. From the submission root, run:

   ```bash
   bash work/setup.sh
   bash work/run.sh <repo> <docs> <output>
   ```

   `setup.sh` installs the pinned official npm package. Do not download or substitute a bundled CodeGraph binary.

2. Confirm `<output>/run-summary.json` says `complete` and that `codegraph_status` contains `indexed` and a nonzero `explore` count when findings exist.

3. Read `<output>/findings.json`, `<output>/output.md`, and `<output>/codegraph-evidence.md`.

4. For a finding whose graph evidence is ambiguous, query the installed CLI directly from the repository root:

   ```bash
   CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1 \
     <submission>/work/.runtime/node_modules/.bin/codegraph explore \
     "Trace <behavior> from <symbol>; include callers, callees, alternate paths, and counterevidence"
   ```

   Ask behavioral questions with a symbol or file anchor. Prefer one focused `explore` call over broad file crawling.

5. Apply [the evidence gate](references/evidence-gate.md) before accepting, editing, or adding a finding.

6. Return both machine-readable JSON and human-readable Markdown. Preserve stable IDs and exact line excerpts.

## Classification

- Use `normative_contradiction` only for MUST/SHALL/SHOULD behavior contradicted by reachable code.
- Use `optional_capability_gap` for an unimplemented MAY/OPTIONAL behavior; never call it a standards violation.
- Use `feature_gap` when a documented feature/protocol is absent without a universal conformance mandate.
- Use `functional_misrouting` when branch order or dispatch prevents the documented behavior.
- Suppress a candidate if applicability, reachability, document identity, or source evidence cannot be established.

## Completion

Finish only when:

- every reported item has a design citation, actual behavior, exact code evidence, applicability, and counterevidence record;
- every evidence excerpt still matches the current file;
- optional behavior is labelled correctly;
- the JSON and Markdown report the same findings;
- the command exits and prints `RUN_COMPLETE` without human interaction.
