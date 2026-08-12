"""Publishing an article to `cmo-changes`, and the four refusals that matter.

There is no mock git here. Each test stands up a real bare repository as
`origin`, a real clone on `cmo-changes` with a real `main`, and lets the publish
path run `git` for real. The reason is the invariant: "publishing pushes to
`cmo-changes` and never to `main`" is a claim about what happened to a repository,
and a fake that records argv can only tell you what was *asked for*. Here, after a
publish, `main` is read back out of `origin` and compared to what it was.

The refusals are tested one at a time, from an otherwise-publishable card, so each
test names exactly one reason a human is not offered the button.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

import ceo_blog_publish
import console_board
from ceo_blog_publish import PublicationConflict, PublicationRefused
from cmo_runtime.decisions import DecisionConflict, DecisionStore

BLOG_POSTS = """export type BlogCategorySlug =
  | "financing"
  | "battery-selection"
  | "charging-maintenance"
  | "safety"
  | "lifecycle-recycling"
  | "partners-industry";

export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: BlogCategorySlug;
  coverImage?: string;
}

export const blogPosts: BlogPost[] = [
];
"""

ARTICLE = """---
title: A useful finance guide
meta_title: Useful Finance Guide for EV Owners
meta_description: A concise description copied exactly into the blog index.
slug: useful-finance-guide
category: financing
audience: EV owners
source_urls: https://example.org/source
---

# A useful finance guide

A useful introduction with **strong evidence** and a [dated source](https://example.org/source).

{{image:decision-flow|How a reader moves from a question to a verified next step.}}

## What to check

- Confirm the vehicle details.
- Confirm the available finance terms.
"""

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">
<title>EV finance decision flow</title><desc>A reader verifies each decision input.</desc>
<rect width="1000" height="560" fill="#fff"/>
</svg>
"""


def _card(category: str = "financing") -> str:
    lines = [
        "### TASK-900 — A useful finance guide",
        "- ID: TASK-900",
        "- Title: A useful finance guide",
        "- Owner: content",
        "- Skill: content",
        "- Priority: medium",
        "- Status: Human Approval",
        "- Attachment: artifacts/TASK-900-content.md",
        "- Image slot decision-flow: artifacts/TASK-900-decision-flow.svg",
        "- Change type: website",
        "- Metric: Organic sessions",
        "- Tag: action to be taken by: human",
        "- Revision round: 0",
        "- Completed date: not completed",
        "- Last updated: 2026-08-11T00:00:00Z",
        "- Updated: 2026-08-11T00:00:00Z",
    ]
    if category:
        lines.insert(9, f"- Category: {category}")
    return "\n".join(lines) + "\n"


def _board(card: str) -> str:
    return (
        "# CMO Task Board\n\n## Backlog\n\n_No tasks._\n\n## In Progress\n\n_No tasks._\n\n"
        "## CMO Review\n\n_No tasks._\n\n## Human Approval\n\n" + card + "\n## Completed\n\n_No tasks._\n"
    )


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=str(root), capture_output=True, text=True, check=True
    ).stdout.strip()


class PublishFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)

        self.profile = root / "profile"
        (self.profile / "artifacts").mkdir(parents=True)
        (self.profile / "state").mkdir()
        (self.profile / "logs").mkdir()
        (self.profile / "tasks.md").write_text(_board(_card()), encoding="utf-8")
        (self.profile / "artifacts/TASK-900-content.md").write_text(ARTICLE, encoding="utf-8")
        (self.profile / "artifacts/TASK-900-decision-flow.svg").write_text(SVG, encoding="utf-8")

        # A real origin, a real main, and a real cmo-changes checked out.
        self.origin = root / "origin.git"
        git(root, "init", "--bare", "-b", "main", str(self.origin))
        self.website = root / "website"
        self.website.mkdir()
        git(self.website, "init", "-b", "main")
        git(self.website, "config", "user.email", "test@itarang.test")
        git(self.website, "config", "user.name", "test")
        git(self.website, "remote", "add", "origin", str(self.origin))
        for relative in ("src/data", "src/app/(marketing)/blog", "public/images/blog"):
            (self.website / relative).mkdir(parents=True, exist_ok=True)
        (self.website / "src/data/blog-posts.ts").write_text(BLOG_POSTS, encoding="utf-8")
        (self.website / "public/images/blog/.keep").write_text("", encoding="utf-8")
        git(self.website, "add", "-A")
        git(self.website, "commit", "-m", "the site as it stands")
        git(self.website, "push", "origin", "main")
        git(self.website, "checkout", "-b", "cmo-changes")
        git(self.website, "push", "-u", "origin", "cmo-changes")
        self.main_before = git(self.website, "rev-parse", "origin/main")

    # ---- helpers ---------------------------------------------------------

    def task(self) -> dict:
        board = console_board.read_board(self.profile / "tasks.md", self.profile)
        return next(item for item in board["tasks"] if item["id"] == "TASK-900")

    def approve(self, *, fingerprint: str | None = None) -> None:
        """Record Gate 1 exactly as the console does, via the only approval writer."""
        task = self.task()
        recorded = console_board.publish_fingerprint(task, self.profile) if fingerprint is None else fingerprint
        DecisionStore(self.profile).decide(
            "TASK-900",
            "approve",
            approver_id="ceo@itarang.test",
            surface="dashboard",
            publish_fingerprint=recorded,
            components=console_board.publish_component_record(task, self.profile),
        )

    def preflight(self) -> ceo_blog_publish.BlogPreflight:
        return ceo_blog_publish.preflight(
            self.profile, "TASK-900", website_root=self.website, today=date(2026, 8, 12)
        )

    def publish(self, request_id: str | None = None) -> dict:
        check = self.preflight()
        if request_id is None:
            request_id = ceo_blog_publish.issue_request(
                self.profile, "TASK-900", actor="ceo@itarang.test", head=check.head
            )
        return ceo_blog_publish.publish(
            self.profile,
            "TASK-900",
            actor="ceo@itarang.test",
            role="ceo",
            request_id=request_id,
            website_root=self.website,
            today=date(2026, 8, 12),
        )

    def log_events(self) -> list[dict]:
        path = self.profile / "logs" / "approvals.log"
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TheClickDoesAllOfIt(PublishFixture):
    def test_a_publish_writes_all_three_files_and_pushes_them(self) -> None:
        self.approve()

        outcome = self.publish()

        self.assertEqual(outcome["result"], "pushed")
        self.assertEqual(outcome["branch"], "cmo-changes")
        pushed = git(self.website, "show", "--stat", "--name-only", "--format=", "origin/cmo-changes")
        self.assertIn("src/app/(marketing)/blog/useful-finance-guide/page.tsx", pushed)
        self.assertIn("src/data/blog-posts.ts", pushed)
        self.assertIn("public/images/blog/useful-finance-guide.svg", pushed)

    def test_the_blog_index_entry_is_added_not_only_the_page(self) -> None:
        """Without it the post is absent from /blog and from its category page."""
        self.approve()
        self.publish()

        index = git(self.website, "show", "origin/cmo-changes:src/data/blog-posts.ts")
        self.assertIn('slug: "useful-finance-guide"', index)
        self.assertIn('category: "financing"', index)

    def test_the_marker_becomes_real_jsx_and_the_svg_is_copied(self) -> None:
        self.approve()
        self.publish()

        page = git(self.website, "show",
                   "origin/cmo-changes:src/app/(marketing)/blog/useful-finance-guide/page.tsx")
        self.assertNotIn("{{image:", page, "the image marker was published verbatim")
        self.assertIn("/images/blog/useful-finance-guide.svg", page)
        self.assertIn("EV finance decision flow", page, "the SVG title is not the image alt text")

    def test_the_card_carries_the_preview_url_afterwards(self) -> None:
        self.approve()

        outcome = self.publish()

        self.assertEqual(
            outcome["preview_url"], "https://itarangwebsite.vercel.app/blog/useful-finance-guide"
        )
        task = self.task()
        self.assertEqual(task["preview_url"], outcome["preview_url"])
        self.assertEqual(task["change_status"], "published to cmo-changes")
        self.assertEqual(task["commit_hash(es)"], outcome["commit"])
        self.assertEqual(console_board.blog_state(task)["state"], "published")
        self.assertEqual(console_board.blog_state(task)["url"], outcome["preview_url"])

    def test_the_publication_is_recorded_with_who_clicked_and_which_commit(self) -> None:
        self.approve()

        outcome = self.publish()

        event = self.log_events()[-1]
        self.assertEqual(event["event"], "blog-publication")
        self.assertEqual(event["actor"], "ceo@itarang.test")
        self.assertEqual(event["result"], "pushed")
        self.assertEqual(event["commit"], outcome["commit"])
        self.assertTrue(event["timestamp"])

    def test_the_commit_message_names_the_human_who_clicked(self) -> None:
        self.approve()
        self.publish()

        message = git(self.website, "log", "-1", "--format=%B", "origin/cmo-changes")
        self.assertIn("Published-by: ceo@itarang.test", message)
        self.assertIn("Gate 1 approved by ceo@itarang.test", message)


