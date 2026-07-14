# Evidence Gate

Accept a candidate only if all checks pass.

1. **Document identity** — cite the exact document, section, source path, and paragraph. Resolve obsolete documents to the benchmark-selected version when possible.
2. **Normative meaning** — record MUST, MUST NOT, SHOULD, MAY, recommendation, or informative strength. Missing MAY behavior is an optional gap, not noncompliance.
3. **Applicability** — state the runtime condition that reaches the behavior. Reject hypothetical mismatches that cannot occur for supported inputs.
4. **Implementation behavior** — show the actual branch, call, constant, missing handler, or explicit implementation admission. A comment alone is a lead; corroborate it with reachable code or repository-wide absence checks.
5. **Graph-backed counterevidence** — use CodeGraph to inspect callers, callees, alternate handlers, wrappers, generated implementations, feature flags, and external ownership. Record what was checked.
6. **Reproducible location** — include repository-relative path, current line range, enclosing symbol, and exact line-numbered excerpt. Re-read the file before emission.
7. **Deduplication** — merge findings that share the same root cause and requirement. Keep distinct failures when their trigger or impact differs.
8. **Confidence** — require at least 70%. Lower confidence belongs in suppressed candidates, not the final report.

For negative claims such as “not implemented,” search protocol names, message constants, handler names, configuration keys, ports, and action call sites. A zero-result keyword search alone is insufficient; combine structural CodeGraph results with source evidence and scope the conclusion to the audited repository.
