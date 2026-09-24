import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import advisory_render as ar


class ParseMismatchesTests(unittest.TestCase):
    def test_parses_a_single_mismatch_line(self):
        text = "some preamble\nMISMATCH: Reimbursement | 50,000 aEthLidoGHO | 69,939.27 aEthLidoGHO | amount\nmore text"
        mismatches, remaining = ar.parse_mismatches(text)
        self.assertEqual(len(mismatches), 1)
        m = mismatches[0]
        self.assertEqual(m["action"], "Reimbursement")
        self.assertEqual(m["forum"], "50,000 aEthLidoGHO")
        self.assertEqual(m["payload"], "69,939.27 aEthLidoGHO")
        self.assertEqual(m["type"], "amount")
        self.assertNotIn("MISMATCH:", remaining)
        self.assertIn("preamble", remaining)
        self.assertIn("more text", remaining)

    def test_parses_multiple_mismatch_lines(self):
        text = (
            "MISMATCH: A | 1 | 2 | amount\n"
            "MISMATCH: B | x | y | address\n"
        )
        mismatches, _ = ar.parse_mismatches(text)
        self.assertEqual(len(mismatches), 2)
        self.assertEqual(mismatches[1]["action"], "B")

    def test_no_mismatch_lines_returns_empty_list(self):
        mismatches, remaining = ar.parse_mismatches("just a normal table\nno special lines here")
        self.assertEqual(mismatches, [])
        self.assertIn("normal table", remaining)


class RenderAiMismatchAlertTests(unittest.TestCase):
    def test_empty_list_renders_note(self):
        out = ar.render_ai_mismatch_alert([])
        self.assertIn("[!NOTE]", out)
        self.assertIn("No mismatches found", out)

    def test_nonempty_list_renders_warning_with_orange_marker(self):
        mismatches = [{"action": "Reimbursement", "forum": "50,000", "payload": "69,939.27", "type": "amount"}]
        out = ar.render_ai_mismatch_alert(mismatches)
        self.assertIn("[!WARNING]", out)
        self.assertIn("🟠", out)
        self.assertIn("Reimbursement", out)
        self.assertIn("50,000", out)
        self.assertIn("69,939.27", out)

    def test_one_line_per_mismatch(self):
        mismatches = [
            {"action": "A", "forum": "1", "payload": "2", "type": "amount"},
            {"action": "B", "forum": "3", "payload": "4", "type": "address"},
        ]
        out = ar.render_ai_mismatch_alert(mismatches)
        self.assertEqual(out.count("🟠"), 2)


class RenderScaleAlertTests(unittest.TestCase):
    def test_no_flags_renders_note(self):
        out = ar.render_scale_alert("no scale-bound flags")
        self.assertIn("[!NOTE]", out)

    def test_no_diff_report_renders_note(self):
        out = ar.render_scale_alert("no diff report was generated for this proposal; decimals-scale check skipped")
        self.assertIn("[!NOTE]", out)

    def test_flags_render_caution_with_red_marker(self):
        out = ar.render_scale_alert(
            "possible decimals error: USDC raw=10000000000000 -> 10000000 human units (outside [1e-06, 1e+09])"
        )
        self.assertIn("[!CAUTION]", out)
        self.assertIn("🔴", out)
        self.assertIn("USDC", out)

    def test_one_line_per_flag(self):
        out = ar.render_scale_alert("flag one\nflag two\nflag three")
        self.assertEqual(out.count("🔴"), 3)


if __name__ == "__main__":
    unittest.main()