class ItNeverReachesMain(PublishFixture):
    """Invariant 8, read back out of the repository rather than off an argv list."""

    def test_main_is_byte_identical_after_a_publish(self) -> None:
        self.approve()

        self.publish()

        self.assertEqual(git(self.website, "rev-parse", "origin/main"), self.main_before)
        self.assertNotEqual(git(self.website, "rev-parse", "origin/cmo-changes"), self.main_before)

    def test_the_published_page_does_not_exist_on_main(self) -> None:
        self.approve()
        self.publish()

        listing = git(self.website, "ls-tree", "-r", "--name-only", "origin/main")
        self.assertNotIn("useful-finance-guide", listing)

    def test_no_git_invocation_names_main(self) -> None:
        self.approve()
        client = ceo_blog_publish.Git(self.website)
        check = ceo_blog_publish.preflight(
            self.profile, "TASK-900", website_root=self.website, git=client, today=date(2026, 8, 12)
        )
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test", head=check.head
        )

        ceo_blog_publish.publish(
            self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
            request_id=request_id, website_root=self.website, git=client, today=date(2026, 8, 12),
        )

        for call in client.calls:
            self.assertNotIn("main", call, f"a git call named main: {call}")


class ItRefusesForOneNamedReasonAtATime(PublishFixture):
    def test_without_a_gate_one_approval_it_cannot_publish(self) -> None:
        check = self.preflight()

        self.assertFalse(check.eligible)
        self.assertIn("no Gate 1 approval is recorded for this card", check.blockers)

    def test_without_a_gate_one_approval_the_publish_call_itself_refuses(self) -> None:
        """The button is not the guard. Calling past it must fail the same way."""
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test", head="deadbeef"
        )

        with self.assertRaises(PublicationConflict) as raised:
            self.publish(request_id)

        self.assertIn("no Gate 1 approval", str(raised.exception))
        self.assertEqual(git(self.website, "rev-parse", "origin/main"), self.main_before)

    def test_a_missing_category_refuses_with_the_reason(self) -> None:
        (self.profile / "tasks.md").write_text(_board(_card(category="")), encoding="utf-8")
        self.approve()

        check = self.preflight()

        self.assertFalse(check.eligible)
        self.assertIn("no category is recorded on the card", check.blockers)

    def test_a_category_outside_the_six_refuses_and_names_them(self) -> None:
        (self.profile / "tasks.md").write_text(_board(_card(category="opinion")), encoding="utf-8")
        self.approve()

        check = self.preflight()

        self.assertFalse(check.eligible)
        blocker = next(reason for reason in check.blockers if "opinion" in reason)
        self.assertIn("not one of the six allowed", blocker)
        self.assertIn("charging-maintenance", blocker)

    def test_an_article_edited_after_approval_refuses(self) -> None:
        """Invariant 7's third case: approved has to mean approved *of this*."""
        self.approve()
        self.assertTrue(self.preflight().eligible)

        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE + "\nA paragraph nobody approved.\n", encoding="utf-8"
        )

        check = self.preflight()
        self.assertFalse(check.eligible)
        self.assertIn("changed after this card was approved", " ".join(check.blockers))

    def test_an_approval_recorded_before_fingerprinting_refuses(self) -> None:
        """Records written before fingerprinting existed, as they sit on disk.

        `decide()` will no longer produce one of these — a website card with no
        commit must carry a fingerprint — but the ones already written do not
        vanish, and publish has to fail closed against them rather than assume the
        card is unchanged.
        """
        self.approve()
        approvals = self.profile / "state" / "human-approvals.json"
        record = json.loads(approvals.read_text(encoding="utf-8"))
        del record["TASK-900"]["publish_fingerprint"]
        approvals.write_text(json.dumps(record, indent=2), encoding="utf-8")

        check = self.preflight()

        self.assertFalse(check.eligible)
        self.assertIn("predates publish verification", " ".join(check.blockers))

    def test_a_checkout_on_the_wrong_branch_refuses(self) -> None:
        self.approve()
        git(self.website, "checkout", "main")

        check = self.preflight()

        self.assertFalse(check.eligible)
        self.assertIn("not cmo-changes", " ".join(check.blockers))


