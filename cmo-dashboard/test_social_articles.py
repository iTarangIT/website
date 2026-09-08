"""The Social tab lists the articles the *site* publishes, not the cards that wrote them.

The tab used to read task cards whose board state said `published`. On the real
board that produced five rows: two end-to-end fixtures, a landing-page brief, and
two articles -- and none of the nine articles a reader can actually open. The two
that are live on the site today were written by hand and never had a card at all.

So the fixtures here are deliberately awkward in the ways the real checkout is:
an article with no card, an article whose page exists but whose registry entry a
publish commit deleted, and a registry that is not in date order.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import blog_registry
import ceo_console
import ceo_social
from cmo_runtime.console_db import ConsoleDB

REGISTRY = '''export interface BlogPost {
  slug: string;
  title: string;
}

export const blogCategories: BlogCategory[] = [
  { name: "Financing", slug: "financing", description: "Battery price and EMI." },
];

export const blogPosts: BlogPost[] = [
  {
    slug: "battery-replacement-cost",
    title: "What an e-rickshaw battery costs to replace",
    excerpt:
      "A replacement pack is rarely the whole bill.",
    date: "2026-08-12",
    readTime: "6 min read",
    category: "financing",
    coverImage: "/images/blog/battery-replacement-cost-cover.svg",
  },
  {
    slug: "charging-at-home",
    title: "Charging an e-rickshaw at home",
    excerpt: "What a shared meter changes.",
    date: "2026-08-20",
    readTime: "4 min read",
    category: "charging-maintenance",
  },
];
'''

PAGE = '''import {{ createMetadata }} from "@/lib/metadata";
import BlogLayout from "@/components/blog/BlogLayout";

export const metadata = createMetadata({{
  title: "{title}",
  description: "{description}",
  path: "/blog/{slug}",
}});

export default function Article() {{
  return (
    <BlogLayout
      title="{title}"
      slug="{slug}"
      date="{date}"
      readTime="6 min read"
      category="{category}"
    >
      <p>
        A replacement pack is rarely the whole bill. Labour and downtime move the
        number by a third, and operators who budget for the pack alone borrow twice.
      </p>
      <h2>What the bill actually contains</h2>
      <p>Fitment, the controller check, and a day off the road. Let&apos;s count it.</p>
    </BlogLayout>
  );
}}
'''


def checkout(root: Path, *, registry: str = REGISTRY, pages: tuple[str, ...] = ()) -> Path:
    """A website checkout shaped like the real one, without being a git clone."""
    (root / "src" / "data").mkdir(parents=True, exist_ok=True)
    (root / "src" / "data" / "blog-posts.ts").write_text(registry, encoding="utf-8")
    for slug in pages:
        directory = root / "src" / "app" / "(marketing)" / "blog" / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "page.tsx").write_text(
            PAGE.format(
                title=f"Article {slug}",
                description=f"What {slug} is about.",
                slug=slug,
                date="2026-07-01",
                category="financing",
            ),
            encoding="utf-8",
        )
    return root


class TheRegistryReader(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.root, True)

    def test_every_registry_entry_is_a_post_and_the_categories_are_not(self):
        """`blogCategories` has a `slug:` on every line and is not an article."""
        posts = blog_registry.posts(checkout(self.root))
        self.assertEqual(
            [post.slug for post in posts],
            ["charging-at-home", "battery-replacement-cost"],
            "newest first, by the date the post carries",
        )

    def test_a_page_the_registry_forgot_is_still_a_published_article(self):
        """Commit 430c3c6 deleted four entries whose pages kept answering.

        A reader can open the URL, so the article is promotable. Obeying the
        registry here is how those four fell off the console for a month.
        """
        posts = blog_registry.posts(checkout(self.root, pages=("informal-financing",)))
        forgotten = next(post for post in posts if post.slug == "informal-financing")
        self.assertFalse(forgotten.listed, "the registry does not carry it")
        self.assertEqual(forgotten.title, "Article informal-financing", "read off its page")

    def test_an_unreadable_checkout_yields_nothing_rather_than_raising(self):
        self.assertEqual(blog_registry.posts(self.root / "nowhere"), [])

    def test_the_article_text_is_the_prose_and_never_the_markup(self):
        root = checkout(self.root, pages=("battery-replacement-cost",))
        post = blog_registry.find(root, "battery-replacement-cost")
        markdown = blog_registry.article_markdown(root, post)

        self.assertIn("slug: battery-replacement-cost", markdown)
        self.assertIn("Labour and downtime move the", markdown)
        self.assertIn("## What the bill actually contains", markdown)
        self.assertIn("Let's count it.", markdown, "entities are decoded")
        self.assertNotIn("<p>", markdown)
        self.assertNotIn("BlogLayout", markdown)
        self.assertNotIn("className", markdown)

    def test_the_fingerprint_moves_when_the_article_does(self):
        """`send` refuses an instruction whose article changed under it."""
        root = checkout(self.root, pages=("battery-replacement-cost",))
        post = blog_registry.find(root, "battery-replacement-cost")
        before = blog_registry.fingerprint(root, post)

        page = root / "src" / "app" / "(marketing)" / "blog" / "battery-replacement-cost" / "page.tsx"
        page.write_text(page.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        self.assertNotEqual(before, blog_registry.fingerprint(root, post))


class TheTabLists(unittest.TestCase):
    """What `social_payload` puts on the screen, against a real database."""

    def setUp(self) -> None:
        self.profile = Path(tempfile.mkdtemp())
        self.root = checkout(Path(tempfile.mkdtemp()), pages=("informal-financing",))
        self.addCleanup(__import__("shutil").rmtree, self.profile, True)
        self.addCleanup(__import__("shutil").rmtree, self.root, True)
        (self.profile / "tasks.md").write_text("# CMO Task Board\n", encoding="utf-8")
        patches = [
            mock.patch.object(ceo_console, "PROFILE_DIR", self.profile),
            mock.patch.object(ceo_social, "DEFAULT_WEBSITE_ROOT", str(self.root)),
            mock.patch.object(ceo_social.BufferClient, "configured", staticmethod(lambda _: True)),
            mock.patch.object(ceo_social, "live_origin", lambda: "https://www.itarang.com"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def payload(self) -> dict:
        return ceo_console.social_payload([])

    def test_an_article_with_no_task_card_anywhere_is_on_the_list(self):
        """The whole bug: both articles live on the site have no card, so the tab
        that read cards showed neither of them."""
        rows = {row["slug"] for row in self.payload()["articles"]}
        self.assertEqual(
            rows, {"battery-replacement-cost", "charging-at-home", "informal-financing"}
        )

    def test_each_row_carries_the_url_a_follower_would_tap(self):
        row = next(
            item for item in self.payload()["articles"]
            if item["slug"] == "battery-replacement-cost"
        )
        self.assertEqual(
            row["url"], "https://www.itarang.com/blog/battery-replacement-cost"
        )
        self.assertEqual(row["task_id"], "blog:battery-replacement-cost")

    def test_copy_written_earlier_is_never_dropped_off_the_screen(self):
        """A human's edits must not vanish because the list stopped being cards."""
        database = ConsoleDB(self.profile)
        try:
            database.save_crosspost_draft(
                task_id="TASK-089",
                platform="linkedin",
                body="Copy a human edited before this list changed.",
                link="https://www.itarang.com/blog/gone",
                article_fingerprint="whatever",
            )
        finally:
            database.close()

        row = next(
            item for item in self.payload()["articles"] if item["task_id"] == "TASK-089"
        )
        self.assertEqual(len(row["drafts"]), 1)
        self.assertIn("Not a published article", row["state"])

    def test_a_row_says_whether_a_reader_can_open_it_today(self):
        """Live and not-yet-merged are both listed, and told apart.

        Writing the copy before the merge is the point of seeing an unmerged
        article; sending it is what `preflight` refuses.
        """
        for row in self.payload()["articles"]:
            self.assertIn("live", row)
            self.assertIn(row["state"], {
                "Live on the site",
                "Not merged to main yet",
                "Not a published article — copy written earlier",
            })


