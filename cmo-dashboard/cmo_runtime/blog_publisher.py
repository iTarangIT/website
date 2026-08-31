from __future__ import annotations

import argparse
import html
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Mapping

from cmo_runtime.agent_runtime import BoardStore
from cmo_runtime.review_sections import strip_scaffolding
from cmo_runtime.content_flow import (
    BLOG_CATEGORY_SLUGS,
    IMAGE_MARKER,
    MAX_IMAGE_SLOTS,
    ContentRunRefused,
    _validate_svg,
)


_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.S)
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_INLINE = re.compile(
    r"\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|(?<!\*)\*([^*]+)\*(?!\*)|`([^`]+)`"
)
_TABLE_DIVIDER = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
#: Board field naming the article's cover image, when one was generated.
COVER_FIELD = "Cover image"

#: Suffixes accepted for a generated or uploaded illustration. WebP is what the
#: generator writes; the other three exist because the console upload route has
#: always accepted them and a human-supplied picture publishes the same way.
RASTER_SUFFIXES = frozenset({".webp", ".png", ".jpg", ".jpeg"})

#: Said under an illustration no human drew. Every generated image also carries an
#: invisible SynthID watermark; this is the half a reader can see. Set to "" to stop
#: disclosing.
AI_FIGURE_CREDIT = "Illustration generated with AI."

_REQUIRED_FRONTMATTER = {
    "title",
    "meta_title",
    "meta_description",
    "slug",
    "audience",
    "source_urls",
}


class BlogPublishRefused(RuntimeError):
    """A fail-closed publisher outcome safe to show to an operator."""


@dataclass(frozen=True)
class Figure:
    """One rendered `<figure>`: where the file will live and what it says."""

    src: str
    alt: str
    width: int
    height: int
    caption: str
    credit: str
    kind: str


@dataclass(frozen=True)
class PublishedImage:
    """One file this publish will write into the website worktree."""

    path: Path
    source: bytes
    role: str


@dataclass(frozen=True)
class PublishPlan:
    task_id: str
    slug: str
    category: str
    publication_date: str
    read_time: str
    page_path: Path
    page_source: str
    updated_blog_posts: str
    #: Every image this publish writes: the diagram, the illustration when the
    #: article has one, and the cover when one was generated.
    images: tuple[PublishedImage, ...] = ()
    #: Public path of the cover, empty when the post publishes without one.
    cover_src: str = ""

    @property
    def image_paths(self) -> tuple[Path, ...]:
        return tuple(image.path for image in self.images)

    def image_for(self, role: str) -> PublishedImage | None:
        """The diagram, illustration, or cover this publish writes — or None."""
        return next((image for image in self.images if image.role == role), None)


