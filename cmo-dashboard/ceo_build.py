"""What build am I looking at?

The console is served from a copy of this directory under the profile dir, not
from the git checkout. That gap is invisible from the screen: a stale console and
a fresh one look identical. This module makes it visible.

Two independent facts, because they fail in different ways:

- `source_stamp()` reads the newest `*.py` beside this module. It answers "when
  were the files on the serving box last changed", which catches a deploy that
  never ran.
- `page_digest()` hashes the assembled document. It answers "is this byte-for-byte
  the page I expect", which catches a deploy that ran but landed a different build,
  or a cache serving something older than the files on disk.

Both render in the footer and travel back in the `X-CMO-Build` response header, so
the same value can be read off the screen or off `curl -I`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

#: Substituted after the document is assembled, so the digest can cover the whole
#: page except the digest itself.
PLACEHOLDER = "@@CMO_BUILD_STAMP@@"

__all__ = ["PLACEHOLDER", "source_stamp", "page_digest", "stamp_document", "build_header"]


def source_stamp(directory: Path | None = None) -> dict[str, str]:
    """The newest Python source the console runs on, and when it changed.

    Two directories, not one. The console imports `cmo_runtime` for the board, the
    decisions, the writer and the publisher — so a runtime-only deploy changes what
    the console *does* while leaving every file beside this module untouched.

    That is not academic. `deploy-dashboard` refuses to report success unless the
    served stamp moves, and with the stamp reading only this directory, a change
    landing entirely in `cmo_runtime` could never move it: the deploy reported
    failure having actually succeeded, which trains you to ignore the one check
    that exists to be believed.
    """
    root = Path(directory) if directory is not None else Path(__file__).resolve().parent
    newest_time = 0.0
    newest_name = ""
    count = 0
    candidates: list[Path] = []
    for folder, prefix in ((root, ""), (root.parent / "cmo_runtime", "cmo_runtime/")):
        try:
            candidates.extend(sorted(folder.glob("*.py")))
        except OSError:
            continue
    for path in candidates:
        try:
            modified = path.stat().st_mtime
        except OSError:
            continue
        count += 1
        if modified > newest_time:
            newest_time = modified
            # Name it the way the deploy script names it, so "which file moved"
            # reads the same in the header and in the deploy output.
            newest_name = (
                f"cmo_runtime/{path.name}" if path.parent.name == "cmo_runtime" else path.name
            )
    if not newest_name:
        return {"time": "unknown", "file": "none", "count": "0", "epoch": "0"}
    stamp = dt.datetime.fromtimestamp(newest_time)
    return {
        "time": stamp.strftime("%d %b %Y %H:%M"),
        "file": newest_name,
        "count": str(count),
        "epoch": str(int(newest_time)),
    }


def page_digest(document: str) -> str:
    """A short, stable fingerprint of the assembled page."""
    return hashlib.sha256(document.encode("utf-8")).hexdigest()[:12]


def build_header(document: str, directory: Path | None = None) -> str:
    """The one-line value carried in X-CMO-Build."""
    source = source_stamp(directory)
    return f"src={source['epoch']} file={source['file']} page={page_digest(document)}"


def stamp_document(document: str, directory: Path | None = None) -> tuple[str, str]:
    """Replace the placeholder with the rendered stamp; return (page, header).

    The digest is taken while the placeholder is still in place, so the value shown
    on screen is reproducible: hash the served page with its stamp text swapped back
    for the placeholder and the same digest comes out.
    """
    source = source_stamp(directory)
    digest = page_digest(document)
    stamped = (
        f"<span class=\"build-label\">build</span> "
        f"<span class=\"build-value\">{source['time']}</span>"
        f"<span class=\"build-sep\">·</span>"
        f"<span class=\"build-value\">{source['file']}</span>"
        f"<span class=\"build-sep\">·</span>"
        f"<span class=\"build-value\">page {digest}</span>"
    )
    header = f"src={source['epoch']} file={source['file']} page={digest}"
    return document.replace(PLACEHOLDER, stamped), header
