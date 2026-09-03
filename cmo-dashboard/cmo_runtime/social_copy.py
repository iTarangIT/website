"""Turn one published article into copy that belongs on each platform.

The same paragraph pasted to LinkedIn, X and Instagram reads as filler on all
three. A LinkedIn audience wants the professional claim and the number behind
it; X wants a thread that earns the next tap; Instagram wants a caption written
to sit under a picture. These are different pieces of writing, not one piece
reformatted, and this module produces three.

Two producers, and the console always says which one it used:

* **writer** — one tool-restricted Hermes call, given the article and
  `social.skill`, returning the three drafts in delimited sections. This is the
  good path and the default.
* **composed** — a deterministic draft assembled from the article's own front
  matter and opening sentences. It is not a silent fallback dressed up as
  authorship: `SocialDraft.source` says `composed`, the console prints it, and a
  human edits before anything is sent.

Every draft is bounded by the destination's real limit before it leaves here, so
a rejection surfaces as an editable refusal in the console rather than as a
Buffer 400 after the human has already pressed send.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

#: Hard ceilings the networks enforce. A draft over one of these is refused
#: here, where the reason can be shown beside the text a human can shorten.
from cmo_runtime import social_tags

PLATFORM_LIMITS = {"linkedin": 3000, "x": 280, "instagram": 2200}

#: What a thread may run to. Longer than this is a blog post, which we have.
MAX_THREAD_ITEMS = 8

#: The platforms this module writes for, in console display order.
PLATFORMS = ("linkedin", "x", "instagram")

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class SocialCopyRefused(RuntimeError):
    """The copy could not be produced, in words an operator can act on."""


@dataclass(frozen=True)
class SocialDraft:
    """One platform's copy, ready for a human to read and edit."""

    platform: str
    body: str
    link: str = ""
    thread: tuple[str, ...] = ()
    image_alt: str = ""
    source: str = "composed"

    @property
    def characters(self) -> int:
        """The length that will actually be checked against the platform limit."""
        return len(self.thread[0]) if self.thread else len(self.body)

    def as_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "body": self.body,
            "link": self.link,
            "thread": list(self.thread),
            "image_alt": self.image_alt,
            "source": self.source,
            "characters": self.characters,
            "limit": PLATFORM_LIMITS[self.platform],
        }


@dataclass(frozen=True)
class ArticleSummary:
    """The parts of a published article the copy is written from."""

    title: str
    meta_description: str
    slug: str
    category: str
    audience: str
    url: str
    body: str
    keywords: tuple[str, ...] = ()
    cover_alt: str = ""
    sentences: tuple[str, ...] = field(default=())


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def _tag_line(summary: ArticleSummary, platform: str) -> str:
    """The curated industry tags for this article on this platform.

    Lives in `social_tags` rather than here because the tags are editorial
    content — a reviewed list of rooms real practitioners are in — and not a
    string transformation of the keywords. See that module for why the old
    slugify-the-keywords approach produced `#evfinance` and, on a card with no
    keywords, produced nothing at all.
    """
    return social_tags.tag_line(
        platform, category=summary.category, keywords=summary.keywords
    )


def with_tags(
    drafts: Mapping[str, SocialDraft], summary: ArticleSummary
) -> dict[str, SocialDraft]:
    """Append the curated tags to every draft, whoever wrote the prose.

    Applied after the producer rather than inside it, so the writer and the
    fallback composer carry the same reviewed tags. A model asked to pick its own
    would pick different ones every regeneration, and none of them assertable.

    Tags are dropped one at a time until the post fits its limit, and dropped
    entirely rather than overflowing it: a tag is worth less than the sentence it
    would push off the end.
    """
    tagged: dict[str, SocialDraft] = {}
    for platform, draft in drafts.items():
        tags = social_tags.tags_for_platform(
            platform, category=summary.category, keywords=summary.keywords
        )
        if platform == "x":
            # The tags ride the last item, which is the one carrying the link.
            # Anywhere earlier and they interrupt the argument mid-thread.
            items = list(draft.thread) or [draft.body]
            items[-1] = _append_tags(items[-1], tags, PLATFORM_LIMITS[platform])
            tagged[platform] = replace(
                draft, thread=tuple(items), body=items[0] if draft.thread else items[0]
            )
            continue
        tagged[platform] = replace(
            draft, body=_append_tags(draft.body, tags, PLATFORM_LIMITS[platform])
        )
    return tagged


def _append_tags(text: str, tags: Sequence[str], limit: int) -> str:
    """`text` with as many of `tags` as fit under `limit`, or `text` unchanged."""
    body = text.rstrip()
    for count in range(len(tags), 0, -1):
        candidate = f"{body}\n\n{' '.join(tags[:count])}"
        if len(candidate) <= limit:
            return candidate
    return body


