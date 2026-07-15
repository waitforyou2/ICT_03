---
name: design-implementation-repair
description: Audit design documents, API contracts, and source code for implementation inconsistencies, then plan and apply minimal code repairs and verify the result. Use when Codex must compare specifications with an existing repository, investigate missing or contradictory behavior with CodeGraph, repair Java/Spring or similar projects without changing the design source of truth, preserve frozen APIs, and produce an evidence-backed Finding → Repair Plan → Patch → Verification report.
---

# Design Implementation Repair

Treat design documents as the source of truth and deliver a verified code repair. Reuse the SpecDiff discipline: retrieve candidates in both directions, require exact evidence and counterevidence, then add a gated repair loop.

## Inputs

Identify these paths before editing:

- `ASSET_ROOT`: directory containing the competition README, design documents, code, tests, and Maven settings.
- `CODE_ROOT`: repair target, normally `<ASSET_ROOT>/code`.
- `OUTPUT_ROOT`: report directory outside protected inputs.
- `SKILL_ROOT`: this skill directory.
- `CODEGRAPH_BIN`: `<submission>/work/.runtime/node_modules/.bin/codegraph` after setup; from `SKILL_ROOT`, this is `../../.runtime/node_modules/.bin/codegraph`.

Edit `CODE_ROOT` in place unless `INSTRUCTION.md` gives another result location. Never edit a design document to match existing code.

## Load the relevant references

Read these files before the corresponding action:

1. Read [authority-and-scope.md](references/authority-and-scope.md) before selecting the source of truth or editing.
2. Read [evidence-gate.md](references/evidence-gate.md) before accepting a Finding.
3. Read [codegraph-playbook.md](references/codegraph-playbook.md) before initializing or querying CodeGraph.
4. Read [repair-policy.md](references/repair-policy.md) before writing a Repair Plan or patch.
5. Read [verification.md](references/verification.md) before running tests or declaring completion.
6. For ShopHub or the design-implementation-consistency competition, also read [shophub-contracts.md](references/shophub-contracts.md).
7. Read [report-format.md](references/report-format.md) before writing the final report.

## Execute the workflow

### 1. Freeze scope and establish the baseline

1. Resolve all input paths to absolute paths.
2. Create `OUTPUT_ROOT` without placing it under `CODE_ROOT`.
3. Snapshot protected inputs:

   ```bash
   python3 "$SKILL_ROOT/scripts/protected_guard.py" snapshot \
     --assets "$ASSET_ROOT" --output "$OUTPUT_ROOT/protected-files.json"
   ```

4. Read the competition README, platform instructions, every design document, root and module POM files, and existing public-test descriptions.
5. Record authority conflicts instead of silently choosing convenient behavior. Public tests are observations, not the specification.
6. Run a baseline compile and public test when feasible; retain the failing test names and logs as evidence.

### 2. Detect inconsistencies using the SpecDiff method

Run the deterministic candidate scan first:

```bash
python3 "$SKILL_ROOT/scripts/contract_scan.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --json "$OUTPUT_ROOT/candidates.json" \
  --markdown "$OUTPUT_ROOT/candidates.md"
```

Build or refresh CodeGraph at the exact code root. Use the commands in the playbook. Then perform both retrieval directions:

- **Requirement-driven:** For every normative clause, locate the controller, DTO, service, state transition, event, configuration, persistence owner, and tests that implement it.
- **Code-driven:** Inspect suspicious constants, placeholders, fake data, direct repository dependencies, broad exception handling, forbidden routes, state mutations, event listeners, and unguarded side effects; map each candidate back to an authoritative requirement.

The scanner produces leads, not accepted findings. Apply the evidence gate to every lead. Search for alternate implementations before asserting that behavior is missing.

### 3. Create a Finding

Accept a Finding only when it contains:

