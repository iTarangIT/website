"""Cross-post a published article to LinkedIn, X and Instagram, through Buffer.

The shape is deliberately the one `ceo_blog_publish` already uses, because it is
the shape that has held: `preflight` reports whether a human *may* be offered the
instruction and says why not in whole sentences; `issue_request` mints a
single-use token only a page render for an authenticated human can obtain; `send`
consumes that token before it touches the network, so a replay never reaches
Buffer.

Three things are load-bearing.

**Nothing is sent before the article is live.** A social post is a link, and a
link to an unmerged branch is a 404 for every follower who taps it. Instagram
makes that literal — Buffer fetches the cover image over the public internet, so
a post for an unpublished article cannot even be constructed. `preflight`
therefore refuses until the card says `merged to main`, and names that as the
blocker rather than greying a button in silence.

**One draft, one row, one Buffer post.** A platform whose row is already `queued`
is not offered again, and regenerating copy does not clear that. Buffer holds the
post either way; a console that forgot would offer to publish it twice.

**A partial send is reported as a partial send.** Three platforms are three
independent Buffer calls, and there is no transaction across them. When the
second fails the first stays queued, its row says so, and the result names
exactly which went and which did not — rather than one "failed" that leaves a
human guessing whether to press it again.
"""

from __future__ import annotations

import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import ceo_publish
from ceo_publish import PublicationConflict, PublicationRefused
from cmo_runtime import social_copy
from cmo_runtime.buffer_client import BufferClient, BufferRefused
from cmo_runtime.console_db import CROSSPOST_PLATFORMS, ConsoleDB

#: Where the website checkout lives on this box — the source of the cover image
#: whose extension the Instagram post needs.
DEFAULT_WEBSITE_ROOT = "/opt/data/work/itarang-website"

#: How long to wait when checking that the article really is reachable.
LIVE_CHECK_TIMEOUT_SECONDS = 8

#: The cover extensions the publisher may have written.
COVER_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg", ".svg")

#: Instagram will not take an SVG. A diagram-only article can be posted to
#: LinkedIn and X and is refused for Instagram, with that sentence on screen.
INSTAGRAM_IMAGE_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg")


@dataclass(frozen=True)
class SocialPreflight:
    """Whether this article may be cross-posted, and everything the tab renders."""

    task_id: str
    eligible: bool
    blockers: list[str] = field(default_factory=list)
    slug: str = ""
    title: str = ""
    live_url: str = ""
    cover_url: str = ""
    fingerprint: str = ""
    channels: list[dict[str, Any]] = field(default_factory=list)
    drafts: list[dict[str, Any]] = field(default_factory=list)
    sendable: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "eligible": self.eligible,
            "blockers": list(self.blockers),
            "slug": self.slug,
            "title": self.title,
            "live_url": self.live_url,
            "cover_url": self.cover_url,
            "fingerprint": self.fingerprint,
            "channels": list(self.channels),
            "drafts": list(self.drafts),
            "sendable": list(self.sendable),
            "notes": list(self.notes),
        }


def live_origin() -> str:
    """The production origin, from the same place `preview_metrics` reads it."""
    import preview_metrics

    return preview_metrics.live_url()


def _requests_path(profile_dir: Path) -> Path:
    return profile_dir / "state" / "social-send-requests.json"


def _cover_path(website_root: Path, slug: str) -> Path | None:
    """The cover the publisher wrote, found by extension rather than assumed."""
    for suffix in COVER_SUFFIXES:
        candidate = website_root / "public" / "images" / "blog" / f"{slug}-cover{suffix}"
        if candidate.is_file():
            return candidate
    return None


def article_is_reachable(url: str, *, opener: Any | None = None) -> bool:
    """Whether the live URL actually answers.

    The board says `merged to main` the moment Gate 2 merges; the VPS deploy that
    makes the page real happens afterwards. Asking the site is the difference
    between "we merged it" and "a reader can open it", and only the second is a
    reason to post a link to it.
    """
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "itarang-cmo"})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=LIVE_CHECK_TIMEOUT_SECONDS) as response:
            return 200 <= int(getattr(response, "status", 200)) < 300
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return False


