"""Publish an approved article to `cmo-changes`, and stop at the preview.

This is not Gate 2. `ceo_publish.py` is Gate 2 — it merges `cmo-changes` into
`main`, and nothing here can reach `main` by any path: the only branch name this
module will push to is the one constant below, and a test asserts on the argv of
every git call to prove it.

What this does is the step that had no button at all. `BlogPublisher` has been
able to turn an approved artifact into `page.tsx`, a `blog-posts.ts` entry and an
SVG for some time, and every one of those conversions was somebody running a
script by hand. This puts it behind a click, adds the commit and the push, and
records who asked in `approvals.log`.

Nothing here decides anything either. `preflight` reports whether a human *may*
be offered the instruction; `publish` executes one single-use instruction a human
has already given. The instruction ID can only be minted by a page render for an
authenticated human, and it is consumed before any of the work starts, so a replay
never reaches git.

See SOUL.md section 12 clause 4 for why the shape is this one.
"""

from __future__ import annotations

import re
import secrets
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import ceo_publish
from ceo_publish import PublicationConflict, PublicationRefused

#: The only branch this module will ever write to.
BRANCH = "cmo-changes"

#: The fixed Vercel preview `cmo-changes` deploys to. Not per-commit.
PREVIEW_ORIGIN = "https://itarangwebsite.vercel.app"

#: Where the website checkout lives on this box.
DEFAULT_WEBSITE_ROOT = "/opt/data/work/itarang-website"

GIT_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class BlogPreflight:
    task_id: str
    eligible: bool
    blockers: list[str] = field(default_factory=list)
    slug: str = ""
    category: str = ""
    branch: str = BRANCH
    head: str = ""
    preview_url: str = ""
    approver: str = ""
    files: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "eligible": self.eligible,
            "blockers": list(self.blockers),
            "slug": self.slug,
            "category": self.category,
            "branch": self.branch,
            "head": self.head,
            "preview_url": self.preview_url,
            "approver": self.approver,
            "files": list(self.files),
        }


