"""Every blog post the website publishes, read from the site's own registry.

The Social tab used to list *task cards* whose board state said `published`, and
that list was wrong in both directions. It carried three cards that were never
articles at all -- two dummy end-to-end fixtures and a landing-page brief -- and
it carried none of the seven articles a reader can actually open, because the
oldest posts were written by hand and never had a card, and the newest ones sit
on `cmo-changes` under a card that still says "in preview".

So the list comes from the place the site itself decides what is published:
`src/data/blog-posts.ts`. Everything in `blogPosts` renders on /blog and has a
page; nothing else does. A card, when one exists for the same slug, is still
worth having -- it carries the writer's artifact and the topic keywords the copy
is written from -- but it is no longer what decides whether an article is on the
list.

`main` is the branch the VPS deploys, so the slugs in `main` are the ones a
follower can open today. A slug that is only on `cmo-changes` is listed too,
marked as not live yet, because a human wants to see the article coming and write
its copy before the merge -- but `ceo_social` refuses to send it, and asks the
live site rather than trusting this flag.

The page directories are read as well as the registry, and that is not
belt-and-braces. Commit `430c3c6` replaced the `blogPosts` array instead of
appending to it, dropping four articles -- including both of the two that are
live on `main` today -- while their pages stayed on disk and kept answering. An
article whose page exists is an article a reader can open, whatever the registry
currently remembers, so it belongs on this list and its absence from the registry
is said out loud rather than silently obeyed.
"""

from __future__ import annotations

import hashlib
import html
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

#: How an article is addressed once it is not a task card. `ceo_social` and the
#: console both key rows on this, and `crosspost_drafts.task_id` stores it -- the
#: column is TEXT and has never meant anything narrower than "which article".
ARTICLE_PREFIX = "blog:"

#: The branch the VPS deploys. A slug in this branch's registry is a live URL.
LIVE_BRANCH = "main"

#: The registry itself, relative to the checkout root.
REGISTRY_PATH = "src/data/blog-posts.ts"

#: Where a post's page lives. The first that exists wins; the route group is part
#: of the directory name and not a pattern.
PAGE_DIRECTORIES = ("src/app/(marketing)/blog", "src/app/blog")

_ENTRIES = re.compile(r"export const blogPosts\b[^=]*=\s*\[(.*?)\n\];", re.S)
_TAG = re.compile(r"<[^>]+>")
_EXPRESSION = re.compile(r"\{[^{}]*\}")


def article_key(slug: str) -> str:
    """The console row key for a published article."""
    return f"{ARTICLE_PREFIX}{slug}"


def slug_of_key(key: str) -> str:
    """The slug inside an article key, or "" when the key is a task id."""
    key = str(key or "")
    return key[len(ARTICLE_PREFIX):] if key.startswith(ARTICLE_PREFIX) else ""


@dataclass(frozen=True)
class BlogPost:
    """One published article: what it says, whether it is live, how it was found."""

    slug: str
    title: str
    excerpt: str
    date: str
    category: str
    cover_image: str
    #: `main` publishes this slug, so the URL answers for a reader today.
    live: bool = False
    #: The registry lists it. False means the page exists and answers but /blog
    #: and the sitemap do not link it -- promoting it is still fine, and the
    #: console says so rather than hiding the article.
    listed: bool = True

    @property
    def key(self) -> str:
        return article_key(self.slug)


def _field(entry: str, name: str) -> str:
    """One `name: "value"` from a registry entry, across a line break if need be."""
    match = re.search(rf'\b{name}:\s*"((?:[^"\\]|\\.)*)"', entry, re.S)
    if match is None:
        return ""
    return " ".join(match.group(1).replace('\\"', '"').split())


def _entries(source: str) -> list[str]:
    """The object literals inside `blogPosts`, by brace depth rather than by regex.

    `blogCategories` sits in the same file and also has `slug:` on every line, so
    the array has to be found before anything is matched inside it.
    """
    block = _ENTRIES.search(source)
    if block is None:
        return []
    body = block.group(1)
    found: list[str] = []
    depth = 0
    start = 0
    for index, character in enumerate(body):
        if character == "{":
            if depth == 0:
                start = index + 1
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                found.append(body[start:index])
    return found


def parse(source: str) -> list[BlogPost]:
    """Read `blogPosts` out of the registry's text."""
    posts: list[BlogPost] = []
    for entry in _entries(source):
        slug = _field(entry, "slug")
        if not slug:
            continue
        posts.append(
            BlogPost(
                slug=slug,
                title=_field(entry, "title"),
                excerpt=_field(entry, "excerpt"),
                date=_field(entry, "date"),
                category=_field(entry, "category"),
                cover_image=_field(entry, "coverImage"),
            )
        )
    return posts


