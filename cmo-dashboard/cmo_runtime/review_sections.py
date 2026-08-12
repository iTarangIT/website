"""What the writer says to its reviewers, and never to a reader.

The writer produces two things in one file: an article, and notes about the
article — the decision bullets a reviewer signs off, the claims a human has to
verify, the internal links being proposed, the call to action explicitly marked
as not for publication, and when the sources were accessed. All of it is
addressed to whoever reviews the piece.

Two consumers have to agree about which is which. The console files these under
"Review notes" so Sanchit reads the article without them; the publisher must drop
them entirely, because a page carrying "Non-published call to action for review"
has published exactly the thing that sentence says is not published.

They did not agree. The console matched five heading patterns; the publisher
matched three different ones and missed `Decision bullets:` altogether, so it went
to the website. This module is the single definition, imported by both, with a
test that fails if either stops using it. The same drift between two Markdown
renderers is what put raw asterisks on a page once already.

Scaffolding arrives two ways, so this recognises both:

- as its own `##` heading, which is what the contract asks for;
- as a labelled sentence inside a closing paragraph, which is what the writer
  actually did on TASK-084 — `... battery passport concept. Claims requiring
  human verification before publication: ...`. Nothing was stripping those,
  in either consumer.
"""

from __future__ import annotations

import re

__all__ = [
    "REVIEW_LABELS",
    "HEADING_PATTERNS",
    "is_review_heading",
    "split_inline_scaffolding",
    "strip_scaffolding",
]

#: Every label the writer uses to address a reviewer. Matched at the start of a
#: heading, or at the start of a sentence inside a paragraph.
REVIEW_LABELS: tuple[str, ...] = (
    "decision bullets",
    "claims requiring human verification",
    "proposed internal links",
    "non-published call to action",
    "source notes",
    "source-backed outline",
    "review notes",
)

#: The heading form, kept as compiled patterns because `ceo_reader` has always
#: exported them that way and other code reads that name.
HEADING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(rf"^{re.escape(label)}\b") for label in REVIEW_LABELS
)

#: The inline form. A label may be followed by a few qualifying words before its
#: colon — "Claims requiring human verification *before publication*:" — so a
#: short run of non-colon characters is allowed between the two.
_INLINE = re.compile(
    r"(?is)(?:(?<=^)|(?<=[.!?]\s)|(?<=[.!?]\s\s))"
    r"(?:" + "|".join(re.escape(label) for label in REVIEW_LABELS) + r")"
    r"[^:\n]{0,40}:"
)


def _normalise(title: str) -> str:
    value = re.sub(r"\s+", " ", title).strip().strip(":").casefold()
    return value.replace("—", "-").replace("–", "-")


def is_review_heading(title: str) -> bool:
    """Whether a heading introduces review scaffolding rather than prose."""
    normalised = _normalise(title)
    return any(pattern.search(normalised) for pattern in HEADING_PATTERNS)


def split_inline_scaffolding(paragraph: str) -> tuple[str, str]:
    """Split one paragraph into (prose, scaffolding) at the first review label.

    Returns the paragraph unchanged as prose when it carries none. A paragraph
    that is scaffolding from its first character comes back with empty prose,
    which is how a whole trailing paragraph of notes disappears from the page.
    """
    match = _INLINE.search(paragraph)
    if match is None:
        return paragraph, ""
    return paragraph[: match.start()].rstrip(), paragraph[match.start():].strip()


def strip_scaffolding(body: str) -> str:
    """Everything a reader should see, and nothing addressed to a reviewer.

    Whole sections go when their heading is a review heading — down to the next
    heading of the same level or shallower, so a `###` inside a review section
    goes with it. Then any labelled sentence surviving inside a paragraph is cut,
    along with everything after it in that paragraph.
    """
    kept: list[str] = []
    fenced = False
    omit_at: int | None = None
    for line in body.splitlines():
        if re.match(r"^(?:```|~~~)", line.strip()):
            fenced = not fenced
            kept.append(line)
            continue
        heading = None if fenced else re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if heading is not None:
            level = len(heading.group(1))
            if is_review_heading(heading.group(2)):
                omit_at = level
                continue
            if omit_at is not None and level <= omit_at:
                omit_at = None
        if omit_at is not None:
            continue
        if fenced:
            kept.append(line)
            continue
        prose, _notes = split_inline_scaffolding(line)
        if prose:
            kept.append(prose)
        elif not line.strip():
            kept.append(line)
    # A dropped paragraph can leave three blank lines where there were two.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip() + "\n"
