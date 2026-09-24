#!/usr/bin/env python3
"""Builds the proposal-checks advisory comment body: alert blocks (rendered
by us, from parsed structured data) on top, sanitized rendered-markdown
tables/body below. Never fences the model's tables in ```text -- that made
them unreadable; sanitize.py is what makes rendering them directly safe.
"""
import sys

import advisory_render as ar
from sanitize import sanitize_markdown

AI_OUTPUT_CAP = 20000
SCALE_OUTPUT_CAP = 4000


def build(ai_out_text: str, scale_out_text: str) -> str:
    mismatches, body = ar.parse_mismatches(ai_out_text)
    parts = [
        "**Forum-vs-payload spec check (advisory, not a review or approval)**",
        "",
        ar.render_ai_mismatch_alert(mismatches),
        "",
        ar.render_scale_alert(scale_out_text),
        "",
        sanitize_markdown(body, AI_OUTPUT_CAP),
    ]
    return "\n".join(parts)


def main():
    ai_out_path, scale_out_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(ai_out_path, encoding="utf-8") as f:
        ai_out_text = f.read()
    try:
        with open(scale_out_path, encoding="utf-8") as f:
            scale_out_text = f.read()[:SCALE_OUTPUT_CAP]
    except FileNotFoundError:
        scale_out_text = ""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(build(ai_out_text, scale_out_text))


if __name__ == "__main__":
    main()