class Git:
    """Every git call this module makes, in one place that can be recorded.

    A test asserts on `calls` that no invocation names `main`. That is only worth
    anything if there is no second way to run git from here — so there is not.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.calls: list[list[str]] = []

    def run(self, *arguments: str, check: bool = True) -> str:
        command = ["git", *arguments]
        self.calls.append(command)
        completed = subprocess.run(
            command,
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if check and completed.returncode != 0:
            detail = " ".join((completed.stderr or completed.stdout or "").split())[:500]
            raise PublicationRefused(f"git {arguments[0]} failed: {detail}")
        return completed.stdout.strip()

    def current_branch(self) -> str:
        return self.run("branch", "--show-current")

    def remote_head(self, branch: str) -> str:
        self.run("fetch", "origin", branch)
        return self.run("rev-parse", f"origin/{branch}")

    def head(self) -> str:
        return self.run("rev-parse", "HEAD")


def _artifact_category(profile_dir: Path, task: dict[str, Any]) -> str:
    import console_board

    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        return ""
    match = re.search(r"(?m)^category:\s*(.+?)\s*$", article.read_text(encoding="utf-8")[:4000])
    return match.group(1).strip() if match else ""


def preflight(
    profile_dir: str | Path,
    task_id: str,
    *,
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    git: Git | None = None,
    today: date | None = None,
) -> BlogPreflight:
    """Report whether a human may be offered the publish instruction, and why not.

    Every blocker is a separate sentence naming the thing that is wrong. A button
    that greys out without saying why is the same as no button.
    """
    import console_board
    from cmo_runtime import decisions
    from cmo_runtime.blog_publisher import BlogPublisher, BlogPublishRefused
    from cmo_runtime.content_flow import BLOG_CATEGORY_SLUGS

    profile_dir = Path(profile_dir)
    website_root = Path(website_root)
    board = console_board.read_board(profile_dir / "tasks.md", profile_dir)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        return BlogPreflight(task_id, False, [f"no such task: {task_id}"])

    blockers: list[str] = []

    record = decisions.decision_record(profile_dir, task_id)
    approved = bool(record and record.get("decision") == "approve")
    if not approved:
        blockers.append("no Gate 1 approval is recorded for this card")

    # What was approved, not merely that something was. An approval recorded
    # before fingerprinting carries none, and guessing that nothing has changed
    # since is exactly the guess this refuses to make.
    if approved:
        recorded = str(record.get("publish_fingerprint", "")).strip()
        if not recorded:
            blockers.append(
                "this approval predates publish verification, so what was approved "
                "cannot be confirmed; ask for a fresh Gate 1"
            )
        elif recorded != console_board.publish_fingerprint(task, profile_dir):
            blockers.append(
                "the article or its category changed after this card was approved; "
                "ask for a fresh Gate 1"
            )

    card_category = str(task.get("category", "")).strip()
    artifact_category = _artifact_category(profile_dir, task)
    for name, value in (("card", card_category), ("article front matter", artifact_category)):
        if not value:
            blockers.append(f"no category is recorded on the {name}")
        elif value not in BLOG_CATEGORY_SLUGS:
            blockers.append(
                f"the {name} category {value!r} is not one of the six allowed: "
                + ", ".join(sorted(BLOG_CATEGORY_SLUGS))
            )
    if card_category and artifact_category and card_category != artifact_category:
        blockers.append(
            f"the card says category {card_category!r} and the article says {artifact_category!r}"
        )

    publisher = BlogPublisher(profile_dir, website_root)
    slug = ""
    files: list[str] = []
    try:
        plan = publisher.preview(task_id, publication_date=today or datetime.now(UTC).date())
    except BlogPublishRefused as error:
        blockers.append(str(error))
    except (OSError, KeyError, ValueError) as error:
        blockers.append(f"the article could not be converted: {error}")
    else:
        slug = plan.slug
        files = [
            str(plan.page_path.relative_to(website_root)),
            "src/data/blog-posts.ts",
            str(plan.image_path.relative_to(website_root)),
        ]

    client = git or Git(website_root)
    head = ""
    try:
        branch = client.current_branch()
        if branch != BRANCH:
            blockers.append(f"the website checkout is on {branch or '<detached>'}, not {BRANCH}")
        dirty = client.run("status", "--porcelain", "--untracked-files=no")
        if dirty:
            blockers.append(
                "the website checkout has uncommitted tracked changes: " + dirty.replace("\n", "; ")
            )
        head = client.remote_head(BRANCH)
    except PublicationRefused as error:
        blockers.append(str(error))

    return BlogPreflight(
        task_id=task_id,
        eligible=not blockers,
        blockers=blockers,
        slug=slug,
        category=card_category,
        head=head,
        preview_url=f"{PREVIEW_ORIGIN}/blog/{slug}" if slug else "",
        approver=str(record.get("approver_id", "")) if record else "",
        files=files,
    )


def _requests_path(profile_dir: Path) -> Path:
    return profile_dir / "state" / "blog-publication-requests.json"


def issue_request(profile_dir: str | Path, task_id: str, *, actor: str, head: str) -> str:
    """Mint a single-use instruction ID. Only a human page render calls this."""
    profile_dir = Path(profile_dir)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a publish instruction requires an authenticated human")
    request_id = secrets.token_urlsafe(24)
    path = _requests_path(profile_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with ceo_publish._locked(profile_dir):
        pending = ceo_publish._read_json(path)
        pending[request_id] = {
            "task_id": task_id,
            "actor": actor,
            "head": head.lower(),
            "issued_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        ceo_publish._write_json(path, pending)
    return request_id


def publish(
    profile_dir: str | Path,
    task_id: str,
    *,
    actor: str,
    role: str,
    request_id: str,
    website_root: str | Path = DEFAULT_WEBSITE_ROOT,
    git: Git | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Execute one authenticated human's single-use instruction. Stops at the preview."""
    from cmo_runtime.blog_publisher import BlogPublisher, BlogPublishRefused
    from cmo_runtime.task_file import TaskFile

    profile_dir = Path(profile_dir)
    website_root = Path(website_root)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a publish instruction requires an authenticated human")

    # Consume the instruction before anything else, so a replay cannot even reach
    # the re-check, let alone the working tree.
    with ceo_publish._locked(profile_dir):
        path = _requests_path(profile_dir)
        pending = ceo_publish._read_json(path)
        instruction = pending.pop(request_id, None)
        if instruction is None:
            raise PublicationConflict("this publish instruction is unknown or already used")
        ceo_publish._write_json(path, pending)
    if instruction["task_id"] != task_id or instruction["actor"] != actor:
        raise PublicationConflict("this publish instruction was issued for a different human or card")

    client = git or Git(website_root)
    check = preflight(profile_dir, task_id, website_root=website_root, git=client, today=today)
    if not check.eligible:
        raise PublicationConflict("; ".join(check.blockers))
    if check.head != instruction["head"]:
        raise PublicationConflict(
            f"{BRANCH} moved after the instruction was issued: "
            f"{instruction['head'][:7]} → {check.head[:7]}"
        )

    publisher = BlogPublisher(profile_dir, website_root)
    publication_date = today or datetime.now(UTC).date()
    try:
        plan = publisher.apply(task_id, publication_date=publication_date)
    except BlogPublishRefused as error:
        raise PublicationRefused(str(error)) from error

    message = (
        f"Publish {task_id}: {plan.slug}\n\n"
        f"Adds the blog page, its blog-posts.ts entry and its diagram on {BRANCH}.\n"
        f"Gate 1 approved by {check.approver}.\n\n"
        f"Published-by: {actor}\n"
        f"Published-via: CEO console ({role})\n"
        f"Publication-request: {request_id}\n"
    )
    outcome: dict[str, Any] = {
        "event": "blog-publication",
        "task_id": task_id,
        "actor": actor,
        "role": role,
        "request_id": request_id,
        "branch": BRANCH,
        "slug": plan.slug,
        "category": plan.category,
        "files": check.files,
        "observed_head": check.head,
        "preview_url": f"{PREVIEW_ORIGIN}/blog/{plan.slug}",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        # Exactly the three files this publish produced, by name. `git add -A`
        # here would sweep up whatever else is lying in the worktree and push it
        # under a commit message about a blog post.
        client.run("add", "--", *check.files)
        client.run("-c", f"user.name=iTarang CMO", "-c", "user.email=it@itarang.com",
                   "commit", "-m", message)
        commit = client.head()
        # Fails rather than forces if the remote moved between the re-check and
        # here. Nothing local is pushed on a lease failure.
        client.run("push", "--force-with-lease=" + f"{BRANCH}:{check.head}", "origin",
                   f"HEAD:refs/heads/{BRANCH}")
    except PublicationRefused as error:
        # Put the worktree back exactly as it was. A half-applied publish is worse
        # than none: the next attempt would refuse on "blog page already exists".
        client.run("reset", "--hard", check.head, check=False)
        client.run("clean", "-fd", "--", "src/app/(marketing)/blog", "public/images/blog", check=False)
        outcome.update({"result": "refused", "reason": str(error)})
        ceo_publish._append_log(profile_dir, outcome)
        raise

    outcome.update({"result": "pushed", "commit": commit})
    ceo_publish._append_log(profile_dir, outcome)

    TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {
            "Change status": "published to cmo-changes",
            "Branch": BRANCH,
            "Commit hash(es)": commit,
            "Preview URL": outcome["preview_url"],
            "Published by": actor,
            "Published at": outcome["timestamp"],
            "Latest summary": (
                f"Published to {BRANCH} at {commit[:7]} by {actor}; awaiting a human merge to main."
            ),
        },
    )
    return outcome
