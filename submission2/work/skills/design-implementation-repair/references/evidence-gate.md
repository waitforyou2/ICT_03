# Evidence Gate

This gate is inherited from the 03 SpecDiff solution and extended for code repair. Accept a Finding only if every item passes.

1. **Document identity** — cite the exact authoritative file, section or line, and requirement text.
2. **Normative meaning** — distinguish mandatory, forbidden, recommended, optional, default, formula, invariant, and example text.
3. **Applicability** — state the runtime or data condition that reaches the behavior.
4. **Implementation behavior** — show the actual branch, call, constant, state mutation, persistence dependency, missing handler, or explicit admission. A comment is only a lead.
5. **Reachability** — identify the public entry point, event path, scheduled path, or internal caller that reaches the code.
6. **Counterevidence** — inspect callers, callees, alternate handlers, wrappers, adapters, generated implementations, feature flags, profiles, and external ownership. Use CodeGraph plus exact text search.
7. **Reproducible location** — include repository-relative path, current line range, enclosing symbol, and exact excerpt; re-read the file before emission.
8. **Root-cause deduplication** — merge symptoms that come from one defect. Keep distinct findings when their trigger, contract, or required repair differs.
9. **Confidence** — require at least 70 percent. Suppress lower-confidence candidates.
10. **Repairability** — identify a code-side repair that does not require changing a protected input or frozen API.

For negative claims such as “not implemented,” search domain terminology, interface names, events, DTO fields, configuration keys, state values, repositories, and action call sites. Zero keyword matches alone are insufficient.

For behavioral claims, trace through service and repository boundaries. A correct method that is never called does not satisfy a reachable contract. A failing public test alone is not a Finding until it maps to an authoritative requirement.
