"""Parses the spec-check model's structured mismatch lines and renders
GitHub alert blocks for them, plus for the deterministic scale_check output.
Only this code may emit `> [!...]` alert syntax in the posted comment --
sanitize.sanitize_markdown() strips any the model tried to produce itself.

Expected model output contract (see prompts/spec-check.md): zero or more
lines of the exact form
    MISMATCH: <action> | <forum value> | <payload value> | <type>
anywhere in the response. Everything else is free-form markdown body text.
"""
import re

MISMATCH_LINE_RE = re.compile(
    r"^MISMATCH:\s*(?P<action>[^|\n]+)\|\s*(?P<forum>[^|\n]+)\|\s*(?P<payload>[^|\n]+)\|\s*(?P<type>[^|\n]+)$",
    re.MULTILINE,
)


def parse_mismatches(model_output: str):
    """Returns (mismatches, remaining_body). remaining_body has the MISMATCH
    lines removed so they aren't duplicated under the rendered tables."""
    mismatches = [
        {
            "action": m.group("action").strip(),
            "forum": m.group("forum").strip(),
            "payload": m.group("payload").strip(),
            "type": m.group("type").strip(),
        }
        for m in MISMATCH_LINE_RE.finditer(model_output)
    ]
    remaining = MISMATCH_LINE_RE.sub("", model_output).strip()
    return mismatches, remaining


def render_ai_mismatch_alert(mismatches) -> str:
    if not mismatches:
        return "> [!NOTE]\n> No mismatches found."
    lines = [
        f"> 🟠 **{m['action']}** ({m['type']}): forum says `{m['forum']}`, payload says `{m['payload']}`"
        for m in mismatches
    ]
    return "> [!WARNING]\n" + "\n".join(lines)


def render_scale_alert(scale_check_output: str) -> str:
    flags = [
        line.strip()
        for line in scale_check_output.splitlines()
        if line.strip() and line.strip() not in ("no scale-bound flags",)
        and not line.startswith("no diff report was generated")
    ]
    if not flags:
        return "> [!NOTE]\n> No decimals-scale issues found."
    lines = [f"> 🔴 {line}" for line in flags]
    return "> [!CAUTION]\n" + "\n".join(lines)