def summarise_article(
    markdown: str,
    *,
    url: str,
    keywords: Sequence[str] = (),
    cover_alt: str = "",
) -> ArticleSummary:
    """Read a published article into the handful of parts the copy needs.

    Deliberately lenient about the header: this runs after the publisher has
    already validated it, and a strict re-parse here would only turn a published
    article into a refusal at the point it is being promoted.
    """
    from cmo_runtime.content_flow import front_matter_fields, split_front_matter_text

    fields = front_matter_fields(markdown) or {}
    front, body = split_front_matter_text(markdown)
    if not front and body.lstrip().startswith("---"):
        # `split_front_matter_text` needs a body after the closing `---` and
        # returns the whole file as prose when there is none. Left alone, the
        # header then walks into a LinkedIn post as `--- title: A ---`. Strip it
        # here rather than publish it.
        parts = body.lstrip().split("---", 2)
        body = parts[2] if len(parts) == 3 else ""
    prose = "\n".join(
        line for line in body.splitlines() if line.strip() and not line.lstrip().startswith(("#", "!", "|", ">"))
    )
    sentences = tuple(part.strip() for part in _SENTENCE.split(_clean(prose)) if part.strip())
    return ArticleSummary(
        title=_clean(fields.get("title")),
        meta_description=_clean(fields.get("meta_description")),
        slug=_clean(fields.get("slug")),
        category=_clean(fields.get("category")),
        audience=_clean(fields.get("audience")),
        url=url,
        body=body,
        keywords=tuple(_clean(word) for word in keywords if _clean(word)),
        cover_alt=_clean(cover_alt),
        sentences=sentences[:12],
    )


def _fit(text: str, limit: int) -> str:
    """Trim to a limit on a sentence boundary, then a word boundary, never mid-word."""
    text = _clean(text)
    if len(text) <= limit:
        return text
    kept: list[str] = []
    for sentence in _SENTENCE.split(text):
        candidate = " ".join((*kept, sentence)).strip()
        if len(candidate) > limit:
            break
        kept.append(sentence)
    if kept:
        return " ".join(kept).strip()
    return text[: max(0, limit - 1)].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def compose(summary: ArticleSummary) -> dict[str, SocialDraft]:
    """Build one draft per platform from the article itself.

    Each is shaped for its destination rather than truncated to fit it:

    * **LinkedIn** — the claim, then the two sentences that support it, then the
      link. The audience line from the front matter opens it, because "For fleet
      operators:" is the whole reason a professional reader stops.
    * **X** — a thread. One sentence per item so each can stand alone in a
      timeline, the link on the last, capped at `MAX_THREAD_ITEMS`.
    * **Instagram** — a caption written to sit under the cover, ending in the
      link-in-bio line, because Instagram captions do not carry live links.
    """
    lead = summary.meta_description or (summary.sentences[0] if summary.sentences else "")
    if not lead:
        raise SocialCopyRefused("The article has neither a meta description nor a first sentence.")

    support = " ".join(summary.sentences[1:3])
    audience = f"For {summary.audience}: " if summary.audience else ""

    linkedin_body = _fit(
        f"{audience}{summary.title}\n\n{lead}"
        + (f"\n\n{support}" if support else "")
        + f"\n\nRead the full piece: {summary.url}",
        PLATFORM_LIMITS["linkedin"],
    )

    items: list[str] = [_fit(f"{summary.title}\n\n{lead}", PLATFORM_LIMITS["x"])]
    for sentence in summary.sentences[1:]:
        if len(items) >= MAX_THREAD_ITEMS - 1:
            break
        if len(sentence) <= PLATFORM_LIMITS["x"] - 4:
            items.append(sentence)
    items.append(_fit(f"Full article: {summary.url}", PLATFORM_LIMITS["x"]))

    instagram_body = _fit(
        f"{summary.title}\n\n{lead}\n\nFull article linked in bio.",
        PLATFORM_LIMITS["instagram"],
    )

    return {
        "linkedin": SocialDraft(
            platform="linkedin", body=linkedin_body, link=summary.url, source="composed"
        ),
        "x": SocialDraft(
            platform="x",
            body=items[0],
            link=summary.url,
            thread=tuple(items),
            source="composed",
        ),
        "instagram": SocialDraft(
            platform="instagram",
            body=instagram_body,
            link=summary.url,
            image_alt=summary.cover_alt or summary.title,
            source="composed",
        ),
    }


def validate(drafts: Mapping[str, SocialDraft]) -> None:
    """Refuse anything a network would reject, naming the platform and the overrun."""
    for platform, draft in drafts.items():
        limit = PLATFORM_LIMITS.get(platform)
        if limit is None:
            raise SocialCopyRefused(f"{platform} is not a platform this console posts to.")
        if not draft.body.strip():
            raise SocialCopyRefused(f"The {platform} draft is empty.")
        if len(draft.body) > limit:
            raise SocialCopyRefused(
                f"The {platform} draft is {len(draft.body)} characters against a {limit} limit."
            )
        for index, item in enumerate(draft.thread, start=1):
            if len(item) > limit:
                raise SocialCopyRefused(
                    f"Thread item {index} is {len(item)} characters against a {limit} limit."
                )
        if len(draft.thread) > MAX_THREAD_ITEMS:
            raise SocialCopyRefused(
                f"The thread runs to {len(draft.thread)} posts against a {MAX_THREAD_ITEMS} cap."
            )


