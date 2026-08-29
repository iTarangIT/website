"""The one Markdown reader in this console.

Every surface that shows an article body goes through `render_markdown_fragment`:
the console Read tab, the `/ceo/artifact` document route, and the print/PDF sheet.
It exists in Python — not in the browser script — so that a test can render a real
artifact and assert on the HTML that comes out. The previous reader lived inside a
JavaScript string, which is why it shipped raw pipes and literal `**` for weeks
with every suite green.

Rules escape first and mark up second, so an artifact can never inject HTML.
"""

from __future__ import annotations

import html
import re
from typing import Any, Iterable, Sequence

from cmo_runtime import review_sections

__all__ = [
    "render_markdown_fragment",
    "render_article",
    "split_review_notes",
    "strip_front_matter",
    "split_source",
    "REVIEW_HEADINGS",
]

SLOT_LINE = re.compile(r"^\{\{image:([a-z0-9][a-z0-9_-]{0,40})(?:\|([^}]*))?\}\}$", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
RULE = re.compile(r"^(?:-[ \t]*){3,}$|^(?:\*[ \t]*){3,}$|^(?:_[ \t]*){3,}$")
UNORDERED = re.compile(r"^[-*+]\s+(.*)$")
ORDERED = re.compile(r"^(\d{1,3})[.)]\s+(.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
FENCE = re.compile(r"^(?:```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
ALIGNMENT_ROW = re.compile(r"^\|?\s*:?-{1,}:?\s*(?:\|\s*:?-{1,}:?\s*)*\|?$")

# Escaping runs before markup, so inline rules only ever see these entities.
CODE_SPAN = re.compile(r"`([^`]+)`")
BACKSLASH = re.compile(r"\\(&amp;|&lt;|&gt;|&quot;|&#39;|[!-/:-@\[-`{-~])")
IMAGE = re.compile(r"!\[([^\]\n]*)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)")
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)(?:\s+&quot;([^&]*)&quot;)?\)")
BOLD = re.compile(r"(?<![*\w])\*\*(?=\S)(.+?)(?<=\S)\*\*(?!\*)", re.S)
ITALIC_STAR = re.compile(r"(?<![*\w])\*(?=[^\s*])([^*]+?)(?<=\S)\*(?!\*)")
ITALIC_UNDER = re.compile(r"(?<![_\w])_(?=\S)([^_]+?)(?<=\S)_(?![_\w])")
BARE_URL = re.compile(r"(?<![\"'=(\w])(https?://[^\s<>()\[\]]+[^\s<>()\[\].,;:])")
SAFE_HREF = re.compile(r"^(?:https?://|mailto:|/|\#)", re.I)

#: Headings the writer uses to talk to its reviewers. They are review scaffolding,
#: not prose, so the reader files them under "Review notes" instead of inline.
#:
#: Defined in `cmo_runtime.review_sections` and imported here rather than restated,
#: because this list and the publisher's used to be two lists. They disagreed, and
#: the difference — `Decision bullets:` — was published to the website.
REVIEW_HEADINGS = review_sections.HEADING_PATTERNS


def _esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def strip_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` block off the body. Metadata never reaches the reader."""
    body = text.lstrip("﻿")
    if body.lstrip("\n").startswith("---"):
        body = body.lstrip("\n")
    else:
        return {}, text.lstrip("﻿")
    lines = body.split("\n")
    if lines[0].strip() != "---":
        return {}, body
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            metadata: dict[str, str] = {}
            for line in lines[1:index]:
                if ":" not in line or line.startswith((" ", "\t", "-")):
                    continue
                name, _, value = line.partition(":")
                key = name.strip().casefold().replace("-", "_")
                metadata[key] = value.strip().strip('"').strip("'")
            return metadata, "\n".join(lines[index + 1 :])
    return {}, body


def split_source(text: str) -> tuple[dict[str, str], str, str]:
    """The same split as `strip_front_matter`, keeping the block it throws away.

    The console's editor has to hand back the whole file, header included, or
    `check_edited_front_matter` refuses the save — so the browser needs the block
    as text, not as the parsed dict. Rebuilding it from `strip_front_matter`'s
    metadata cannot work: the parse lowercases keys, drops quotes and forgets the
    order, so a save would rewrite the header every time.

    The prefix is taken by length rather than re-matched, because every return path
    in `strip_front_matter` yields a suffix of the text it was given. So
    `front_matter + body == text` holds by construction — including the BOM and any
    blank lines above the block — and there is no second parser to drift from the
    first.
    """
    metadata, body = strip_front_matter(text)
    return metadata, text[: len(text) - len(body)], body


def _is_review_heading(title: str) -> bool:
    return review_sections.is_review_heading(title)


def split_review_notes(text: str) -> tuple[str, str]:
    """Return (prose, review notes) — the scaffolding sections lifted out in order."""
    lines = text.split("\n")
    prose: list[str] = []
    notes: list[str] = []
    target = prose
    capture_level = 0
    fenced = False
    for line in lines:
        if FENCE.match(line.strip()):
            fenced = not fenced
            target.append(line)
            continue
        heading = None if fenced else HEADING.match(line)
        if heading is not None:
            level = len(heading.group(1))
            if _is_review_heading(heading.group(2)):
                target = notes
                capture_level = level
                target.append(line)
                continue
            if target is notes and level <= capture_level:
                target = prose
        target.append(line)
    return "\n".join(prose).strip("\n"), "\n".join(notes).strip("\n")


def _href(raw: str) -> str:
    value = html.unescape(raw).strip()
    return value if SAFE_HREF.match(value) else ""


def _emphasis(text: str) -> str:
    text = BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = ITALIC_STAR.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    return ITALIC_UNDER.sub(lambda m: f"<em>{m.group(1)}</em>", text)


def _inline_markup(escaped: str, sealed: list[str]) -> str:
    """Inline markup over already-escaped text.

    Anything that must not be re-examined by a later rule — code, links, escaped
    punctuation — is replaced by a placeholder and put back at the end.
    """

    def seal(fragment: str) -> str:
        sealed.append(fragment)
        return f"\x00{len(sealed) - 1}\x00"

    text = CODE_SPAN.sub(lambda m: seal(f"<code>{m.group(1)}</code>"), escaped)
    text = BACKSLASH.sub(lambda m: seal(m.group(1)), text)
    # A remote image would be an external request from the console. The alt text
    # carries the meaning; the image itself does not load. Article diagrams come
    # through {{image:...}} slots, which this host serves itself.
    text = IMAGE.sub(
        lambda m: seal(
            f'<span class="image-omitted">{_emphasis(m.group(1))}</span>' if m.group(1).strip() else ""
        ),
        text,
    )

    def link(match: re.Match[str]) -> str:
        label = _emphasis(match.group(1))
        target = _href(match.group(2))
        if not target:
            # An unusable target still must not leave raw Markdown on the page.
            return seal(label)
        title = f' title="{match.group(3)}"' if match.group(3) else ""
        external = ' target="_blank" rel="noopener noreferrer"' if target.startswith("http") else ""
        return seal(f'<a href="{_esc(target)}"{title}{external}>{label}</a>')

    text = LINK.sub(link, text)
    text = BARE_URL.sub(
        lambda m: seal(
            f'<a href="{_esc(m.group(1))}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>'
        ),
        text,
    )
    return _emphasis(text)


def _inline(escaped: str) -> str:
    sealed: list[str] = []
    text = _inline_markup(escaped, sealed)
    # Sealed fragments can hold placeholders of their own, so resolve until settled.
    for _ in range(8):
        if "\x00" not in text:
            break
        text = re.sub(r"\x00(\d+)\x00", lambda m: sealed[int(m.group(1))], text)
    return text.replace("\x00", "")


def _cells(row: str) -> list[str]:
    body = row.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    parts = re.split(r"(?<!\\)\|", body)
    return [part.replace("\\|", "|").strip() for part in parts]


def _alignments(row: str) -> list[str]:
    output = []
    for cell in _cells(row):
        left, right = cell.startswith(":"), cell.endswith(":")
        output.append("center" if left and right else "right" if right else "left" if left else "")
    return output


def _slot_figure(slot: dict[str, Any]) -> str:
    """One caption per figure. The loading placeholder never repeats the caption."""
    identifier = _esc(str(slot.get("id", "")))
    caption = _inline(_esc(str(slot.get("caption", "")).strip()))
    caption_id = f"figcap-{identifier}"
    if slot.get("bound"):
        frame = (
            f'<div class="figure-frame" data-image-url="{_esc(str(slot.get("url", "")))}">'
            '<span class="figure-status">Loading diagram…</span></div>'
        )
        classes = "figure"
    else:
        frame = (
            '<div class="figure-frame is-empty"><strong>Image slot</strong>'
            f"<span>{identifier}</span>"
            "<span>No image is bound yet. Bind one from the Files tab.</span></div>"
        )
        classes = "figure is-unbound"
    return (
        f'<figure class="{classes}" aria-labelledby="{caption_id}">{frame}'
        f'<figcaption id="{caption_id}">{caption}</figcaption></figure>'
    )


def _table(header: str, alignment: str, body: Sequence[str]) -> str:
    aligns = _alignments(alignment)

    def row(cells: list[str], tag: str) -> str:
        out = []
        for index, cell in enumerate(cells):
            align = aligns[index] if index < len(aligns) else ""
            attribute = f' class="align-{align}"' if align else ""
            scope = ' scope="col"' if tag == "th" else ""
            out.append(f"<{tag}{scope}{attribute}>{_inline(_esc(cell))}</{tag}>")
        return "<tr>" + "".join(out) + "</tr>"

    head = row(_cells(header), "th")
    rows = "".join(row(_cells(line), "td") for line in body)
    return (
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Table">'
        f"<table class=\"prose-table\"><thead>{head}</thead><tbody>{rows}</tbody></table></div>"
    )


def render_markdown_fragment(
    text: str,
    *,
    slots: Iterable[dict[str, Any]] | None = None,
    strip_metadata: bool = True,
) -> str:
    """Render the artifact Markdown subset to an HTML fragment (no document wrapper).

    Handles front matter, headings, paragraphs, bullet and ordered lists, block
    quotes, horizontal rules, fenced code, tables, image slots and inline
    emphasis, code, and links. Escaping happens before every rule.
    """
    if strip_metadata:
        _metadata, text = strip_front_matter(text or "")
    slot_map = {str(slot.get("id", "")).casefold(): slot for slot in (slots or [])}
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    index = 0
    total = len(lines)

    def paragraph(buffer: list[str]) -> None:
        if buffer:
            joined = "<br>".join(_inline(_esc(item)) for item in buffer)
            if joined.strip():
                out.append(f"<p>{joined}</p>")
            buffer.clear()

    buffer: list[str] = []
    while index < total:
        raw = lines[index]
        line = raw.strip()

        fence = FENCE.match(line)
        if fence:
            paragraph(buffer)
            index += 1
            code: list[str] = []
            while index < total and not FENCE.match(lines[index].strip()):
                code.append(lines[index])
                index += 1
            index += 1
            language = f' class="language-{_esc(fence.group(1))}"' if fence.group(1) else ""
            out.append(f"<pre><code{language}>{_esc(chr(10).join(code))}</code></pre>")
            continue

        if not line:
            paragraph(buffer)
            index += 1
            continue

        slot_marker = SLOT_LINE.match(line)
        if slot_marker:
            paragraph(buffer)
            key = slot_marker.group(1).casefold()
            slot = slot_map.get(key)
            if slot is not None:
                out.append(_slot_figure(slot))
            else:
                caption = (slot_marker.group(2) or key.replace("-", " ")).strip()
                out.append(_slot_figure({"id": key, "caption": caption, "bound": False}))
            index += 1
            continue

        heading = HEADING.match(raw.rstrip())
        if heading:
            paragraph(buffer)
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(_esc(heading.group(2)))}</h{level}>")
            index += 1
            continue

        if RULE.match(line):
            paragraph(buffer)
            out.append("<hr>")
            index += 1
            continue

        if (
            "|" in line
            and index + 1 < total
            and ALIGNMENT_ROW.match(lines[index + 1].strip())
            and len(_cells(lines[index + 1])) == len(_cells(line))
        ):
            paragraph(buffer)
            header, alignment = line, lines[index + 1].strip()
            index += 2
            body: list[str] = []
            while index < total and "|" in lines[index] and lines[index].strip():
                body.append(lines[index].strip())
                index += 1
            out.append(_table(header, alignment, body))
            continue

        quote = QUOTE.match(line)
        if quote:
            paragraph(buffer)
            quoted: list[str] = []
            while index < total and QUOTE.match(lines[index].strip()):
                quoted.append(QUOTE.match(lines[index].strip()).group(1))
                index += 1
            out.append("<blockquote>" + render_markdown_fragment("\n".join(quoted), strip_metadata=False) + "</blockquote>")
            continue

        bullet = UNORDERED.match(line)
        number = ORDERED.match(line)
        if bullet or number:
            paragraph(buffer)
            ordered = number is not None
            pattern = ORDERED if ordered else UNORDERED
            items: list[str] = []
            while index < total:
                candidate = lines[index].strip()
                match = pattern.match(candidate)
                if match:
                    items.append(match.group(2) if ordered else match.group(1))
                    index += 1
                    continue
                # A wrapped continuation line belongs to the item above it.
                if candidate and items and lines[index].startswith((" ", "\t")):
                    items[-1] += " " + candidate
                    index += 1
                    continue
                break
            tag = "ol" if ordered else "ul"
            start = ""
            if ordered:
                first = ORDERED.match(line)
                if first and first.group(1) != "1":
                    start = f' start="{int(first.group(1))}"'
            rendered = "".join(f"<li>{_inline(_esc(item))}</li>" for item in items)
            out.append(f"<{tag}{start}>{rendered}</{tag}>")
            continue

        buffer.append(line)
        index += 1

    paragraph(buffer)
    return "".join(out)


def cover_strip(cover: dict[str, Any] | None) -> str:
    """The picture that will go on the blog card, shown above the article.

    Gate 1 approves what the reader is looking at. The cover never appears in the
    prose, so without this the one image most people will actually see was the one
    image the approver could not.
    """
    if not cover:
        return ""
    if not cover.get("bound"):
        return (
            '<div class="cover-strip is-empty"><strong>Cover image</strong>'
            "<span>None bound. Generate or upload one from the Files tab.</span></div>"
        )
    # The frame is the inner element, as it is for a body slot: hydration replaces
    # the frame's children with the loaded picture, so a caption inside it would be
    # thrown away the moment the image arrived.
    return (
        '<figure class="figure cover-strip"><div class="figure-frame" data-image-url="'
        + _esc(str(cover.get("url", "")))
        + '"><span class="figure-status">Loading cover…</span></div>'
        "<figcaption>Cover image — blog card and social preview</figcaption></figure>"
    )


def render_article(text: str, slots: Iterable[dict[str, Any]] | None = None,
                   cover: dict[str, Any] | None = None) -> dict[str, Any]:
    """Render one artifact into prose HTML plus its collapsed review notes."""
    metadata, body = strip_front_matter(text or "")
    prose, notes = split_review_notes(body)
    slot_list = list(slots or [])
    note_titles = [
        re.sub(r"\s+", " ", match.group(2)).strip().strip(":")
        for match in (HEADING.match(line) for line in notes.split("\n"))
        if match is not None and _is_review_heading(match.group(2))
    ]
    return {
        "metadata": metadata,
        "html": cover_strip(cover)
        + render_markdown_fragment(prose, slots=slot_list, strip_metadata=False),
        "review_notes_html": render_markdown_fragment(notes, slots=slot_list, strip_metadata=False),
        "review_note_titles": note_titles,
        "prose_markdown": prose,
    }