class BlogPublisher:
    def __init__(self, profile_root: str | Path, website_root: str | Path) -> None:
        self.profile_root = Path(profile_root).resolve()
        self.website_root = Path(website_root).resolve()

    def preview(
        self,
        task_id: str,
        *,
        publication_date: date,
        category_override: str | None = None,
        _require_recorded_category: bool = False,
    ) -> PublishPlan:
        card = BoardStore(self.profile_root).get(task_id)
        expected_attachment = f"artifacts/{task_id}-content.md"
        if card.fields.get("Attachment") != expected_attachment:
            raise BlogPublishRefused(
                f"{task_id} Attachment must be {expected_attachment}"
            )
        article_path = self._artifact(expected_attachment)
        fields, body = _parse_frontmatter(article_path.read_text(encoding="utf-8"))
        if _require_recorded_category and (
            not fields.get("category") or not card.fields.get("Category")
        ):
            raise BlogPublishRefused(
                "apply requires category in both artifact front matter and task card"
            )
        category = _resolve_category(
            artifact_category=fields.get("category", ""),
            card_category=card.fields.get("Category", ""),
            category_override=category_override,
        )
        slug = fields["slug"]
        if _SLUG.fullmatch(slug) is None:
            raise BlogPublishRefused(f"invalid blog slug: {slug}")

        public_body = _public_body(body)
        markers = list(IMAGE_MARKER.finditer(public_body))
        if not 1 <= len(markers) <= MAX_IMAGE_SLOTS:
            raise BlogPublishRefused(
                f"{task_id} must declare between one and {MAX_IMAGE_SLOTS} image slots;"
                f" found {len(markers)}"
            )

        page_path = (
            self.website_root
            / "src/app/(marketing)/blog"
            / slug
            / "page.tsx"
        )
        # Publishing over somebody else's page stays refused. Publishing over the
        # page *this card* published is a republish, and it has to be possible: the
        # converter is code, code gets fixed, and the fix has to reach the article
        # that exposed it without inventing a second slug for the same post.
        # Keyed on the preview URL rather than the change status: re-approving a
        # card resets its status to `awaiting Gate 2`, and a republish is almost
        # always preceded by exactly that. The recorded URL is the durable evidence
        # that this card published this slug.
        republishing = card.fields.get("Preview URL", "").rstrip("/").endswith(f"/blog/{slug}")
        if page_path.exists() and not republishing:
            raise BlogPublishRefused(f"blog page already exists: {page_path}")

        figures: dict[str, Figure] = {}
        images: list[PublishedImage] = []
        for marker in markers:
            slot_id = marker.group(1)
            caption = marker.group(2).strip()
            figure, published = self._bind_slot(
                card=card,
                task_id=task_id,
                slug=slug,
                slot_id=slot_id,
                caption=caption,
            )
            figures[marker.group(0)] = figure
            images.append(published)

        cover = self._bind_cover(card=card, slug=slug)
        if cover is not None:
            images.append(cover)
        cover_src = f"/images/blog/{cover.path.name}" if cover is not None else ""

        for published in images:
            if published.path.exists() and not republishing:
                raise BlogPublishRefused(f"blog image already exists: {published.path}")

        blog_posts_path = self.website_root / "src/data/blog-posts.ts"
        blog_posts = blog_posts_path.read_text(encoding="utf-8")
        read_time = _read_time(public_body)
        page_source = _render_page(
            fields=fields,
            body=public_body,
            category=category,
            publication_date=publication_date.isoformat(),
            read_time=read_time,
            figures=figures,
            cover_src=cover_src,
        )
        updated_blog_posts = _insert_blog_post(
            blog_posts,
            replace=republishing,
            slug=slug,
            title=fields["title"],
            excerpt=fields["meta_description"],
            publication_date=publication_date.isoformat(),
            read_time=read_time,
            category=category,
            cover_image=cover_src,
        )
        return PublishPlan(
            task_id=task_id,
            slug=slug,
            category=category,
            publication_date=publication_date.isoformat(),
            read_time=read_time,
            page_path=page_path,
            page_source=page_source,
            updated_blog_posts=updated_blog_posts,
            images=tuple(images),
            cover_src=cover_src,
        )

    def _image_destination(
        self, slug: str, slot_id: str, suffix: str, *, legacy: str
    ) -> Path:
        """Where one slot's file is committed on the website.

        Keyed by slot id, because an article may now carry several images of the
        same kind and the old names could not tell them apart: every diagram
        wanted `{slug}.svg` and every illustration `{slug}-figure.webp`. That
        collision is the entire reason the article was capped at one of each.

        A file already sitting at the old name keeps it. Republishing is a
        supported path -- the converter is code, code gets fixed, and the fix has
        to reach the article that exposed it -- and renaming an image on a live
        page would break the URL for a fix that has nothing to do with it.
        """
        directory = self.website_root / "public/images/blog"
        existing = directory / legacy
        if existing.exists():
            return existing
        return directory / f"{slug}-{slot_id.casefold()}{suffix}"

    def _bind_slot(
        self,
        *,
        card: Any,
        task_id: str,
        slug: str,
        slot_id: str,
        caption: str,
    ) -> tuple["Figure", "PublishedImage"]:
        """Resolve one declared image slot to the file that will be committed.

        The bound artifact's suffix decides which kind it is. That is the whole
        dispatch: an SVG is the writer's hand-authored diagram and is validated as
        one, anything else is a generated or uploaded illustration and is validated
        as one. No second marker syntax, because the board field already says which
        file is bound and the file already says what it is.
        """
        image_field = f"Image slot {slot_id}"
        reference = card.fields.get(image_field, "")
        if not reference:
            raise BlogPublishRefused(f"{task_id} is missing card field: {image_field}")
        source_path = self._artifact(reference)
        source = source_path.read_bytes()
        suffix = source_path.suffix.casefold()

        if suffix == ".svg":
            try:
                svg_text = source.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise BlogPublishRefused(f"{reference} is not UTF-8 SVG") from exc
            try:
                _validate_svg(svg_text)
            except ContentRunRefused as exc:
                raise BlogPublishRefused(f"SVG refused: {exc}") from exc
            alt_text, width, height = _svg_metadata(svg_text)
            destination = self._image_destination(slug, slot_id, ".svg", legacy=f"{slug}.svg")
            credit = ""
            kind = "diagram"
        elif suffix in RASTER_SUFFIXES:
            # A picture carries no title element to read alt text out of, so the
            # writer states it on the card. An illustration nobody described is not
            # publishable: a screen reader would reach it and find nothing.
            alt_text = _single_line_field(card.fields.get(f"Image alt {slot_id}", ""))
            if not alt_text:
                raise BlogPublishRefused(
                    f"{task_id} is missing card field: Image alt {slot_id}"
                )
            width, height = _raster_metadata(source, reference)
            destination = self._image_destination(
                slug, slot_id, suffix, legacy=f"{slug}-figure{suffix}"
            )
            credit = AI_FIGURE_CREDIT
            kind = "illustration"
        else:
            raise BlogPublishRefused(
                f"{reference} is not a publishable image; expected .svg or one of "
                + ", ".join(sorted(RASTER_SUFFIXES))
            )

        figure = Figure(
            src=f"/images/blog/{destination.name}",
            alt=alt_text,
            width=width,
            height=height,
            caption=caption,
            credit=credit,
            kind=kind,
        )
        return figure, PublishedImage(path=destination, source=source, role=kind)

    def _bind_cover(self, *, card: Any, slug: str) -> "PublishedImage | None":
        """Resolve the card's cover image, if it has one.

        Optional on purpose. A cover that failed to generate must not hold an
        approved article at the gate — the blog card falls back to its category
        gradient exactly as it did before covers existed.
        """
        reference = card.fields.get(COVER_FIELD, "")
        if not reference:
            return None
        source_path = self._artifact(reference)
        suffix = source_path.suffix.casefold()
        if suffix not in RASTER_SUFFIXES:
            raise BlogPublishRefused(
                f"{COVER_FIELD} must be a raster image; {reference} is not"
            )
        source = source_path.read_bytes()
        _raster_metadata(source, reference)
        destination = self.website_root / "public/images/blog" / f"{slug}-cover{suffix}"
        return PublishedImage(path=destination, source=source, role="cover")

    def apply(self, task_id: str, *, publication_date: date) -> PublishPlan:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=self.website_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if branch != "cmo-changes":
            raise BlogPublishRefused(
                f"website apply requires cmo-changes; current branch is {branch or '<detached>'}"
            )
        # Tracked files only. The worktree permanently carries untracked agent
        # scratch (context/, memory.md), so a blanket clean check refuses every
        # publish forever — while a *tracked* modification really is somebody
        # else's work in progress and must stop this. Nothing untracked can ride
        # along regardless: the commit stages its three paths by name.
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=self.website_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if status:
            raise BlogPublishRefused(
                "website worktree has uncommitted tracked changes: " + status.replace("\n", "; ")
            )
        plan = self.preview(
            task_id,
            publication_date=publication_date,
            _require_recorded_category=True,
        )
        blog_posts_path = self.website_root / "src/data/blog-posts.ts"
        _atomic_publish(
            {
                plan.page_path: plan.page_source.encode("utf-8"),
                blog_posts_path: plan.updated_blog_posts.encode("utf-8"),
                **{image.path: image.source for image in plan.images},
            }
        )
        return plan

    def write_preview(self, plan: PublishPlan, output_dir: str | Path) -> dict[str, Path]:
        output = Path(output_dir).resolve()
        try:
            output.relative_to(self.website_root)
        except ValueError:
            pass
        else:
            raise BlogPublishRefused("preview output must not be inside the website worktree")
        paths = {
            "page": output
            / "src/app/(marketing)/blog"
            / plan.slug
            / "page.tsx",
            "blog_posts": output / "src/data/blog-posts.ts",
        }
        # Mirrors the worktree layout so a preview can be typechecked exactly where
        # the real page would sit, images and all.
        for image in plan.images:
            key = image.role if image.role != "diagram" else "image"
            paths[key] = output / "public/images/blog" / image.path.name
        existing = [str(path) for path in paths.values() if path.exists()]
        if existing:
            raise BlogPublishRefused(
                "preview output already exists: " + ", ".join(existing)
            )
        _atomic_publish(
            {
                paths["page"]: plan.page_source.encode("utf-8"),
                paths["blog_posts"]: plan.updated_blog_posts.encode("utf-8"),
                **{
                    output / "public/images/blog" / image.path.name: image.source
                    for image in plan.images
                },
            }
        )
        return paths

    def _artifact(self, reference: str) -> Path:
        if not reference.startswith("artifacts/"):
            raise BlogPublishRefused(f"artifact must be beneath artifacts/: {reference}")
        artifacts = (self.profile_root / "artifacts").resolve()
        candidate = (self.profile_root / reference).resolve()
        try:
            candidate.relative_to(artifacts)
        except ValueError as exc:
            raise BlogPublishRefused(f"artifact escaped artifacts/: {reference}") from exc
        if not candidate.is_file():
            raise BlogPublishRefused(f"artifact does not exist: {reference}")
        return candidate


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(markdown.strip())
    if match is None:
        raise BlogPublishRefused("article is missing flat front matter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise BlogPublishRefused(f"invalid front-matter line: {line}")
        name, value = line.split(":", 1)
        name = name.strip()
        if name in fields:
            raise BlogPublishRefused(f"duplicate front-matter field: {name}")
        fields[name] = value.strip()
    missing = sorted(name for name in _REQUIRED_FRONTMATTER if not fields.get(name))
    if missing:
        raise BlogPublishRefused("article front matter is missing: " + ", ".join(missing))
    return fields, match.group(2).strip()


def _resolve_category(
    *,
    artifact_category: str,
    card_category: str,
    category_override: str | None,
) -> str:
    supplied = [value for value in (artifact_category, card_category) if value]
    if len(set(supplied)) > 1:
        raise BlogPublishRefused(
            f"artifact category {artifact_category!r} does not match card category {card_category!r}"
        )
    category = supplied[0] if supplied else (category_override or "")
    if category_override and category and category_override != category:
        raise BlogPublishRefused(
            f"category override {category_override!r} does not match recorded category {category!r}"
        )
    if not category:
        allowed = ", ".join(sorted(BLOG_CATEGORY_SLUGS))
        raise BlogPublishRefused(f"category is undecided; choose one of: {allowed}")
    if category not in BLOG_CATEGORY_SLUGS:
        raise BlogPublishRefused(f"unknown blog category: {category}")
    return category


def _read_time(body: str) -> str:
    without_markers = IMAGE_MARKER.sub("", body)
    words = re.findall(r"\b[\w’'-]+\b", without_markers, re.UNICODE)
    minutes = max(1, math.ceil(len(words) / 200))
    return f"{minutes} min read"


def _public_body(body: str) -> str:
    """Everything a reader should see. One definition, shared with the console.

    This used to carry its own list of three heading names. The console carried a
    different list of five, and the difference went to the website: `Decision
    bullets:` was on the console's list and not on this one, so it was published
    under its own heading, on a page anyone can read.
    """
    return strip_scaffolding(body)


def _single_line_field(value: object) -> str:
    return " ".join(str(value or "").split())


def _raster_metadata(source: bytes, reference: str) -> tuple[int, int]:
    """Read a picture's pixel dimensions, or refuse it.

    The `<Image>` element needs real width and height or the page reflows as the
    picture loads, and a size taken on trust from a board field would be a size
    nobody measured. Pillow is already in the runtime venv for the generator.
    """
    from PIL import Image as PillowImage

    try:
        with PillowImage.open(io.BytesIO(source)) as opened:
            width, height = opened.size
            opened.verify()
    except Exception as exc:  # Pillow raises a wide family for malformed input
        raise BlogPublishRefused(f"{reference} is not a readable image: {exc}") from exc
    if width < 1 or height < 1:
        raise BlogPublishRefused(f"{reference} has no dimensions")
    return width, height


def _svg_metadata(svg: str) -> tuple[str, int, int]:
    root = ET.fromstring(svg)
    title = next(
        (
            (element.text or "").strip()
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "title" and (element.text or "").strip()
        ),
        "",
    )
    if not title:
        raise BlogPublishRefused("SVG requires non-empty title text for image alt text")
    parts = root.attrib.get("viewBox", "").replace(",", " ").split()
    if len(parts) != 4:
        raise BlogPublishRefused("SVG viewBox must contain four numbers")
    try:
        width_value = float(parts[2])
        height_value = float(parts[3])
    except ValueError as exc:
        raise BlogPublishRefused("SVG viewBox contains a non-numeric dimension") from exc
    if width_value <= 0 or height_value <= 0:
        raise BlogPublishRefused("SVG viewBox dimensions must be positive")
    return title, max(1, round(width_value)), max(1, round(height_value))


def _jsx_text(value: str) -> str:
    return (
        html.escape(value, quote=False)
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def _render_inline(value: str) -> str:
    rendered: list[str] = []
    cursor = 0
    for match in _INLINE.finditer(value):
        rendered.append(_jsx_text(value[cursor : match.start()]))
        label, href, strong, emphasis, code = match.groups()
        if label is not None and href is not None:
            if not (href.startswith("https://") or href.startswith("http://") or href.startswith("/")):
                raise BlogPublishRefused(f"unsupported link destination: {href}")
            external = href.startswith(("https://", "http://"))
            attributes = (
                ' target="_blank" rel="noopener noreferrer"' if external else ""
            )
            rendered.append(
                f'<a href="{html.escape(href, quote=True)}"{attributes}>'
                f"{_render_inline(label)}</a>"
            )
        elif strong is not None:
            rendered.append(f"<strong>{_render_inline(strong)}</strong>")
        elif emphasis is not None:
            rendered.append(f"<em>{_render_inline(emphasis)}</em>")
        else:
            rendered.append(f"<code>{_jsx_text(code or '')}</code>")
        cursor = match.end()
    rendered.append(_jsx_text(value[cursor:]))
    return "".join(rendered)


def _table_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _render_blocks(body: str, *, figures: Mapping[str, Figure]) -> str:
    if re.search(r"<\s*/?\s*[A-Za-z]", body):
        raise BlogPublishRefused("raw HTML is not supported in writer Markdown")
    lines = body.splitlines()
    blocks: list[str] = []
    index = 0
    h1_seen = False
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            if h1_seen:
                raise BlogPublishRefused("article contains more than one Markdown H1")
            h1_seen = True
            index += 1
            continue
        if line in figures:
            figure = figures[line]
            caption_html = _render_inline(figure.caption)
            if figure.credit:
                caption_html += (
                    f' <span className="text-gray-400">{html.escape(figure.credit)}</span>'
                )
            blocks.extend(
                [
                    '      <figure className="my-10">',
                    "        <Image",
                    f'          src="{html.escape(figure.src, quote=True)}"',
                    f'          alt="{html.escape(figure.alt, quote=True)}"',
                    f"          width={{{figure.width}}}",
                    f"          height={{{figure.height}}}",
                    '          loading="lazy"',
                    "          unoptimized",
                    '          className="h-auto w-full rounded-xl"',
                    "        />",
                    f"        <figcaption>{caption_html}</figcaption>",
                    "      </figure>",
                ]
            )
            index += 1
            continue
        heading = re.match(r"^(#{2,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            blocks.append(
                f"      <h{level}>{_render_inline(heading.group(2))}</h{level}>"
            )
            index += 1
            continue
        if index + 1 < len(lines) and "|" in line and _TABLE_DIVIDER.match(lines[index + 1]):
            headers = _table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(_table_cells(lines[index]))
                index += 1
            if any(len(row) != len(headers) for row in rows):
                raise BlogPublishRefused("Markdown table rows have inconsistent column counts")
            blocks.extend(
                [
                    '      <div className="overflow-x-auto">',
                    "        <table>",
                    "          <thead>",
                    "            <tr>",
                ]
            )
            blocks.extend(
                f"              <th>{_render_inline(cell)}</th>" for cell in headers
            )
            blocks.extend(["            </tr>", "          </thead>", "          <tbody>"])
            for row in rows:
                blocks.append("            <tr>")
                blocks.extend(
                    f"              <td>{_render_inline(cell)}</td>" for cell in row
                )
                blocks.append("            </tr>")
            blocks.extend(["          </tbody>", "        </table>", "      </div>"])
            continue
        unordered = re.match(r"^-\s+(.+)$", line)
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if unordered or ordered:
            tag = "ul" if unordered else "ol"
            items: list[str] = []
            pattern = re.compile(r"^-\s+(.+)$" if unordered else r"^\d+\.\s+(.+)$")
            while index < len(lines):
                item = pattern.match(lines[index].strip())
                if item is None:
                    break
                items.append(item.group(1))
                index += 1
            blocks.append(f"      <{tag}>")
            blocks.extend(f"        <li>{_render_inline(item)}</li>" for item in items)
            blocks.append(f"      </{tag}>")
            continue
        if line == "---":
            blocks.append("      <hr />")
            index += 1
            continue

        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip():
            candidate = lines[index].strip()
            if (
                # `figures` is keyed by the whole marker line, the same way the
                # block loop above tests it. This read `candidate == marker` for
                # as long as `marker` had been gone from the signature: a
                # paragraph wrapped over two lines raised NameError instead of
                # publishing, which writer-generated Markdown never hit because
                # it puts a paragraph on one line, and a hand-edited article did.
                candidate in figures
                or candidate.startswith("#")
                or re.match(r"^(?:-|\d+\.)\s+", candidate)
                or (
                    index + 1 < len(lines)
                    and "|" in candidate
                    and _TABLE_DIVIDER.match(lines[index + 1])
                )
            ):
                break
            paragraph.append(candidate)
            index += 1
        blocks.append(f"      <p>{_render_inline(' '.join(paragraph))}</p>")
    return "\n".join(blocks)


def _component_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-")) + "Article"


def _render_page(
    *,
    fields: dict[str, str],
    body: str,
    category: str,
    publication_date: str,
    read_time: str,
    figures: Mapping[str, Figure],
    cover_src: str = "",
) -> str:
    blocks = _render_blocks(body, figures=figures)
    title = json.dumps(fields["meta_title"], ensure_ascii=False)
    description = json.dumps(fields["meta_description"], ensure_ascii=False)
    slug = fields["slug"]
    path = json.dumps(f"/blog/{slug}", ensure_ascii=False)
    layout_title = html.escape(fields["title"], quote=True)
    # Without this the post shares the generic site-wide `/og-image.jpg`. Omitted
    # rather than faked when the article publishes with no cover: `createMetadata`
    # already falls back.
    og_image = (
        f"\n  ogImage: {json.dumps(cover_src, ensure_ascii=False)}," if cover_src else ""
    )
    return f'''import Image from "next/image";
import {{ createMetadata }} from "@/lib/metadata";
import BlogLayout from "@/components/blog/BlogLayout";

export const metadata = createMetadata({{
  title: {title},
  description: {description},
  path: {path},{og_image}
}});

export default function {_component_name(slug)}() {{
  return (
    <BlogLayout
      title="{layout_title}"
      slug="{html.escape(slug, quote=True)}"
      date="{publication_date}"
      readTime="{read_time}"
      category="{category}"
    >
{blocks}
    </BlogLayout>
  );
}}
'''


def _insert_blog_post(
    source: str,
    *,
    replace: bool = False,
    slug: str,
    title: str,
    excerpt: str,
    publication_date: str,
    read_time: str,
    category: str,
    cover_image: str = "",
) -> str:
    existing = re.search(rf'(?m)^  \{{\n(?:.*\n)*?    slug: {re.escape(json.dumps(slug))},\n(?:.*\n)*?  \}},\n', source)
    if existing is not None:
        if not replace:
            raise BlogPublishRefused(f"blogPosts already contains slug: {slug}")
        # A republish rewrites its own entry in place rather than adding a second
        # one, so /blog does not list the post twice.
        source = source[: existing.start()] + source[existing.end():]
    elif re.search(rf'^\s+slug:\s*{re.escape(json.dumps(slug))},?\s*$', source, re.M):
        raise BlogPublishRefused(f"blogPosts already contains slug: {slug}")
    start = source.find("export const blogPosts")
    if start < 0:
        raise BlogPublishRefused("blog-posts.ts has no blogPosts export")
    closing = source.find("\n];", start)
    if closing < 0:
        raise BlogPublishRefused("blog-posts.ts blogPosts array has no closing bracket")
    entry = "\n".join(
        [
            "  {",
            f"    slug: {json.dumps(slug, ensure_ascii=False)},",
            f"    title: {json.dumps(title, ensure_ascii=False)},",
            f"    excerpt: {json.dumps(excerpt, ensure_ascii=False)},",
            f"    date: {json.dumps(publication_date)},",
            f"    readTime: {json.dumps(read_time)},",
            f"    category: {json.dumps(category)},",
        ]
        + (
            [f"    coverImage: {json.dumps(cover_image, ensure_ascii=False)},"]
            if cover_image
            else []
        )
        + ["  },"]
    )
    prefix = source[:closing].rstrip()
    return prefix + "\n" + entry + source[closing:]


def _atomic_publish(files: dict[Path, bytes]) -> None:
    originals = {path: path.read_bytes() if path.is_file() else None for path in files}
    staged: dict[Path, Path] = {}
    try:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            temporary_path = Path(temporary)
            staged[path] = temporary_path
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        replaced: list[Path] = []
        try:
            for path, temporary_path in staged.items():
                os.replace(temporary_path, path)
                replaced.append(path)
        except Exception:
            for path in reversed(replaced):
                original = originals[path]
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    descriptor, temporary = tempfile.mkstemp(
                        prefix=f".{path.name}.restore.",
                        dir=path.parent,
                    )
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(original)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, path)
            raise
    finally:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    default_profile = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Convert an approved iTarang Markdown artifact into website blog sources."
    )
    parser.add_argument("task_id", metavar="TASK-ID")
    parser.add_argument("--profile-root", type=Path, default=default_profile)
    parser.add_argument(
        "--website-root",
        type=Path,
        default=Path(os.environ.get("ITARANG_WEBSITE_ROOT", "/opt/data/work/itarang-website")),
    )
    parser.add_argument("--date", dest="publication_date")
    parser.add_argument("--category", choices=sorted(BLOG_CATEGORY_SLUGS))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        publish_date = (
            date.fromisoformat(args.publication_date)
            if args.publication_date
            else datetime.now(UTC).date()
        )
    except ValueError:
        parser.error("--date must use YYYY-MM-DD")

    publisher = BlogPublisher(args.profile_root, args.website_root)
    try:
        if args.apply:
            if args.category:
                raise BlogPublishRefused(
                    "--category is dry-run only; apply requires category in artifact and card"
                )
            plan = publisher.apply(args.task_id, publication_date=publish_date)
            print(f"APPLIED (not committed): {plan.page_path}")
            print(f"UPDATED: {publisher.website_root / 'src/data/blog-posts.ts'}")
            for image in plan.images:
                print(f"COPIED ({image.role}): {image.path}")
            return 0

        plan = publisher.preview(
            args.task_id,
            publication_date=publish_date,
            category_override=args.category,
        )
        output_dir = args.output_dir or (
            publisher.profile_root / "tmp" / f"{args.task_id}-publish-preview"
        )
        paths = publisher.write_preview(plan, output_dir)
        print("DRY RUN — website worktree unchanged")
        print(f"PAGE: {paths['page']}")
        print(f"BLOG INDEX: {paths['blog_posts']}")
        for image in plan.images:
            print(f"IMAGE ({image.role}): {paths[image.role if image.role != 'diagram' else 'image']}")
        print(f"DATE: {plan.publication_date}")
        print(f"READ TIME: {plan.read_time}")
        print(f"CATEGORY: {plan.category}")
        return 0
    except BlogPublishRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