class ABlogIsAWebsiteChange(PublishFixture):
    """The classification that decides whether approval is Gate 1 or completion.

    A blog post adds a route, an entry in the post registry and a sitemap URL. It
    was reaching `DecisionStore` with no `Change type` at all, so approval took the
    non-website branch: straight to Completed with `Change status: completed`, past
    the publish step entirely, and the button then had no card to act on.
    """

    def section_of(self, task_id: str) -> str:
        from cmo_runtime.agent_runtime import BoardStore

        return BoardStore(self.profile).get(task_id).section

    def field(self, task_id: str, name: str) -> str:
        from cmo_runtime.agent_runtime import BoardStore

        return BoardStore(self.profile).get(task_id).fields.get(name, "")

    def test_the_writer_marks_a_finished_article_as_a_website_change(self) -> None:
        """Classified where the artifact is made, not guessed at later."""
        import inspect

        from cmo_runtime.content_flow import ContentRuntime

        source = inspect.getsource(ContentRuntime.execute)
        self.assertIn('"Change type": "website"', source)

    def test_approving_a_blog_card_leaves_it_in_human_approval(self) -> None:
        self.approve()

        self.assertEqual(self.section_of("TASK-900"), "Human Approval")
        self.assertEqual(self.field("TASK-900", "Change status"), "awaiting Gate 2")

    def test_approving_a_blog_card_turns_the_publish_button_on(self) -> None:
        self.assertFalse(self.preflight().eligible)

        self.approve()

        check = self.preflight()
        self.assertTrue(check.eligible, check.blockers)
        self.assertEqual(check.slug, "useful-finance-guide")

    def test_approval_alone_never_reaches_completed(self) -> None:
        self.approve()

        self.assertNotEqual(self.section_of("TASK-900"), "Completed")
        self.assertEqual(self.field("TASK-900", "Completed date"), "not completed")

    def test_publishing_does_not_complete_the_card_either(self) -> None:
        """Completed waits for the merge and live evidence, neither of which we do."""
        self.approve()

        self.publish()

        self.assertEqual(self.section_of("TASK-900"), "Human Approval")
        self.assertEqual(self.field("TASK-900", "Change status"), "published to cmo-changes")
        self.assertEqual(self.field("TASK-900", "Completed date"), "not completed")

    def test_a_website_card_with_no_commit_needs_a_fingerprint_to_be_approved(self) -> None:
        """A blog card is approved before it has a commit, so something else pins it.

        The old rule demanded commit SHAs from every website card, which no blog
        card can supply at Gate 1. Dropping the rule outright would let a website
        card be approved with nothing recording what was approved.
        """
        from cmo_runtime.decisions import DecisionConflict, DecisionStore, DecisionValidationError

        with self.assertRaises(DecisionValidationError) as raised:
            DecisionStore(self.profile).decide(
                "TASK-900", "approve", approver_id="ceo@itarang.test", surface="dashboard",
            )

        self.assertIn("publish fingerprint", str(raised.exception))
        self.assertEqual(self.section_of("TASK-900"), "Human Approval")


