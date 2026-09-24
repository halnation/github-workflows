"""Sanitizes untrusted AI/model markdown before it is posted as a GitHub PR
or issue comment, so it can be rendered as real markdown (tables included)
instead of dumped inside a ```text fence. Shared by ai-comment.yml's review
comment and proposal-checks.yml's advisory comment -- one implementation,
not two copies of the same rules in YAML.

Rules (in order):
1. Strip raw HTML tags and HTML comments. (Our own dedup marker is added by
   the caller AFTER sanitizing, never sanitized itself.)
2. Drop markdown images (`![alt](url)`) entirely -- alt text only, no image.
3. Neutralize `@mentions` with a zero-width space so they don't ping anyone.
4. Neutralize `#123`-style references with a zero-width space. The model's
   output is never a deliberate same-repo issue/PR reference (it is
   analyzing forum/proposal content, not this repo's issues), and whether a
   bare `#123` would resolve inside or outside the current repo cannot be
   determined from the text alone, so every one is neutralized.
5. Markdown links (`[text](url)`) whose host is not in ALLOWED_LINK_HOSTS
   are rewritten to plain `text` (the URL is dropped, not just hidden).
6. Truncate to max_len characters.
"""
import re
from urllib.parse import urlparse

ALLOWED_LINK_HOSTS = {
    "github.com",
    "governance.aave.com",
    "snapshot.org",
    "app.aave.com",
    "etherscan.io",
    # other chain explorers used across our proposal repos
    "arbiscan.io",
    "basescan.org",
    "snowtrace.io",
    "polygonscan.com",
    "gnosisscan.io",
    "bscscan.com",
    "lineascan.build",
    "optimistic.etherscan.io",
    "sonicscan.org",
    "zkevm.polygonscan.com",
}

_HTML_TAG_RE = re.compile(r"<!--.*?-->|<[^>]+>", re.DOTALL)
_ALERT_SYNTAX_RE = re.compile(r"\[!(\w+)\]")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MENTION_RE = re.compile(r"@(?=\w)")
_ISSUE_REF_RE = re.compile(r"#(?=\d)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")

ZERO_WIDTH_SPACE = "​"


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text)


def _drop_images(text: str) -> str:
    return _IMAGE_RE.sub("", text)


def _neutralize_mentions(text: str) -> str:
    return _MENTION_RE.sub("@" + ZERO_WIDTH_SPACE, text)


def _neutralize_issue_refs(text: str) -> str:
    return _ISSUE_REF_RE.sub("#" + ZERO_WIDTH_SPACE, text)


def _neutralize_alert_syntax(text: str) -> str:
    # GitHub renders `> [!NOTE]` / `[!WARNING]` / `[!CAUTION]` (etc.) as
    # colored alert blocks. Only OUR code (advisory_render.py) is allowed to
    # emit those, built from parsed, structured data -- never from raw model
    # text, or the model could paint its own output red/orange at will.
    return _ALERT_SYNTAX_RE.sub(lambda m: "[" + ZERO_WIDTH_SPACE + "!" + m.group(1) + "]", text)


def _delink_disallowed_hosts(text: str) -> str:
    def repl(m):
        link_text, url = m.group(1), m.group(2)
        host = urlparse(url).hostname or ""
        host = host.lower()
        if host in ALLOWED_LINK_HOSTS or any(
            host.endswith("." + allowed) for allowed in ALLOWED_LINK_HOSTS
        ):
            return m.group(0)
        return link_text or url

    return _LINK_RE.sub(repl, text)


def sanitize_markdown(text: str, max_len: int = 20000) -> str:
    text = _strip_html(text)
    text = _drop_images(text)
    text = _neutralize_mentions(text)
    text = _neutralize_issue_refs(text)
    text = _neutralize_alert_syntax(text)
    text = _delink_disallowed_hosts(text)
    return text[:max_len]


if __name__ == "__main__":
    import sys

    in_path, max_len = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    with open(in_path, encoding="utf-8") as f:
        raw = f.read()
    sys.stdout.write(sanitize_markdown(raw, max_len))
