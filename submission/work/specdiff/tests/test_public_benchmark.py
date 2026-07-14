from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specdiff.engine import analyze


EXPECTED_TOPICS = {
    "nd-option-limit",
    "proxy-random-delay",
    "proxy-unsolicited-na",
    "ipv6-fragment-chain",
    "dhcpv6-absent",
    "mld-misrouting",
}


class PublicBenchmarkRegressionTests(unittest.TestCase):
    def test_all_six_known_topics_without_issue_files_as_input(self):
        challenge = Path(__file__).resolve().parents[4]
        repo = challenge / "code" / "f-stack"
        docs = challenge / "Difference" / "benchmark.md"
        cache = challenge / "submission" / "work" / "specdiff" / "cache"
        with tempfile.TemporaryDirectory() as output:
            summary, findings = analyze(
                repo, docs, output, cache,
                allow_network=False, codegraph="off",
            )
        topics = {tag for finding in findings for tag in finding.tags}
        by_topic = {
            tag: finding for finding in findings for tag in finding.tags
            if tag in EXPECTED_TOPICS
        }
        self.assertTrue(EXPECTED_TOPICS <= topics, EXPECTED_TOPICS - topics)
        self.assertIn(by_topic["proxy-random-delay"].requirement.strength, {"should", "recommendation"})
        self.assertIn(by_topic["ipv6-fragment-chain"].requirement.strength, {"must", "must_not"})
        self.assertFalse(any("/issues/" in finding.requirement.source_path.replace("\\", "/") for finding in findings))
        self.assertFalse(any("hard-limit" in finding.tags for finding in findings))
        self.assertEqual(6, summary.findings)


if __name__ == "__main__":
    unittest.main()
