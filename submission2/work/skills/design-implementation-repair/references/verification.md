# Verification

Verification is evidence, not ceremony. Run the narrowest useful check after each patch and the full acceptance ladder before completion.

## Bundled verifier

```bash
python3 "$SKILL_ROOT/scripts/verify_project.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --output "$OUTPUT_ROOT/verification" --phase compile

python3 "$SKILL_ROOT/scripts/verify_project.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --output "$OUTPUT_ROOT/verification" --phase public
```

Phases:

- `compile`: compile all reactor production and test sources without running tests;
- `unit`: run module unit tests;
- `install`: install repaired modules to the supplied local Maven repository;
- `public`: install repaired modules, then run supplied public black-box tests;
- `acceptance`: compile, install, and run public black-box tests;
- `all`: run unit tests followed by public black-box tests.

Use the Maven settings and local repository supplied with the asset. Never fall back silently to user-level Maven settings.

## Required final checks

1. **Compile:** all reactor modules compile.
2. **Targeted behavior:** exercise the fixed rule with a focused unit or existing black-box scenario.
3. **Public acceptance:** all supplied black-box tests pass.
4. **Protected guard:** README, design documents, public tests, and settings match the initial snapshot.
5. **API drift:** compare all documented routes, methods, headers, request/response field names/types, success statuses, and error envelope.
6. **Structural re-audit:** re-run CodeGraph queries for module boundaries, event consumers, callers, and affected tests.
7. **Negative scan:** ensure forbidden routes, fake data, stale placeholders, duplicate owned models, wrong rounding, and bypass paths are absent.
8. **Report validation:** every fixed Finding has plan, patch, and successful verification evidence.

Unit tests in the repair target may encode stale implementation behavior. Do not modify or ignore them merely to make them green. If a unit test conflicts with the authoritative design, update it only as part of the same documented Finding and record why. Public black-box tests are protected and must never be edited.

Do not claim hidden-test success. Record exact commands, exit codes, test totals, failures, errors, skipped counts, and log paths.
