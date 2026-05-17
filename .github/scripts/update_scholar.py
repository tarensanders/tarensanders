#!/usr/bin/env python3
"""Refresh Google Scholar metric badges in README.md.

Runs daily from .github/workflows/scholar.yml. On any failure (Scholar
rate-limits the bots aggressively) the script exits 0 without touching the
README, so the existing badges stay visible.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCHOLAR_ID = "8KNzhS4AAAAJ"
README = Path(__file__).resolve().parents[2] / "README.md"
START = "<!-- SCHOLAR:START -->"
END = "<!-- SCHOLAR:END -->"
COLOR = "1F3A93"


def shield(label: str, value: int) -> str:
    label_safe = label.replace("-", "--").replace(" ", "%20")
    return (
        f"![{label}](https://img.shields.io/badge/"
        f"{label_safe}-{value}-{COLOR})"
    )


def fetch_metrics() -> dict[str, int]:
    from scholarly import scholarly

    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(
        author, sections=["basics", "indices", "publications"]
    )
    return {
        "Publications": len(author.get("publications", [])),
        "Citations": int(author.get("citedby", 0)),
        "h-index": int(author.get("hindex", 0)),
        "i10-index": int(author.get("i10index", 0)),
    }


def main() -> int:
    try:
        metrics = fetch_metrics()
    except Exception as exc:  # noqa: BLE001
        print(f"Scholar fetch failed; leaving README untouched: {exc}",
              file=sys.stderr)
        return 0

    if not metrics or not any(metrics.values()):
        print("No metrics returned; leaving README untouched.", file=sys.stderr)
        return 0

    badges = " ".join(shield(k, v) for k, v in metrics.items())
    text = README.read_text()
    block = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new_text, count = block.subn(f"{START}\n{badges}\n{END}", text)
    if count != 1:
        print("SCHOLAR markers not found in README.", file=sys.stderr)
        return 1
    if new_text == text:
        print("No changes.")
        return 0
    README.write_text(new_text)
    print("README updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