class AStaleApprovalCanBeGivenAgain(PublishFixture):
    """The deadlock, and the way out of it.

    A card carried Gate 1 from 09:58. Its article changed afterwards, so publish
    refused on the stale fingerprint and asked for a fresh Gate 1 — while
    `DecisionStore` allowed one decision per card and the console offered no way to
    give another. Three correct rules with no state transition between them.

    The way out is not a looser fingerprint. The fingerprint caught a real change
    to an approved artifact and is what grants the second decision: a card whose
    digest still matches is decided, and stays decided.
    """

    def approvals(self) -> dict:
        return json.loads((self.profile / "state" / "human-approvals.json").read_text(encoding="utf-8"))

    def change_the_article(self) -> None:
        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE.replace("A useful introduction", "A rather better introduction"),
            encoding="utf-8",
        )

    def reapprove(self) -> None:
        self.approve()

    def test_a_decision_that_still_covers_the_article_is_not_re_openable(self) -> None:
        """The rule that stands: one decision per card, first writer wins."""
        self.approve()

        with self.assertRaises(DecisionConflict) as raised:
            self.approve()

        self.assertIn("already decided", str(raised.exception))

    def test_a_changed_article_makes_the_card_re_approvable(self) -> None:
        self.approve()
        self.assertFalse(console_board.read_board(self.profile / "tasks.md", self.profile)["tasks"][0]["decision_stale"])

        self.change_the_article()

        task = self.task()
        self.assertTrue(task["decision_stale"])
        self.assertEqual(task["decision_status"], "approval out of date")
        self.assertIn("the article changed", " ".join(task["decision_change"]))

    def test_the_new_decision_supersedes_the_old_and_keeps_it(self) -> None:
        self.approve()
        first = self.approvals()["TASK-900"]
        self.change_the_article()

        self.reapprove()

        current = self.approvals()["TASK-900"]
        self.assertNotEqual(current["publish_fingerprint"], first["publish_fingerprint"])
        self.assertEqual(current["supersedes_timestamp"], first["timestamp"])
        self.assertEqual(current["supersedes_fingerprint"], first["publish_fingerprint"])
        self.assertEqual(current["supersedes_count"], "1")

    def test_the_superseded_decision_survives_in_the_log(self) -> None:
        """Nothing is overwritten; the log gains lines."""
        self.approve()
        first = self.approvals()["TASK-900"]
        self.change_the_article()

        self.reapprove()

        events = self.log_events()
        superseded = [event for event in events if event.get("outcome") == "superseded"]
        recorded = [event for event in events if event.get("outcome") == "recorded"]
        self.assertEqual(len(superseded), 1)
        self.assertEqual(len(recorded), 2, "the original approval was rewritten rather than kept")
        self.assertEqual(superseded[0]["timestamp"], first["timestamp"])
        self.assertEqual(superseded[0]["publish_fingerprint"], first["publish_fingerprint"])
        self.assertIn("the approved artifact changed", superseded[0]["reason"])
        # Order matters: the decision being replaced is written before the one
        # replacing it, so the log reads forwards.
        self.assertLess(events.index(superseded[0]), events.index(recorded[-1]))

    def test_the_card_carries_the_superseded_decision_too(self) -> None:
        from cmo_runtime.agent_runtime import BoardStore

        self.approve()
        self.change_the_article()
        self.reapprove()

        card = BoardStore(self.profile).get("TASK-900")
        note = card.fields.get("Superseded decision 1", "")
        self.assertIn("ceo@itarang.test", note)
        self.assertIn("the approved artifact changed", note)
        self.assertEqual(card.fields.get("Human decision by"), "ceo@itarang.test")

    def test_publish_then_proceeds_on_the_new_fingerprint(self) -> None:
        """The whole point, end to end, against a real repository."""
        self.approve()
        self.change_the_article()
        self.assertFalse(self.preflight().eligible)

        self.reapprove()

        check = self.preflight()
        self.assertTrue(check.eligible, check.blockers)
        outcome = self.publish()
        self.assertEqual(outcome["result"], "pushed")
        self.assertEqual(git(self.website, "rev-parse", "origin/main"), self.main_before)
        page = git(self.website, "show",
                   "origin/cmo-changes:src/app/(marketing)/blog/useful-finance-guide/page.tsx")
        self.assertIn("A rather better introduction", page, "the old article was published")

    def test_a_change_after_the_second_approval_makes_it_stale_again(self) -> None:
        """The guard is not spent by being used once."""
        self.approve()
        self.change_the_article()
        self.reapprove()
        self.assertTrue(self.preflight().eligible)

        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE.replace("A useful introduction", "A third introduction"), encoding="utf-8"
        )

        self.assertFalse(self.preflight().eligible)
        self.assertTrue(self.task()["decision_stale"])

    def test_a_record_with_no_fingerprint_stays_shut(self) -> None:
        """Nothing can tell stale from unchanged there, so it is not guessed at."""
        self.approve()
        approvals = self.profile / "state" / "human-approvals.json"
        record = json.loads(approvals.read_text(encoding="utf-8"))
        del record["TASK-900"]["publish_fingerprint"]
        approvals.write_text(json.dumps(record, indent=2), encoding="utf-8")
        self.change_the_article()

        self.assertFalse(self.task()["decision_stale"])
        with self.assertRaises(DecisionConflict) as raised:
            self.approve()
        self.assertIn("already decided", str(raised.exception))


