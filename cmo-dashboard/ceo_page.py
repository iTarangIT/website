from __future__ import annotations

import ceo_build
from ceo_markup import MARKUP
from ceo_script import SCRIPT
from ceo_style import STYLE


def render_page(*, title: str = "iTarang CEO Console") -> bytes:
    """Assemble the console document and stamp it with its own build identity."""
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title><style>{STYLE}</style></head><body>{MARKUP}<script>{SCRIPT}</script></body></html>"
    )
    stamped, _header = ceo_build.stamp_document(document)
    return stamped.encode("utf-8")


def page_build_header(*, title: str = "iTarang CEO Console") -> str:
    """The X-CMO-Build value for the page render_page() would return."""
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title><style>{STYLE}</style></head><body>{MARKUP}<script>{SCRIPT}</script></body></html>"
    )
    return ceo_build.build_header(document)


def page_bytes() -> bytes:
    return render_page()
