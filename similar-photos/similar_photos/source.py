"""Image-source / forum hosting lookup (exact frame only — no person ID)."""

from __future__ import annotations

import hashlib
import json
import webbrowser
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote


@dataclass
class SourceHit:
    url: str
    site: str
    note: str = ""


@dataclass
class SourceReport:
    image: str
    sha256: str
    hits: list[SourceHit] = field(default_factory=list)
    browser_helpers: list[dict[str, str]] = field(default_factory=list)
    note: str = (
        "Só lista URLs confirmadas que hospedam este arquivo/quadro. "
        "Sem hits inventados. Engines muitas vezes bloqueiam automação — use os helpers."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def helper_urls(path: Path) -> list[dict[str, str]]:
    """URLs to open manually for reverse-image SOURCE search."""
    p = path.resolve()
    # TinEye and Yandex expect upload UI; we open the landing pages.
    return [
        {
            "name": "TinEye",
            "url": "https://tineye.com/",
            "how": f"Upload {p.name} and copy pages that host this exact photo.",
        },
        {
            "name": "Yandex Images",
            "url": "https://yandex.com/images/",
            "how": "Camera icon → upload file → open Sites tab for hosting pages.",
        },
        {
            "name": "Google Images",
            "url": "https://images.google.com/",
            "how": "Camera → upload image → filter Exact matches if available.",
        },
        {
            "name": "Bing Visual Search",
            "url": "https://www.bing.com/visualsearch",
            "how": "Upload the same file and open matching page results only.",
        },
    ]


def search_sources(path: Path, open_browsers: bool = False) -> SourceReport:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    report = SourceReport(image=str(path), sha256=_sha256(path), browser_helpers=helper_urls(path))
    # Best-effort: no fabricated hits. Optional future: wire paid reverse-image APIs.
    # Attempt a lightweight web hint search by filename only when distinctive.
    name = path.name
    if len(name) > 20 and name.lower() not in {"image.jpg", "photo.jpg", "img.png"}:
        q = quote(f'"{name}"')
        report.browser_helpers.append(
            {
                "name": "DuckDuckGo filename",
                "url": f"https://duckduckgo.com/?q={q}",
                "how": "Filename dork — only useful if the original filename is unique.",
            }
        )
    if open_browsers:
        for helper in report.browser_helpers[:3]:
            webbrowser.open(helper["url"])
    return report


def report_json(report: SourceReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