class RepublishingItsOwnPage(PublishFixture):
    """The converter is code. Code gets fixed, and the fix has to reach the page.

    Publishing over somebody else's page stays refused. Publishing over the page
    this card published is a republish — otherwise a converter bug is permanent
    for every article that already went out, or gets a second slug for the same
    post.
    """

    def test_a_second_publish_of_the_same_card_replaces_its_page(self) -> None:
        self.approve()
        self.publish()

        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE.replace("A useful introduction", "A corrected introduction"), encoding="utf-8"
        )
        self.approve()  # the artifact moved, so Gate 1 is given again
        outcome = self.publish()

        self.assertEqual(outcome["result"], "pushed")
        page = git(self.website, "show",
                   "origin/cmo-changes:src/app/(marketing)/blog/useful-finance-guide/page.tsx")
        self.assertIn("A corrected introduction", page)
        self.assertNotIn("A useful introduction", page)

    def test_the_post_is_listed_once_not_twice(self) -> None:
        self.approve()
        self.publish()
        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE.replace("A useful introduction", "A corrected introduction"), encoding="utf-8"
        )
        self.approve()
        self.publish()

        index = git(self.website, "show", "origin/cmo-changes:src/data/blog-posts.ts")
        self.assertEqual(index.count('slug: "useful-finance-guide"'), 1)

    def test_publishing_over_a_page_this_card_did_not_publish_is_refused(self) -> None:
        from cmo_runtime.blog_publisher import BlogPublisher, BlogPublishRefused

        page = self.website / "src/app/(marketing)/blog/useful-finance-guide/page.tsx"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("somebody else's article\n", encoding="utf-8")

        with self.assertRaises(BlogPublishRefused) as raised:
            BlogPublisher(self.profile, self.website).preview(
                "TASK-900", publication_date=date(2026, 8, 12)
            )

        self.assertIn("already exists", str(raised.exception))
        self.assertEqual(page.read_text(encoding="utf-8"), "somebody else's article\n")


class ReviewScaffoldingNeverReachesThePage(PublishFixture):
    """It did. `Decision bullets:` was published under its own heading."""

    def publish_with_scaffolding(self) -> str:
        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE + """
## Decision bullets:

- Measure before commissioning more pages.
- Check the finance terms.

## Closing

A closing paragraph. Claims requiring human verification before publication: the finance terms.

Proposed internal links: the Battery Passport article. Source notes: retained pages were accessed on 2026-08-11.
""",
            encoding="utf-8",
        )
        self.approve()
        self.publish()
        return git(self.website, "show",
                   "origin/cmo-changes:src/app/(marketing)/blog/useful-finance-guide/page.tsx")

    def test_no_scaffolding_label_survives_to_the_page(self) -> None:
        page = self.publish_with_scaffolding()

        for phrase in ("Decision bullets", "Claims requiring human verification",
                       "Proposed internal links", "Source notes", "accessed on 2026-08-11"):
            self.assertNotIn(phrase, page, phrase)

    def test_the_article_around_it_still_publishes(self) -> None:
        page = self.publish_with_scaffolding()

        self.assertIn("A closing paragraph.", page)
        self.assertIn("<h2>Closing</h2>", page)
        self.assertIn("<h2>What to check</h2>", page)


class TheConverterEmitsRealElements(PublishFixture):
    """<h2>, <p>, <ul>/<li>, <table> — never a styled span."""

    def page(self) -> str:
        (self.profile / "artifacts/TASK-900-content.md").write_text(
            ARTICLE + """
### A subsection

| City | Price |
|---|---:|
| Delhi | 12,000 |
""",
            encoding="utf-8",
        )
        self.approve()
        self.publish()
        return git(self.website, "show",
                   "origin/cmo-changes:src/app/(marketing)/blog/useful-finance-guide/page.tsx")

    def test_every_structure_is_a_real_element(self) -> None:
        page = self.page()

        self.assertIn("<h2>What to check</h2>", page)
        self.assertIn("<h3>A subsection</h3>", page)
        self.assertIn("<p>", page)
        self.assertIn("<ul>", page)
        self.assertIn("<li>", page)
        self.assertIn("<table>", page)
        self.assertIn("<figure", page)
        self.assertIn("<figcaption>", page)

    def test_no_heading_is_emitted_as_styled_inline_text(self) -> None:
        page = self.page()

        self.assertNotIn("<span className=", page)
        self.assertNotIn("<b>", page)
        self.assertNotIn("<div>What to check</div>", page)