class ThePipelineTakesAnArticleWithNoCard(unittest.TestCase):
    """Writing and gating copy for an article that never went through the writer."""

    def setUp(self) -> None:
        self.profile = Path(tempfile.mkdtemp())
        self.root = checkout(Path(tempfile.mkdtemp()), pages=("battery-replacement-cost",))
        self.addCleanup(__import__("shutil").rmtree, self.profile, True)
        self.addCleanup(__import__("shutil").rmtree, self.root, True)
        (self.profile / "tasks.md").write_text("# CMO Task Board\n", encoding="utf-8")
        patch = mock.patch.object(ceo_social, "live_origin", lambda: "https://www.itarang.com")
        patch.start()
        self.addCleanup(patch.stop)

    def test_copy_is_written_from_the_page_when_there_is_no_artifact(self):
        result = ceo_social.generate(
            self.profile,
            "blog:battery-replacement-cost",
            actor="it@itarang.com",
            website_root=self.root,
            writer=False,
        )
        drafts = {row["platform"]: row for row in result["drafts"]}
        self.assertEqual(set(drafts), {"linkedin", "x", "instagram"})
        self.assertIn(
            "https://www.itarang.com/blog/battery-replacement-cost",
            drafts["linkedin"]["link"],
        )
        for row in drafts.values():
            self.assertNotIn("BlogLayout", row["body"])

    def test_an_unmerged_article_is_refused_with_the_reason_in_words(self):
        check = ceo_social.preflight(
            self.profile,
            "blog:battery-replacement-cost",
            website_root=self.root,
            check_live=False,
        )
        self.assertFalse(check.eligible)
        self.assertTrue(
            any("not live yet" in blocker for blocker in check.blockers), check.blockers
        )

    def test_a_slug_that_is_not_published_is_refused_by_name(self):
        check = ceo_social.preflight(
            self.profile, "blog:no-such-article", website_root=self.root, check_live=False
        )
        self.assertEqual(check.blockers, ["no such article: blog:no-such-article"])


if __name__ == "__main__":
    unittest.main()