- stable ID and classification;
- exact design path, section or line, and requirement text;
- exact current code path, line range, symbol, and excerpt;
- actual reachable behavior and applicability;
- root cause, not merely a failing test symptom;
- CodeGraph or repository-wide counterevidence check;
- confidence of at least 70 percent;
- affected API and invariants.

Use these classifications:

- `contract_contradiction`: implemented behavior contradicts a mandatory contract;
- `missing_behavior`: required behavior has no implementation after counterevidence search;
- `forbidden_extra_behavior`: code exposes or performs behavior the contract forbids;
- `architecture_boundary`: dependency, storage, or ownership violates module design;
- `workflow_state`: state transition or operation order violates the documented workflow;
- `nonfunctional_contract`: security, idempotency, concurrency, transaction, event isolation, audit, time, or rate-limit requirement is violated.

Suppress a candidate when document identity, applicability, reachability, or current source evidence cannot be established.

### 4. Write the Repair Plan before patching

For each accepted Finding, inspect the exact symbol and blast radius:

```bash
"$CODEGRAPH_BIN" node <symbol> --path "$CODE_ROOT"
"$CODEGRAPH_BIN" impact <symbol> --path "$CODE_ROOT" --depth 2 --json
"$CODEGRAPH_BIN" callers <symbol> --path "$CODE_ROOT"
```

Write a Repair Plan that states:

- intended behavior and invariant;
- root cause;
- smallest production files that must change;
- interfaces, callers, events, persistence, and tests affected;
- frozen API elements that must remain identical;
- migration or compatibility concern;
- exact targeted and regression verification commands;
- rollback condition.

Do not patch a Finding without this plan. Merge findings that share one root cause so one coherent patch fixes them.

### 5. Apply a minimal patch

Implement only the planned behavior:

1. Preserve frozen URL, method, header, request/response fields, types, status codes, and error envelope.
2. Prefer existing public interfaces and module boundaries over cross-module repository access.
3. Preserve unrelated passing behavior.
4. Do not hardcode public-test IDs, fixtures, or expected values.
5. Do not disable validation, security, or tests to obtain a pass.
6. Add or update production code and design-aligned unit tests only when needed.
7. Compile after every coherent patch cluster.
8. Run `codegraph sync "$CODE_ROOT"` after source edits.
9. Re-run `impact` or `affected` for changed files before moving to the next cluster.

If a patch expands beyond its planned files or changes an API shape, stop, revert that patch, and re-plan.

### 6. Verify in layers and feed failures back

Use [verification.md](references/verification.md) and the bundled verifier. The minimum completion ladder is:

1. production and test-source compilation;
2. targeted unit tests for the changed domain when trustworthy;
3. install repaired modules to the supplied local Maven repository;
4. public black-box tests;
5. protected-input hash verification;
6. design-to-code re-audit of every repaired contract;
7. negative scan for forbidden routes, placeholders, fake data, stale duplicate models, and API drift.

Treat a failure as new evidence. Map it to an existing Finding or create a new gated Finding; do not patch directly from a stack trace without a contract.

### 7. Complete the report and clean up

Write `repair-report.json` according to [report-format.md](references/report-format.md), then validate it:

```bash
python3 "$SKILL_ROOT/scripts/validate_repair_report.py" \
  "$OUTPUT_ROOT/repair-report.json"
python3 "$SKILL_ROOT/scripts/protected_guard.py" verify \
  --assets "$ASSET_ROOT" --snapshot "$OUTPUT_ROOT/protected-files.json"
```

Remove the CodeGraph project index before handoff if it was created inside `CODE_ROOT`:

```bash
"$CODEGRAPH_BIN" uninit --force "$CODE_ROOT"
```

Finish only when:

- the repaired code builds;
- public acceptance tests pass;
- protected files are unchanged;
- every fixed Finding has a Repair Plan, patch record, and successful verification evidence;
- no unresolved high-confidence mandatory Finding remains;
- the final report validates;
- the result location is explicit.

Do not claim that hidden tests pass. State only the checks actually executed.