def preflight(
    profile_dir: str | Path,
    task_id: str,
    *,
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    client: BufferClient | None = None,
    check_live: bool = True,
    opener: Any | None = None,
) -> SocialPreflight:
    """Report whether this article may be cross-posted, and why not when it may not."""
    import console_board

    profile_dir = Path(profile_dir)
    website_root = Path(website_root)
    board = console_board.read_board(profile_dir / "tasks.md", profile_dir)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        return SocialPreflight(task_id, False, [f"no such task: {task_id}"])

    blockers: list[str] = []
    notes: list[str] = []

    state = console_board.blog_state(task)
    slug = _slug_for(task, profile_dir)
    title = str(task.get("title", "")).strip()
    origin = live_origin()
    url = f"{origin}/blog/{slug}" if slug else ""

    if not slug:
        blockers.append("this card has no article with a slug")
    if state["state"] != "published":
        blockers.append(
            "the article is not live yet — a social post is a link, and this one "
            f"would 404 (the card says: {state['label']})"
        )
    elif check_live and url and not article_is_reachable(url, opener=opener):
        blockers.append(
            f"{url} did not answer, so the deploy has not landed yet; "
            "the post would link to a page that is not there"
        )

    cover_url = ""
    instagram_has_picture = False
    cover = _cover_path(website_root, slug) if slug else None
    if cover is not None:
        cover_url = f"{origin}/images/blog/{cover.name}"
        instagram_has_picture = cover.suffix.lower() in INSTAGRAM_IMAGE_SUFFIXES
        if not instagram_has_picture:
            notes.append(
                "The cover is an SVG, which Instagram will not accept. "
                "LinkedIn and X can still be sent."
            )
    else:
        notes.append(
            "This article has no cover image, so Instagram cannot be sent — "
            "Instagram requires a picture. LinkedIn and X are unaffected."
        )

    channels: list[dict[str, Any]] = []
    if client is None and not BufferClient.configured(str(profile_dir)):
        blockers.append(
            "Buffer is not connected — set BUFFER_ACCESS_TOKEN and "
            "BUFFER_ORGANIZATION_ID in the profile environment"
        )
    else:
        try:
            buffer = client or BufferClient.from_profile(str(profile_dir))
            channels = [channel.as_dict() for channel in buffer.channels()]
        except BufferRefused as error:
            blockers.append(str(error))

    database = ConsoleDB(profile_dir)
    try:
        drafts = database.crosspost_drafts(task_id)
    finally:
        database.close()

    fingerprint = console_board.publish_fingerprint(task, profile_dir) if slug else ""
    connected = {row["platform"]: row for row in channels if row.get("usable")}
    by_platform = {str(row["platform"]): row for row in drafts}

    sendable: list[str] = []
    for platform in CROSSPOST_PLATFORMS:
        draft = by_platform.get(platform)
        if draft is None or draft.get("status") == "queued":
            continue
        if platform not in connected:
            continue
        cards = list(draft.get("images") or ())
        if cards:
            # Buffer fetches every asset over the open internet. A card that is
            # generated but not yet merged and deployed is a 404 to Buffer, and
            # Buffer reports that as a flat "invalid input" long after the press.
            # Asking here turns it into a sentence about what to do next.
            missing = (
                [
                    card["url"]
                    for card in cards
                    if not article_is_reachable(card["url"], opener=opener)
                ]
                if check_live
                else []
            )
            if missing:
                notes.append(
                    f"The {platform} cards are not on the live site yet "
                    f"({len(missing)} of {len(cards)} unreachable). Merge the commit "
                    "that adds them and wait for the deploy before sending."
                )
                continue
        elif platform == "instagram" and not instagram_has_picture:
            continue
        sendable.append(platform)

    for platform in CROSSPOST_PLATFORMS:
        if platform not in connected:
            notes.append(f"No usable {platform} channel is connected in Buffer.")

    if not drafts:
        notes.append("No copy has been written for this article yet.")

    return SocialPreflight(
        task_id=task_id,
        eligible=not blockers and bool(sendable),
        blockers=blockers,
        slug=slug,
        title=title,
        live_url=url,
        cover_url=cover_url,
        fingerprint=fingerprint,
        channels=channels,
        drafts=drafts,
        sendable=sendable,
        notes=notes,
    )


def _slug_for(task: dict[str, Any], profile_dir: Path) -> str:
    """The article's slug, read from the artifact the card points at."""
    import re

    import console_board

    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        return ""
    match = re.search(r"(?m)^slug:\s*(.+?)\s*$", article.read_text(encoding="utf-8")[:4000])
    return match.group(1).strip().strip("\"'") if match else ""


