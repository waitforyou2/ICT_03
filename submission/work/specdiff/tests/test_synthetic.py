from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specdiff.engine import analyze
from specdiff.evidence_reader import EvidenceReader


class SyntheticGeneralizationTests(unittest.TestCase):
    def run_case(self, design: str, source: str):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, docs, output, cache = root / "repo", root / "docs", root / "output", root / "cache"
            repo.mkdir()
            docs.mkdir()
            (repo / "implementation.c").write_text(source, encoding="utf-8")
            (docs / "design.md").write_text(design, encoding="utf-8")
            summary, findings = analyze(repo, docs, output, cache, allow_network=False, codegraph="off")
            self.assertEqual("complete", summary.status)
            self.assertTrue((output / "findings.json").exists())
            self.assertTrue((output / "output.md").exists())
            return findings

    def test_four_unseen_difference_patterns(self):
        findings = self.run_case(
            """# Design

1. Collection handling

MAX_ENTRIES identifies the collection bound. The parser MUST process all valid entries without silently stopping early.

2. Retry policy

MAX_RETRIES MUST be 3 for every delivery attempt.

3. Export security

The exporter MUST perform encryption for every record before transmission.

4. Packet classification

The router MUST classify every IPv6 multicast packet with the IPv6-specific handler.

5. Optional telemetry

The service MAY emit an optional heartbeat when idle.
""",
            """static int max_entries = 4;
#define MAX_RETRIES 1

int parse_all(int count) {
    for (int i = 0; i < count; i++) {
        if (i > max_entries) {
            break;
        }
    }
    return 0;
}

// TODO: implement exporter encryption for every record
int export_record(void) { return 0; }

int classify(struct packet *packet) {
    if (is_multicast(packet)) {
        return FILTER_MULTI;
    }
    if (packet->type == IPV6) {
        return FILTER_IPV6;
    }
    return FILTER_UNKNOWN;
}
""",
        )
        tags = {tag for finding in findings for tag in finding.tags}
        self.assertIn("hard-limit", tags)
        self.assertIn("constant-mismatch", tags)
        self.assertIn("self-admitted-gap", tags)
        self.assertIn("branch-preemption", tags)
        self.assertFalse(any("heartbeat" in finding.title.lower() for finding in findings))

    def test_compliant_constant_and_may_absence_are_not_reported(self):
        findings = self.run_case(
            """# Design

1. Retry

MAX_RETRIES MUST be 3.

2. Optional event

The service MAY emit an idle heartbeat.
""",
            """#define MAX_RETRIES 3
int send_with_retry(void) { return MAX_RETRIES; }
""",
        )
        self.assertEqual([], findings)

    def test_evidence_excerpts_are_reproducible(self):
        findings = self.run_case(
            """# Design

1. Retry

MAX_RETRIES MUST be 5 for every attempted message delivery.
""",
            """#define MAX_RETRIES 2
""",
        )
        self.assertEqual(1, len(findings))
        self.assertIn("#define MAX_RETRIES 2", findings[0].code_evidence[0].excerpt)
        self.assertIsNotNone(findings[0].requirement)

    def test_must_not_enabled_flag_is_reported(self):
        findings = self.run_case(
            """# Design

1. Production safety

DEBUG_BYPASS MUST NOT be enabled in any production build because it disables authorization.
""",
            """#define DEBUG_BYPASS 1
int authorize(void) { return DEBUG_BYPASS ? 1 : check_policy(); }
""",
        )
        self.assertEqual(1, len(findings))
        self.assertIn("prohibited-enabled", findings[0].tags)
        self.assertEqual("must_not", findings[0].requirement.strength)

    def test_todo_is_suppressed_when_alternative_implementation_exists(self):
        findings = self.run_case(
            """# Design

1. Export security

The exporter MUST perform encryption for every record before transmission.
""",
            """// TODO: implement exporter encryption for every record in this legacy wrapper
int legacy_export(void) { return encrypt_record(); }

int encrypt_record(void) {
    return aes_gcm_encrypt();
}
""",
        )
        self.assertEqual([], findings)

    def test_stale_evidence_is_rejected_after_source_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source = repo / "value.c"
            source.write_text("#define LIMIT 3\n", encoding="utf-8")
            reader = EvidenceReader(repo).build()
            evidence = reader.evidence("value.c", 1, "original value", before=0, after=0)
            self.assertTrue(reader.verify_evidence(evidence))
            source.write_text("#define LIMIT 4\n", encoding="utf-8")
            self.assertFalse(reader.verify_evidence(evidence))


if __name__ == "__main__":
    unittest.main()