def live_slugs(website_root: str | Path) -> set[str]:
    """The slugs `main` publishes, read from git rather than from the working tree.

    The checkout sits on `cmo-changes` -- reading the file on disk would report
    unmerged drafts as live. A git that cannot answer returns nothing rather than
    raising: the flag is a label, and the send gate asks the live site anyway.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(website_root), "show", f"{LIVE_BRANCH}:{REGISTRY_PATH}"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if result.returncode != 0:
        return set() | _live_pages(website_root)
    return {post.slug for post in parse(result.stdout)} | _live_pages(website_root)


def _live_pages(website_root: str | Path) -> set[str]:
    """The slugs that have a page on `main` -- the URLs that answer today.

    A page that `main` carries is reachable whether or not `main`'s registry
    lists it, and both articles live on the site right now are in exactly that
    position on this branch.
    """
    found: set[str] = set()
    for directory in PAGE_DIRECTORIES:
        try:
            result = subprocess.run(
                ["git", "-C", str(website_root), "ls-tree", "--name-only",
                 f"{LIVE_BRANCH}:{directory}"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode != 0:
            continue
        found.update(
            name.rstrip("/")
            for name in result.stdout.split()
            if name.rstrip("/") and not name.endswith(".tsx") and name.rstrip("/") != "category"
        )
    return found


def posts(website_root: str | Path) -> list[BlogPost]:
    """Every published article, newest first: the registry, plus every page on disk."""
    website_root = Path(website_root)
    try:
        source = (website_root / REGISTRY_PATH).read_text(encoding="utf-8")
    except OSError:
        source = ""
    live = live_slugs(website_root)

    found: dict[str, BlogPost] = {}
    for post in parse(source):
        found[post.slug] = BlogPost(
            slug=post.slug,
            title=post.title,
            excerpt=post.excerpt,
            date=post.date,
            category=post.category,
            cover_image=post.cover_image,
            live=post.slug in live,
            listed=True,
        )
    for slug in _page_slugs(website_root):
        if slug in found:
            continue
        found[slug] = _post_from_page(website_root, slug, live=slug in live)

    # The registry is hand-ordered newest-first today; sorting by the date the
    # post itself carries keeps that true when somebody appends to the end, and
    # gives the pages found on disk somewhere sensible to land.
    return sorted(found.values(), key=lambda post: (post.date, post.slug), reverse=True)


def _page_slugs(website_root: Path) -> list[str]:
    """Every article directory in the checkout, whatever the registry says."""
    found: list[str] = []
    for directory in PAGE_DIRECTORIES:
        root = website_root / directory
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.is_dir() and child.name != "category" and (child / "page.tsx").is_file():
                found.append(child.name)
    return found


def _attribute(page_source: str, name: str) -> str:
    """One `name="value"` off the page's `BlogLayout`, which is its own metadata."""
    match = re.search(rf'\b{name}=\{{?"([^"]*)"', page_source)
    return " ".join(match.group(1).split()) if match else ""


def _post_from_page(website_root: Path, slug: str, *, live: bool) -> BlogPost:
    """An article the registry forgot, read from the page that still answers."""
    page = page_path(website_root, slug)
    source = page.read_text(encoding="utf-8") if page is not None else ""
    description = re.search(r'description:\s*\n?\s*"((?:[^"\\]|\\.)*)"', source, re.S)
    return BlogPost(
        slug=slug,
        title=_attribute(source, "title") or slug.replace("-", " "),
        excerpt=" ".join(description.group(1).split()) if description else "",
        date=_attribute(source, "date"),
        category=_attribute(source, "category"),
        cover_image=_attribute(source, "ogImage"),
        live=live,
        listed=False,
    )


def find(website_root: str | Path, slug: str) -> BlogPost | None:
    return next((post for post in posts(website_root) if post.slug == slug), None)


def page_path(website_root: str | Path, slug: str) -> Path | None:
    """The article's page source, which is where its prose lives."""
    for directory in PAGE_DIRECTORIES:
        candidate = Path(website_root) / directory / slug / "page.tsx"
        if candidate.is_file():
            return candidate
    return None


def _prose(page_source: str) -> list[str]:
    """The article's readable text, in order, out of its JSX.

    Only `<p>` and `<h2>` are taken. Everything else on these pages is layout,
    a figure caption, or an import, and copy assembled from a `className` reads
    exactly as badly as it sounds.
    """
    lines: list[str] = []
    for match in re.finditer(r"<(p|h2)(?:\s[^>]*)?>(.*?)</\1>", page_source, re.S):
        text = _EXPRESSION.sub(" ", match.group(2))
        text = html.unescape(_TAG.sub(" ", text))
        text = " ".join(text.split())
        if not text:
            continue
        lines.append(f"## {text}" if match.group(1) == "h2" else text)
    return lines


def article_markdown(website_root: str | Path, post: BlogPost) -> str:
    """The article as the copy writer expects to read it: front matter, then prose.

    `social_copy.summarise_article` reads a published writer artifact, and a post
    that never went through the writer has no artifact. It does have a page, and
    the page has the same two things the summary actually uses -- the header
    fields and the article's own sentences -- so they are assembled here rather
    than the article being refused for the accident of how it was written.
    """
    page = page_path(website_root, post.slug)
    body = "\n\n".join(_prose(page.read_text(encoding="utf-8"))) if page else ""
    front = [
        "---",
        f"title: {post.title}",
        f"meta_description: {post.excerpt}",
        f"slug: {post.slug}",
        f"category: {post.category}",
        "---",
        "",
    ]
    return "\n".join(front) + (body or post.excerpt) + "\n"


def fingerprint(website_root: str | Path, post: BlogPost) -> str:
    """A digest over what a send was approved of: the registry entry and the page.

    `send` refuses an instruction whose fingerprint no longer matches, so that an
    article edited between "prepare" and "approve" is read again before it is
    promoted. A carded article gets that from `publish_fingerprint`; this is the
    same promise for an article whose source of truth is the checkout.
    """
    digest = hashlib.sha256()
    for part in (post.slug, post.title, post.excerpt, post.date, post.cover_image):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    page = page_path(website_root, post.slug)
    if page is not None:
        try:
            digest.update(page.read_bytes())
        except OSError:
            digest.update(b"unreadable")
    return digest.hexdigest()
