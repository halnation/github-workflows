"""Deterministic extraction of payload-side actions from a
ProtocolV3TestBase-generated diff report (diffs/*.md). No AI involved --
the diff report is the ground truth for what the payload actually executes.

Best-effort: this parser targets the common "decoded value" shape the diff
report emits for ERC20 transfer/approval-style state changes, e.g. a line
containing a human amount, a bracketed [raw, N decimals] pair, and a 0x
address. When the diff report is empty or unparseable (for example, if the
fork test could not complete -- a real live-mainnet-state failure unrelated
to any payload bug), this returns an empty list and the caller must say so
plainly rather than inventing payload data.
"""
import re

DECODED_VALUE_RE = re.compile(
    r"(?P<human>[\d,]+(?:\.\d+)?)\s*\[\s*(?P<raw>\d+)\s*,\s*(?P<decimals>\d+)\s*decimals\s*\]"
)
ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]{40}")


def parse_payload_actions(diff_report_text: str):
    """Returns a list of {"action", "asset", "amount", "decimals",
    "recipient", "network", "raw_line"} extracted from decoded value lines."""
    if not diff_report_text or not diff_report_text.strip():
        return []
    actions = []
    for line in diff_report_text.splitlines():
        m = DECODED_VALUE_RE.search(line)
        if not m:
            continue
        addr_m = ADDRESS_RE.search(line)
        actions.append(
            {
                "action": "Transfer",
                "asset": None,
                "amount": m.group("human"),
                "decimals": int(m.group("decimals")),
                "recipient": addr_m.group(0) if addr_m else None,
                "network": None,
                "raw_line": line.strip(),
            }
        )
    return actions
