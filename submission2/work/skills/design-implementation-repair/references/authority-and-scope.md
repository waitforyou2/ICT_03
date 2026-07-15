# Authority and Scope

Use this precedence when sources overlap:

1. Competition modification boundaries and explicitly frozen REST contract.
2. Design documents identified as the acceptance baseline.
3. API, configuration, data-model, and event appendices.
4. Existing code comments and unit tests.
5. Public black-box tests.

Public tests reveal behavior but do not override the design. A count typo, stale comment, or current test expectation is not permission to change the contract.

## Protected inputs

Do not modify:

- design documents;
- competition README and platform instructions;
- public black-box test source or POM;
- Maven settings supplied by the platform;
- frozen API URL, method, headers, request and response names/types, success status, or error envelope;
- test harness isolation or administrator-seeding mechanisms.

Build output under `target/` and local dependency caches are not source changes. The protected guard intentionally excludes generated targets.

## Allowed repair scope

Modify production Java, production configuration, module POM files, and design-aligned unit tests under the repair target when necessary. Add services, adapters, events, DTOs, repositories, or configuration classes only when they implement an authoritative requirement without changing the frozen public API.

## Conflict handling

Record a conflict with both citations. Prefer an explicit frozen declaration over a narrative example. Prefer a domain-specific design over a general overview for internal behavior. If two equally authoritative statements remain incompatible, preserve the public API and choose the behavior that satisfies the stricter safety or business invariant; document the choice and uncertainty.

Never resolve a conflict by editing the source-of-truth document.