def generate(
    profile_dir: str | Path,
    task_id: str,
    *,
    actor: str,
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    writer: Any | None = None,
) -> dict[str, Any]:
    """Write one draft per platform and store them, replacing any that are not sent."""
    import console_board

    profile_dir = Path(profile_dir)
    if not actor.strip():
        raise PublicationRefused("writing social copy requires an authenticated human")

    board = console_board.read_board(profile_dir / "tasks.md", profile_dir)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise PublicationRefused(f"no such task: {task_id}")
    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        raise PublicationRefused("this card has no article to write about")

    slug = _slug_for(task, profile_dir)
    if not slug:
        raise PublicationRefused("this article has no slug, so it has no URL to share")

    cover = _cover_path(Path(website_root), slug)
    summary = social_copy.summarise_article(
        article.read_text(encoding="utf-8"),
        url=f"{live_origin()}/blog/{slug}",
        keywords=_keywords(task),
        cover_alt=str(task.get("Cover alt", "") or task.get("cover_alt", "") or "").strip(),
    )

    skill_text = ""
    try:
        from cmo_runtime.skill_loader import SkillLoader

        skill_text = SkillLoader(profile_dir).load("social")
    except Exception:  # noqa: BLE001 - a missing skill costs authorship, not the drafts
        skill_text = ""

    if writer is None and skill_text.strip():
        writer = social_copy.HermesSocialWriter(profile_dir)

    drafts = social_copy.drafts_for(
        task_id=task_id, summary=summary, skill_text=skill_text, writer=writer
    )
    fingerprint = console_board.publish_fingerprint(task, profile_dir)

    database = ConsoleDB(profile_dir)
    try:
        for platform, draft in drafts.items():
            database.save_crosspost_draft(
                task_id=task_id,
                platform=platform,
                body=draft.body,
                link=draft.link,
                article_fingerprint=fingerprint,
                thread=draft.thread,
                image_alt=draft.image_alt or (cover.name if cover else ""),
                producer=draft.source,
            )
        stored = database.crosspost_drafts(task_id)
    finally:
        database.close()
    return {"task_id": task_id, "drafts": stored}


def _keywords(task: dict[str, Any]) -> list[str]:
    raw = str(task.get("topic_keywords", "") or task.get("Topic keywords", "") or "")
    return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]


def save_draft(
    profile_dir: str | Path,
    task_id: str,
    *,
    platform: str,
    body: str,
    thread: Sequence[str] = (),
    actor: str,
) -> dict[str, Any]:
    """Store a human's edit of one draft, refusing what a network would reject."""
    import console_board

    profile_dir = Path(profile_dir)
    if not actor.strip():
        raise PublicationRefused("editing social copy requires an authenticated human")
    if platform not in CROSSPOST_PLATFORMS:
        raise PublicationRefused(f"{platform} is not a platform this console posts to")

    draft = social_copy.SocialDraft(
        platform=platform,
        body=body.strip(),
        thread=tuple(part.strip() for part in thread if part.strip()),
        source="composed",
    )
    try:
        social_copy.validate({platform: draft})
    except social_copy.SocialCopyRefused as error:
        raise PublicationRefused(str(error)) from error

    board = console_board.read_board(profile_dir / "tasks.md", profile_dir)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise PublicationRefused(f"no such task: {task_id}")

    database = ConsoleDB(profile_dir)
    try:
        existing = {row["platform"]: row for row in database.crosspost_drafts(task_id)}
        row = existing.get(platform)
        if row is None:
            raise PublicationRefused("there is no draft for that platform to edit")
        if row.get("status") == "queued":
            raise PublicationConflict(
                "that post is already queued in Buffer; edit it there rather than here"
            )
        database.save_crosspost_draft(
            task_id=task_id,
            platform=platform,
            body=draft.body,
            link=str(row.get("link", "")),
            article_fingerprint=str(row.get("article_fingerprint", "")),
            thread=draft.thread,
            image_alt=str(row.get("image_alt", "")),
            producer="composed",
        )
        stored = database.crosspost_drafts(task_id)
    finally:
        database.close()
    return {"task_id": task_id, "drafts": stored}