_PROMPT = """\
You are writing social copy to promote one already-published iTarang article.

Follow this skill exactly:
{skill}

The article, as published:
{article}

It is live at: {url}

Write three separate pieces. Do not paste the same text into more than one.

LINKEDIN: a professional summary for {audience}. Open with the claim, support it
with one concrete number or fact taken from the article, close with the link.
Maximum {linkedin_limit} characters. No emoji.

X_THREAD: a JSON array of 2 to {thread_cap} strings, each at most {x_limit}
characters. The first earns the second. The last carries the link.

INSTAGRAM: a caption to sit under the cover image. Maximum {instagram_limit}
characters. Instagram captions have no live link, so say the article is linked
in bio rather than pasting a URL.

Write NO hashtags anywhere, on any of the three. The console appends a reviewed
set afterwards; tags you invent here would be dropped, and would cost you
characters that are checked against the limits above.

Invent nothing that is not in the article. Reply with exactly these sections:

<<<BEGIN_LINKEDIN>>>
...
<<<END_LINKEDIN>>>
<<<BEGIN_X_THREAD>>>
["...", "..."]
<<<END_X_THREAD>>>
<<<BEGIN_INSTAGRAM>>>
...
<<<END_INSTAGRAM>>>
"""


class HermesSocialWriter:
    """One tool-restricted Hermes call, following `HermesContentWriter`'s contract."""

    def __init__(self, root: str | Path, *, command: str | Path | None = None) -> None:
        self.root = Path(root)
        self.command = str(command or os.getenv("HERMES_BIN", "/opt/hermes/.venv/bin/hermes"))

    @staticmethod
    def _section(output: str, name: str) -> str:
        match = re.search(
            rf"(?s)<<<BEGIN_{re.escape(name)}>>>\s*(.*?)\s*<<<END_{re.escape(name)}>>>", output
        )
        if match is None:
            raise SocialCopyRefused(f"The writer response is missing the {name} section.")
        return match.group(1).strip()

    def write(self, *, task_id: str, summary: ArticleSummary, skill_text: str) -> dict[str, SocialDraft]:
        prompt = _PROMPT.format(
            skill=skill_text,
            article=summary.body[:20000],
            url=summary.url,
            audience=summary.audience or "the article's audience",
            linkedin_limit=PLATFORM_LIMITS["linkedin"],
            x_limit=PLATFORM_LIMITS["x"],
            instagram_limit=PLATFORM_LIMITS["instagram"],
            thread_cap=MAX_THREAD_ITEMS,
        )
        usage_dir = self.root / "state" / "social-usage"
        usage_dir.mkdir(parents=True, exist_ok=True)
        usage_path = usage_dir / f"{task_id}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')}.json"
        completed = subprocess.run(
            [self.command, "--ignore-rules", "-t", "web", "--usage-file", str(usage_path), "-z", prompt],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if completed.returncode != 0:
            detail = _clean(completed.stderr or completed.stdout or "no error text")
            raise SocialCopyRefused(f"The social writer exited {completed.returncode}: {detail[:300]}")

        try:
            items = json.loads(self._section(completed.stdout, "X_THREAD"))
        except json.JSONDecodeError as exc:
            raise SocialCopyRefused("The writer's X thread was not a JSON array.") from exc
        if not isinstance(items, list) or not items:
            raise SocialCopyRefused("The writer's X thread was empty.")
        thread = tuple(_clean(item) for item in items if _clean(item))

        drafts = {
            "linkedin": SocialDraft(
                platform="linkedin",
                body=self._section(completed.stdout, "LINKEDIN"),
                link=summary.url,
                source="writer",
            ),
            "x": SocialDraft(
                platform="x", body=thread[0], link=summary.url, thread=thread, source="writer"
            ),
            "instagram": SocialDraft(
                platform="instagram",
                body=self._section(completed.stdout, "INSTAGRAM"),
                link=summary.url,
                image_alt=summary.cover_alt or summary.title,
                source="writer",
            ),
        }
        validate(drafts)
        return drafts


def drafts_for(
    *,
    task_id: str,
    summary: ArticleSummary,
    skill_text: str = "",
    writer: Any | None = None,
) -> dict[str, SocialDraft]:
    """The three drafts, from the writer where it can produce them.

    A writer failure is not fatal — it costs the drafts their authorship, not
    their existence — but it is never hidden: the returned drafts say `composed`
    and the console renders that beside the copy.
    """
    if writer is not None and skill_text.strip():
        try:
            written = with_tags(writer.write(
                task_id=task_id, summary=summary, skill_text=skill_text
            ), summary)
            # Re-checked after tagging: the writer's copy was validated against
            # the limit before the tags were on it.
            validate(written)
            return written
        except SocialCopyRefused:
            pass
        except (OSError, subprocess.SubprocessError):
            pass
    drafts = with_tags(compose(summary), summary)
    validate(drafts)
    return drafts
