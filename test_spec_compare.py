import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_compare as sc


class CompareTests(unittest.TestCase):
    def test_matching_amount_and_recipient_is_clean(self):
        forum = [{"action": "Reimburse", "asset": "aEthLidoGHO", "amount": "50,000",
                  "recipient": "TokenLogic 0xAA088dfF3dcF619664094945028d44E779F19894", "network": "Ethereum"}]
        payload = [{"amount": "50,000", "recipient": "0xAA088dfF3dcF619664094945028d44E779F19894", "decimals": 18}]
        out = sc.compare(forum, payload)
        self.assertEqual(out["warnings"], [])
        self.assertEqual(out["unexplained"], [])
        self.assertEqual(out["forum_only_count"], 0)

    def test_amount_mismatch_on_matched_recipient_is_a_warning(self):
        forum = [{"action": "Reimburse", "asset": "aEthLidoGHO", "amount": "50,000",
                  "recipient": "0xAA088dfF3dcF619664094945028d44E779F19894", "network": "Ethereum"}]
        payload = [{"amount": "35,000", "recipient": "0xAA088dfF3dcF619664094945028d44E779F19894", "decimals": 18}]
        out = sc.compare(forum, payload)
        self.assertEqual(len(out["warnings"]), 1)
        self.assertIn("amount", out["warnings"][0]["detail"])
        self.assertEqual(out["unexplained"], [])

    def test_payload_item_with_no_forum_counterpart_is_unexplained(self):
        forum = []
        payload = [{"amount": "50,000", "recipient": "0xAA088dfF3dcF619664094945028d44E779F19894", "decimals": 18}]
        out = sc.compare(forum, payload)
        self.assertEqual(len(out["unexplained"]), 1)
        self.assertEqual(out["warnings"], [])

    def test_forum_items_with_no_payload_counterpart_are_counted_not_warned(self):
        forum = [
            {"action": "Acquire", "asset": "GHO", "amount": "8M", "recipient": None, "network": "Ethereum"},
            {"action": "Refresh Allowance", "asset": "USDC", "amount": None, "recipient": "MainnetSwapSteward", "network": "Ethereum"},
        ]
        payload = []
        out = sc.compare(forum, payload)
        self.assertEqual(out["forum_only_count"], 2)
        self.assertEqual(out["warnings"], [])
        self.assertEqual(out["unexplained"], [])

    def test_recipient_mismatch_on_amount_matched_is_flagged(self):
        # same amount coincidentally, but payload recipient has an address that
        # doesn't match any forum address -> goes to unexplained, not warnings,
        # since matching is address-driven.
        forum = [{"action": "Reimburse", "asset": "aEthLidoGHO", "amount": "50,000",
                  "recipient": "0xAA088dfF3dcF619664094945028d44E779F19894", "network": "Ethereum"}]
        payload = [{"amount": "50,000", "recipient": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "decimals": 18}]
        out = sc.compare(forum, payload)
        self.assertEqual(len(out["unexplained"]), 1)

    def test_no_recipient_address_on_payload_side_is_unexplained(self):
        forum = [{"action": "Reimburse", "asset": "GHO", "amount": "50,000", "recipient": None, "network": "Ethereum"}]
        payload = [{"amount": "50,000", "recipient": None, "decimals": 18}]
        out = sc.compare(forum, payload)
        self.assertEqual(len(out["unexplained"]), 1)


if __name__ == "__main__":
    unittest.main()