class NoAgentPathCanPublish(PublishFixture):
    """The instruction is the authority, and only a human page render mints one."""

    def test_publish_without_a_request_id_refuses_before_touching_git(self) -> None:
        self.approve()
        head_before = git(self.website, "rev-parse", "origin/cmo-changes")

        with self.assertRaises(PublicationConflict) as raised:
            ceo_blog_publish.publish(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id="", website_root=self.website, today=date(2026, 8, 12),
            )

        self.assertIn("unknown or already used", str(raised.exception))
        self.assertEqual(git(self.website, "rev-parse", "origin/cmo-changes"), head_before)

    def test_an_instruction_is_single_use(self) -> None:
        self.approve()
        check = self.preflight()
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test", head=check.head
        )
        self.publish(request_id)

        with self.assertRaises(PublicationConflict):
            self.publish(request_id)

    def test_an_instruction_issued_for_another_human_is_refused(self) -> None:
        self.approve()
        check = self.preflight()
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="someone.else@itarang.test", head=check.head
        )

        with self.assertRaises(PublicationConflict) as raised:
            self.publish(request_id)

        self.assertIn("different human or card", str(raised.exception))

    def test_issuing_an_instruction_without_an_authenticated_human_refuses(self) -> None:
        with self.assertRaises(PublicationRefused):
            ceo_blog_publish.issue_request(self.profile, "TASK-900", actor="  ", head="abc")


class AMovedBranchHeadIsAConflict(PublishFixture):
    def test_a_head_that_moved_after_the_instruction_pushes_nothing(self) -> None:
        self.approve()
        check = self.preflight()
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test", head=check.head
        )

        # Somebody else pushes to cmo-changes in the meantime.
        other = self.website.parent / "other"
        git(self.website.parent, "clone", str(self.origin), str(other))
        git(other, "config", "user.email", "other@itarang.test")
        git(other, "config", "user.name", "other")
        git(other, "checkout", "cmo-changes")
        (other / "README.md").write_text("someone else was here\n", encoding="utf-8")
        git(other, "add", "-A")
        git(other, "commit", "-m", "unrelated work")
        git(other, "push", "origin", "cmo-changes")
        moved = git(other, "rev-parse", "HEAD")

        with self.assertRaises(PublicationConflict) as raised:
            ceo_blog_publish.publish(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id=request_id, website_root=self.website, today=date(2026, 8, 12),
            )

        self.assertIn("moved after the instruction was issued", str(raised.exception))
        self.assertEqual(git(self.website, "rev-parse", "origin/cmo-changes"), moved,
                         "the other person's commit was overwritten")
        self.assertEqual(git(self.website, "rev-parse", "origin/main"), self.main_before)

    def test_the_conflict_leaves_nothing_half_written_in_the_worktree(self) -> None:
        self.approve()
        check = self.preflight()
        request_id = ceo_blog_publish.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test", head=check.head
        )
        other = self.website.parent / "other"
        git(self.website.parent, "clone", str(self.origin), str(other))
        git(other, "config", "user.email", "other@itarang.test")
        git(other, "config", "user.name", "other")
        git(other, "checkout", "cmo-changes")
        (other / "README.md").write_text("someone else was here\n", encoding="utf-8")
        git(other, "add", "-A")
        git(other, "commit", "-m", "unrelated work")
        git(other, "push", "origin", "cmo-changes")

        with self.assertRaises(PublicationConflict):
            ceo_blog_publish.publish(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id=request_id, website_root=self.website, today=date(2026, 8, 12),
            )

        self.assertFalse(
            (self.website / "src/app/(marketing)/blog/useful-finance-guide/page.tsx").exists(),
            "a refused publish left the page behind, so the next attempt would refuse too",
        )
        self.assertEqual(git(self.website, "status", "--porcelain", "--untracked-files=no"), "")


if __name__ == "__main__":
    unittest.main()
