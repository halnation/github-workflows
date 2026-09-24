import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diff_parser as dp


class ParsePayloadActionsTests(unittest.TestCase):
    def test_empty_text_returns_empty_list(self):
        self.assertEqual(dp.parse_payload_actions(""), [])
        self.assertEqual(dp.parse_payload_actions("   \n  "), [])

    def test_extracts_decoded_value_and_address(self):
        line = "Transfer to 0xAA088dfF3dcF619664094945028d44E779F19894: value: 50,000 [50000000000000000000000, 18 decimals]"
        out = dp.parse_payload_actions(line)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["amount"], "50,000")
        self.assertEqual(out[0]["decimals"], 18)
        self.assertEqual(out[0]["recipient"], "0xAA088dfF3dcF619664094945028d44E779F19894")

    def test_ignores_lines_without_decoded_value(self):
        text = "some unrelated line\nanother line with no brackets"
        self.assertEqual(dp.parse_payload_actions(text), [])

    def test_multiple_decoded_lines(self):
        text = (
            "value: 50,000 [50000000000000000000000, 18 decimals] to 0xAA088dfF3dcF619664094945028d44E779F19894\n"
            "value: 72 [7200000000, 8 decimals] to 0xAA2461f0f0A3dE5fEAF3273eAe16DEF861cf594e\n"
        )
        out = dp.parse_payload_actions(text)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[1]["amount"], "72")
        self.assertEqual(out[1]["decimals"], 8)


if __name__ == "__main__":
    unittest.main()
