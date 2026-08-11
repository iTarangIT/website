from __future__ import annotations

import importlib
from pathlib import Path
from typing import Callable, Iterator


def iter_page_builders() -> Iterator[tuple[str, Callable[[], bytes]]]:
    """Enumerate every dashboard module that follows the *_page.py builder contract."""
    dashboard_dir = Path(__file__).resolve().parent
    for path in sorted(dashboard_dir.glob("*_page.py")):
        # A suite that happens to end in _page.py is a test, not a page builder.
        if path.name.startswith("test_"):
            continue
        module = importlib.import_module(path.stem)
        builder = getattr(module, "page_bytes", None)
        if not callable(builder):
            raise TypeError(f"{path.name} must expose page_bytes()")
        yield path.stem, builder
