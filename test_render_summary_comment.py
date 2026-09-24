import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_summary_comment as rsc


class RenderTests(unittest.TestCase):
    def test_all_pass_shows_all_checkmarks_no_alert_blocks(self):
        results = {k: "success" for k in rsc.CHECK_ORDER}
        out = rsc.render(results, {}, "100", "100", "https://x/pull/1#issuecomment-1")
        self.assertEqual(out.count("✅"), 4)
        self.assertNotIn("❌", out)
        self.assertNotIn("[!CAUTION]", out)

    def test_address_book_failure_shows_x_and_caution_block_with_details(self):
        results = {**{k: "success" for k in rsc.CHECK_ORDER}, "address-book": "failure"}
        details = {"address-book": "src/x/Foo.sol:12: raw address 0xabc not in the address book"}
        out = rsc.render(results, details, "100", "100", "")
        self.assertIn("❌ **address-book**", out)
        self.assertIn("[!CAUTION]", out)
        self.assertIn("Foo.sol:12", out)
        self.assertIn("🔴", out)

    def test_coverage_failure_shows_measured_vs_required(self):
        results = {**{k: "success" for k in rsc.CHECK_ORDER}, "coverage": "failure"}
        out = rsc.render(results, {"coverage": "src/x/Foo.sol:20"}, "83", "100", "")
        self.assertIn("83% measured", out)
        self.assertIn("100% required", out)
        self.assertIn("Foo.sol:20", out)

    def test_advisory_failure_is_not_blocking_no_caution_block(self):
        results = {**{k: "success" for k in rsc.CHECK_ORDER}, "advisory": "failure"}
        out = rsc.render(results, {}, "100", "100", "")
        self.assertIn("❌ **advisory**", out)
        self.assertNotIn("[!CAUTION]", out)

    def test_advisory_link_included_when_present(self):
        results = {k: "success" for k in rsc.CHECK_ORDER}
        out = rsc.render(results, {}, "100", "100", "https://github.com/x/y/pull/1#issuecomment-99")
        self.assertIn("https://github.com/x/y/pull/1#issuecomment-99", out)

    def test_details_are_sanitized(self):
        results = {**{k: "success" for k in rsc.CHECK_ORDER}, "spelling": "failure"}
        details = {"spelling": "src/x.md:3: <script>alert(1)</script> misspelled 'wierd'"}
        out = rsc.render(results, details, "100", "100", "")
        self.assertNotIn("<script>", out)

    def test_missing_details_does_not_crash(self):
        results = {**{k: "success" for k in rsc.CHECK_ORDER}, "coverage": "failure"}
        out = rsc.render(results, {}, "", "", "")
        self.assertIn("[!CAUTION]", out)


if __name__ == "__main__":
    unittest.main()
