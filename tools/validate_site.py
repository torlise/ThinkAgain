from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(tag)


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text(encoding="utf-8"))

    refs = re.findall(r'src="([^"]+)"', html) + re.findall(r'href="([^"]+)"', html)
    missing = []
    for ref in refs:
        if ref.startswith(("#", "http", "data:")):
            continue
        if not (ROOT / ref).exists():
            missing.append(ref)

    parser = Parser()
    parser.feed(html)

    svg_bad = []
    for figure in sorted((ROOT / "assets").glob("figure-*.svg")):
        text = figure.read_text(encoding="utf-8")
        if "<svg" not in text or "data:image/jpeg;base64" not in text:
            svg_bad.append(figure.name)

    result = {
        "html_tags_seen": len(parser.tags),
        "missing_refs": missing,
        "sections": html.count('class="chapter-section'),
        "figures": html.count('<figure class="doc-figure"'),
        "tables": html.count("<table"),
        "callouts": html.count('<aside class="callout'),
        "asset_figures": len(list((ROOT / "assets").glob("figure-*.svg"))),
        "manifest_figures": len(manifest["figures"]),
        "has_mobile_media": "@media (max-width: 860px)" in css,
        "negative_letter_spacing": "letter-spacing: -" in css,
        "svg_bad": svg_bad,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    failures = []
    if missing:
        failures.append("missing_refs")
    if result["figures"] != 14 or result["asset_figures"] != 14:
        failures.append("figure_count")
    if result["sections"] != 9:
        failures.append("section_count")
    if result["negative_letter_spacing"]:
        failures.append("negative_letter_spacing")
    if svg_bad:
        failures.append("svg_bad")

    if failures:
        raise SystemExit(f"Validation failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
