# Repair Policy

## Finding to Repair Plan

Create the plan before changing code. Each plan must include:

- Finding ID and authoritative requirement;
- intended postcondition;
- root cause and reachable path;
- candidate repairs considered and why the chosen one is smallest;
- production files and symbols to change;
- callers, interfaces, events, data, transactions, and tests in the blast radius;
- public API fields and statuses that must remain frozen;
- concurrency, idempotency, ownership, compatibility, and rollback risks;
- targeted verification and regression verification.

Reject plans that say only “make the test pass,” “implement the document,” or “refactor the module.”

## Patch discipline

1. Patch one coherent root-cause cluster at a time.
2. Reuse an existing interface when it represents the documented boundary.
3. Add an adapter in the application composition module when two modules need wiring without direct repository access.
4. Keep strong-consistency work in the main transaction and isolate explicitly non-critical event listeners after commit.
5. Make idempotency durable in the domain model or repository query, not process-local only when persistence is required.
6. Use configured clocks, limits, rates, and defaults instead of literals when the design exposes configuration.
7. Preserve DTO shapes. Add internal DTOs rather than mutating frozen public DTOs.
8. Do not delete tests, weaken assertions, catch and ignore required failures, return fake success, or introduce fixture-specific branches.
9. Re-read every changed file and inspect the diff before verification.

## Rollback and re-plan conditions

Rollback the current patch cluster and re-plan when:

- compilation fails in an unrelated module because the plan missed an interface contract;
- a public API mapping, field, type, header, or status changes;
- the patch touches protected files;
- the changed-file set expands materially beyond the plan;
- passing baseline behavior regresses without a design justification;
- a new alternate implementation invalidates the Finding;
- the repair needs broad rewriting where a local adapter or guard would satisfy the contract.

## Completion semantics

Mark a Finding `fixed` only after successful verification evidence is attached. Use `partially_fixed`, `suppressed`, or `unresolved` honestly. A compile pass alone does not verify a behavioral repair.
