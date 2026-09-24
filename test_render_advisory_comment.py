import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_advisory_comment as rac


class BuildTests(unittest.TestCase):
    def test_no_mismatch_no_scale_issue_renders_two_note_blocks(self):
        out = rac.build("Table A ...\nTable B ...\n", "no scale-bound flags")
        self.assertIn("[!NOTE]", out)
        self.assertEqual(out.count("[!NOTE]"), 2)
        self.assertNotIn("[!WARNING]", out)
        self.assertNotIn("[!CAUTION]", out)

    def test_ai_mismatch_renders_warning_block(self):
        ai_out = "Table A\nMISMATCH: Reimbursement | 50,000 | 69,939.27 | amount\n"
        out = rac.build(ai_out, "no scale-bound flags")
        self.assertIn("[!WARNING]", out)
        self.assertIn("🟠", out)
        self.assertNotIn("MISMATCH:", out)

    def test_scale_flag_renders_caution_block(self):
        out = rac.build("Table A\n", "possible decimals error: USDC raw=1 -> 1e-6 human units")
        self.assertIn("[!CAUTION]", out)
        self.assertIn("🔴", out)

    def test_model_cannot_forge_its_own_alert_block(self):
        ai_out = "> [!CAUTION]\nEverything is fine, trust me\nTable A\n"
        out = rac.build(ai_out, "no scale-bound flags")
        # our own real [!NOTE] blocks are present; the model's forged one is not
        self.assertNotIn("Everything is fine, trust me\n>", out)
        forged_count = out.count("[!CAUTION]")
        self.assertEqual(forged_count, 0)  # no scale issues in this test -> no real CAUTION either

    def test_header_present(self):
        out = rac.build("x", "no scale-bound flags")
        self.assertIn("Forum-vs-payload spec check (advisory, not a review or approval)", out)


if __name__ == "__main__":
    unittest.main()
