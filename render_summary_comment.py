#!/usr/bin/env python3
"""Builds the proposal-checks summary comment: one line per check with
its pass/fail icon, and an alert block per failing blocking check with the
concrete details it produced. Never fails on its own -- called from a job
that must post something even when every upstream job errored."""
import sys

from sanitize import sanitize_markdown

CHECK_ORDER = ["address-book", "spelling", "coverage", "advisory"]
BLOCKING = {"address-book", "spelling", "coverage"}


def _icon(result: str) -> str:
    return "✅" if result == "success" else "❌"


def render(results: dict, details: dict, coverage_pct: str, coverage_min: str, advisory_url: str) -> str:
    lines = ["**Check summary**", ""]
    for name in CHECK_ORDER:
        result = results.get(name, "unknown")
        lines.append(f"- {_icon(result)} **{name}**")

    for name in CHECK_ORDER:
        result = results.get(name, "unknown")
        if result == "success" or name not in BLOCKING:
            continue
        raw_detail = details.get(name, "").strip()
        if name == "coverage":
            header = f"coverage: {coverage_pct or '?'}% measured, {coverage_min or '?'}% required"
            body_lines = [header]
            if raw_detail:
                body_lines.append("uncovered lines (sample):")
                body_lines.extend(f"  {line}" for line in raw_detail.splitlines() if line.strip())
        else:
            body_lines = raw_detail.splitlines() if raw_detail else ["(no details captured)"]
        safe_lines = [sanitize_markdown(line, 300) for line in body_lines if line.strip()]
        block = "\n".join(f"> 🔴 {line}" for line in safe_lines) or "> 🔴 (no details captured)"
        lines.append("")
        lines.append(f"> [!CAUTION]\n> **{name} failed**\n{block}")

    if results.get("advisory") and advisory_url:
        lines.append("")
        lines.append(f"Advisory comment (forum-vs-payload spec check): {advisory_url}")

    return "\n".join(lines)


def main():
    import json

    payload = json.load(sys.stdin)
    out = render(
        payload["results"],
        payload["details"],
        payload.get("coverage_pct", ""),
        payload.get("coverage_min", ""),
        payload.get("advisory_url", ""),
    )
    sys.stdout.write(out)


if __name__ == "__main__":
    main()
