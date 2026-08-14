from __future__ import annotations

from tech_markup import MARKUP
from tech_script import SCRIPT
from tech_style import STYLE


def render_page(*, title: str = "iTarang Technical Console") -> bytes:
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title><style>{STYLE}</style></head><body>'
        f'{MARKUP}<script>{SCRIPT}</script></body></html>'
    )
    return document.encode("utf-8")


def page_bytes() -> bytes:
    return render_page()