def issue_request(
    profile_dir: str | Path, task_id: str, *, actor: str, fingerprint: str, platforms: Sequence[str]
) -> str:
    """Mint a single-use send instruction. Only a human page render calls this."""
    profile_dir = Path(profile_dir)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a send instruction requires an authenticated human")
    request_id = secrets.token_urlsafe(24)
    path = _requests_path(profile_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with ceo_publish._locked(profile_dir):
        pending = ceo_publish._read_json(path)
        pending[request_id] = {
            "task_id": task_id,
            "actor": actor,
            "fingerprint": fingerprint,
            "platforms": sorted(platforms),
            "issued_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        ceo_publish._write_json(path, pending)
    return request_id


def send(
    profile_dir: str | Path,
    task_id: str,
    *,
    actor: str,
    role: str,
    request_id: str,
    platforms: Sequence[str],
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    client: BufferClient | None = None,
    check_live: bool = True,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Queue the approved drafts in Buffer, one platform at a time, and say what happened."""
    profile_dir = Path(profile_dir)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a send instruction requires an authenticated human")

    # Consume the instruction before anything reaches the network, so a replay
    # cannot double-post even if it wins the race to the handler.
    with ceo_publish._locked(profile_dir):
        path = _requests_path(profile_dir)
        pending = ceo_publish._read_json(path)
        instruction = pending.pop(request_id, None)
        if instruction is None:
            raise PublicationConflict("this send instruction is unknown or already used")
        ceo_publish._write_json(path, pending)
    if instruction["task_id"] != task_id or instruction["actor"] != actor:
        raise PublicationConflict("this send instruction was issued for a different human or card")

    check = preflight(
        profile_dir,
        task_id,
        website_root=website_root,
        client=client,
        check_live=check_live,
        opener=opener,
    )
    if check.blockers:
        raise PublicationConflict("; ".join(check.blockers))
    if check.fingerprint != instruction["fingerprint"]:
        raise PublicationConflict(
            "the article changed after this instruction was issued; read it again before posting"
        )

    asked = [platform for platform in CROSSPOST_PLATFORMS if platform in set(platforms)]
    refused = [platform for platform in asked if platform not in check.sendable]
    if refused:
        raise PublicationConflict(
            "these platforms cannot be sent right now: " + ", ".join(refused)
        )
    if not asked:
        raise PublicationRefused("no platform was selected")

    buffer = client or BufferClient.from_profile(str(profile_dir))
    by_platform = {str(row["platform"]): row for row in check.drafts}
    channel_for = {row["platform"]: row["id"] for row in check.channels if row.get("usable")}

    queued: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    database = ConsoleDB(profile_dir)
    try:
        for platform in asked:
            draft = by_platform[platform]
            try:
                cards = list(draft.get("images") or ())
                post = buffer.create_post(
                    channel_id=channel_for[platform],
                    platform=platform,
                    text=str(draft.get("body", "")),
                    link=str(draft.get("link", "")),
                    # The generated cards, where this article has them. Instagram
                    # falls back to the article cover, which is the behaviour
                    # every article published before the cards existed relies on.
                    images=cards,
                    image_url=(
                        check.cover_url if platform == "instagram" and not cards else ""
                    ),
                    image_alt=str(draft.get("image_alt", "")),
                    thread=tuple(draft.get("thread") or ()),
                )
            except BufferRefused as error:
                # One platform's refusal is not the others'. Record it on its own
                # row and keep going, so a LinkedIn outage does not cost the X post.
                database.mark_crosspost_failed(
                    task_id=task_id, platform=platform, error=str(error)
                )
                failures.append({"platform": platform, "error": str(error)})
                continue
            database.mark_crosspost_queued(
                task_id=task_id,
                platform=platform,
                channel_id=channel_for[platform],
                buffer_post_id=post.id,
                scheduled_at=post.due_at,
                actor=actor,
            )
            queued.append(post.as_dict())
        drafts = database.crosspost_drafts(task_id)
    finally:
        database.close()

    ceo_publish._append_log(
        profile_dir,
        {
            "event": "social-crosspost",
            "task_id": task_id,
            "actor": actor,
            "role": role,
            "request_id": request_id,
            "queued": [post["platform"] for post in queued],
            "failed": [failure["platform"] for failure in failures],
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )

    return {
        "task_id": task_id,
        "queued": queued,
        "failed": failures,
        "drafts": drafts,
        "result": "queued" if not failures else ("partial" if queued else "refused"),
    }


#: Where the published cards are served from, and the directory the publisher
#: writes them into. The precedent is `97ddb9b`, which put one article's cards
#: here by hand so Buffer could fetch them by URL.
SOCIAL_IMAGE_DIR = "public/images/social"
SOCIAL_IMAGE_ROUTE = "/images/social"


def card_url(origin: str, filename: str) -> str:
    return f"{origin.rstrip('/')}{SOCIAL_IMAGE_ROUTE}/{filename}"


def plan_cards(
    profile_dir: str | Path, task_id: str, *, website_root: str | Path = DEFAULT_WEBSITE_ROOT
) -> tuple[list[Any], str]:
    """The card set this article would get, and its slug. Generates nothing.

    Separated from `generate_cards` so the console can show a human exactly what
    would be drawn, and what it would cost, before a rupee is spent on it.
    """
    import console_board
    from cmo_runtime import social_cards

    profile_dir = Path(profile_dir)
    board = console_board.read_board(profile_dir / "tasks.md", profile_dir)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise PublicationRefused(f"no such task: {task_id}")
    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        raise PublicationRefused("this card has no article to make social cards from")
    slug = _slug_for(task, profile_dir)
    if not slug:
        raise PublicationRefused("this article has no slug, so its cards have no URL")

    summary = social_copy.summarise_article(
        article.read_text(encoding="utf-8"),
        url=f"{live_origin()}/blog/{slug}",
        keywords=_keywords(task),
        cover_alt=str(task.get("Cover alt", "") or task.get("cover_alt", "") or "").strip(),
    )
    try:
        return social_cards.plan_cards(summary), slug
    except social_cards.CardPlanRefused as error:
        raise PublicationRefused(str(error)) from error


def generate_cards(
    profile_dir: str | Path,
    task_id: str,
    *,
    actor: str,
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    client: Any | None = None,
) -> dict[str, Any]:
    """Draw the infographics and the carousel, and bind them to the drafts.

    The words on every card were chosen by `social_cards.plan_cards` before this
    runs; the model here is a typesetter. That ordering is what makes the set
    reviewable — see `cmo_runtime/social_cards`.

    The cards are written to the artifact store, and the URLs bound to the drafts
    point at the website. They are two different places on purpose: the artifact
    is what a human reviews and what the publisher later commits, and the URL is
    what Buffer will fetch once that commit is merged and deployed. Binding the
    URL early is not a claim that it resolves yet — `preflight` is what refuses a
    send whose cards are not reachable.
    """
    from cmo_runtime import content_flow, image_gen

    profile_dir = Path(profile_dir)
    if not actor.strip():
        raise PublicationRefused("generating social cards requires an authenticated human")

    cards, slug = plan_cards(profile_dir, task_id, website_root=website_root)
    try:
        generator = client or image_gen.GeminiImageClient(profile_dir)
    except image_gen.ImageGenRefused as refusal:
        # "blocked — Gemini not connected" reads as a sentence on the card, which
        # is the whole reason that refusal carries prose rather than a code.
        raise PublicationRefused(str(refusal)) from refusal

    written: list[dict[str, Any]] = []
    for card in cards:
        prompt = image_gen.social_card_prompt(
            role=card.role,
            kicker=card.kicker,
            headline=card.headline,
            support=card.support,
            footer=card.footer,
        )
        try:
            generated = generator.generate(
                prompt, task_id=task_id, aspect_ratio=card.aspect_ratio
            )
        except image_gen.ImageGenRefused as refusal:
            # A budget refusal on card four leaves three paid-for cards on disk.
            # Reporting how far it got is the difference between "try again" and
            # "try again and pay for those three twice".
            raise PublicationRefused(
                f"{refusal} — {len(written)} of {len(cards)} cards were drawn before this"
            ) from refusal
        name = card.filename(slug)
        destination = content_flow._safe_artifact(profile_dir, name)
        content_flow._atomic_artifact_set({destination: generated.webp})
        written.append(
            {
                **card.as_dict(),
                "filename": name,
                "artifact": f"artifacts/{name}",
                "url": card_url(live_origin(), name),
            }
        )

    origin = live_origin()
    database = ConsoleDB(profile_dir)
    try:
        for platform in CROSSPOST_PLATFORMS:
            images = [
                {"url": card_url(origin, item["filename"]), "alt": item["alt_text"]}
                for item in written
                if item["platform"] == platform
            ]
            database.save_crosspost_images(
                task_id=task_id, platform=platform, images=images
            )
        stored = database.crosspost_drafts(task_id)
    finally:
        database.close()

    ceo_publish._append_log(
        profile_dir,
        {
            "event": "social-cards",
            "task_id": task_id,
            "actor": actor,
            "cards": [item["variant"] for item in written],
            "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    return {"task_id": task_id, "slug": slug, "cards": written, "drafts": stored}
