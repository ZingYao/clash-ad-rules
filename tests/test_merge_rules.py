"""验证域名匹配语义和异常缩减保护，不访问真实外部服务。"""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("merge_rules", Path(__file__).parents[1] / "scripts/merge_rules.py")
MERGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MERGE)


class MergeRulesTests(unittest.TestCase):
    def test_duplicate_and_parent_coverage(self):
        output, stats = MERGE.compact(["+.example.com", "+.ads.example.com", "ads.example.com", "example.com", "+.example.com"])
        self.assertEqual(output, ["+.example.com"])
        self.assertEqual(stats["exact_duplicates_removed"], 1)
        self.assertEqual(stats["parent_covered_patterns_removed"], 3)

    def test_exact_domain_does_not_cover_subdomain(self):
        output, _ = MERGE.compact(["example.com", "ads.example.com"])
        self.assertEqual(output, ["ads.example.com", "example.com"])

    def test_child_suffix_does_not_cover_parent(self):
        output, _ = MERGE.compact(["example.com", "+.ads.example.com"])
        self.assertEqual(output, ["+.ads.example.com", "example.com"])

    def test_parent_matching_obeys_label_boundary(self):
        output, _ = MERGE.compact(["+.example.com", "+.evil-example.com", "notexample.com"])
        self.assertEqual(len(output), 3)

    def test_output_is_stable(self):
        rules = ["+.b.example.com", "+.example.com", "other.test"]
        self.assertEqual(MERGE.compact(rules), MERGE.compact(list(reversed(rules))))

    def test_parser_quotes_comments_and_case(self):
        self.assertEqual(MERGE.parse_payload("# source\npayload:\n  - '+.Example.COM'\n  - ads.other.test\n"), ["+.example.com", "ads.other.test"])

    def test_reject_unknown_or_empty_syntax(self):
        for content in ["payload:\n", "other: key", "payload:\n - '*.example.com'", "payload:\n - '.example.com'", "payload:\n - '+.'", "payload:\n - '+.example.com", "payload:\n - example.com # inline"]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                MERGE.parse_payload(content)

    def test_counts_and_shrink_guard(self):
        sources = [(name, b"", ["example.com"] * count) for name, count in MERGE.MINIMUM_ENTRIES.items()]
        MERGE.check_counts(sources, 100000)
        with self.assertRaises(ValueError):
            MERGE.check_counts(sources[:-1], 100000)
        with self.assertRaises(ValueError):
            MERGE.check_counts([(n, b, r[:1]) for n, b, r in sources], 1)
        previous = {"sources": {n: {"entries": len(r) * 2} for n, _, r in sources}, "output_entries": 100000}
        with self.assertRaises(ValueError):
            MERGE.check_counts(sources, 100000, previous)
        previous = {"sources": {n: {"entries": len(r)} for n, _, r in sources}, "output_entries": 200000}
        with self.assertRaises(ValueError):
            MERGE.check_counts(sources, 100000, previous)


if __name__ == "__main__":
    unittest.main()
