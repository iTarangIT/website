from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from cmo_runtime.blog_publisher import BlogPublisher, BlogPublishRefused, main


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

A useful introduction with **strong evidence**, *careful context*, and a [dated source](https://example.org/source).

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

TASKS = """# CMO Task Board

## Backlog

_No tasks._

## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

_No tasks._

## Completed

### TASK-900 — A useful finance guide
- ID: TASK-900
- Owner: content
- Status: Completed
- Attachment: artifacts/TASK-900-content.md
- Category: financing
- Image slot decision-flow: artifacts/TASK-900-decision-flow.svg
"""


class BlogPublisherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.profile = root / "profile"
        self.website = root / "website"
        (self.profile / "artifacts").mkdir(parents=True)
        (self.website / "src/data").mkdir(parents=True)
        (self.website / "src/app/(marketing)/blog").mkdir(parents=True)
        (self.website / "public/images/blog").mkdir(parents=True)
        (self.profile / "tasks.md").write_text(TASKS, encoding="utf-8")
        (self.profile / "artifacts/TASK-900-content.md").write_text(ARTICLE, encoding="utf-8")
        (self.profile / "artifacts/TASK-900-decision-flow.svg").write_text(SVG, encoding="utf-8")
        (self.website / "src/data/blog-posts.ts").write_text(BLOG_POSTS, encoding="utf-8")

    def test_preview_generates_complete_publish_package_without_writing_website(self) -> None:
        before = (self.website / "src/data/blog-posts.ts").read_bytes()

        plan = BlogPublisher(self.profile, self.website).preview(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )

        self.assertEqual(plan.slug, "useful-finance-guide")
        self.assertIn('title: "Useful Finance Guide for EV Owners"', plan.page_source)
        self.assertIn('description: "A concise description copied exactly into the blog index."', plan.page_source)
        self.assertIn('path: "/blog/useful-finance-guide"', plan.page_source)
        self.assertIn('date="2026-08-10"', plan.page_source)
        self.assertIn('readTime="1 min read"', plan.page_source)
        self.assertIn('category="financing"', plan.page_source)
        self.assertIn("<strong>strong evidence</strong>", plan.page_source)
        self.assertIn("<em>careful context</em>", plan.page_source)
        self.assertIn('href="https://example.org/source"', plan.page_source)
        self.assertIn('<figure className="my-10">', plan.page_source)
        self.assertIn('src="/images/blog/useful-finance-guide.svg"', plan.page_source)
        self.assertIn('alt="EV finance decision flow"', plan.page_source)
        self.assertIn('width={1000}', plan.page_source)
        self.assertIn('height={560}', plan.page_source)
        self.assertIn("<figcaption>", plan.page_source)
        self.assertNotIn("{{image:", plan.page_source)
        self.assertNotIn("<h1", plan.page_source)
        self.assertIn('excerpt:', plan.updated_blog_posts)
        self.assertIn('"A concise description copied exactly into the blog index."', plan.updated_blog_posts)
        # the interface still declares `coverImage?`; no generated record sets one
        self.assertNotIn("coverImage:", plan.updated_blog_posts)
        self.assertEqual(plan.image_source, SVG.encode("utf-8"))
        self.assertFalse(plan.page_path.exists())
        self.assertFalse(plan.image_path.exists())
        self.assertEqual((self.website / "src/data/blog-posts.ts").read_bytes(), before)

    def test_generated_multiline_jsx_has_no_blank_line_between_nested_tags(self) -> None:
        plan = BlogPublisher(self.profile, self.website).preview(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )

        self.assertIn(
            '<figure className="my-10">\n        <Image',
            plan.page_source,
        )
        self.assertIn("<ul>\n        <li>", plan.page_source)

    def test_generated_svg_uses_next_image_without_optimization(self) -> None:
        plan = BlogPublisher(self.profile, self.website).preview(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )

        self.assertIn('import Image from "next/image";', plan.page_source)
        self.assertIn("        <Image\n", plan.page_source)
        self.assertIn("          unoptimized\n", plan.page_source)
        self.assertNotIn("<img", plan.page_source)

    def test_preview_omits_review_only_sections_from_public_page_and_read_time(self) -> None:
        article_path = self.profile / "artifacts/TASK-900-content.md"
        review_words = " ".join(["internal"] * 400)
        article_path.write_text(
            ARTICLE
            + f"""

## Source-backed outline

{review_words}

## Claims requiring human verification

Do not expose this review note.

## Proposed internal links and call to action — not published

Do not expose this proposed call to action.

## Sources and dates

- [Public source](https://example.org/public) — accessed 10 August 2026.
""",
            encoding="utf-8",
        )

        plan = BlogPublisher(self.profile, self.website).preview(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )

        self.assertNotIn("Source-backed outline", plan.page_source)
        self.assertNotIn("Claims requiring human verification", plan.page_source)
        self.assertNotIn("Proposed internal links", plan.page_source)
        self.assertIn("Sources and dates", plan.page_source)
        self.assertIn("Public source", plan.page_source)
        self.assertEqual(plan.read_time, "1 min read")

    def test_preview_refuses_missing_required_front_matter_cleanly(self) -> None:
        article_path = self.profile / "artifacts/TASK-900-content.md"
        article_path.write_text(
            ARTICLE.replace(
                "meta_description: A concise description copied exactly into the blog index.\n",
                "",
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            BlogPublishRefused,
            "article front matter is missing: meta_description",
        ):
            BlogPublisher(self.profile, self.website).preview(
                "TASK-900",
                publication_date=date(2026, 8, 10),
            )

    def test_preview_refuses_unsafe_svg_as_a_publish_refusal(self) -> None:
        (self.profile / "artifacts/TASK-900-decision-flow.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560">'
            "<title>Unsafe SVG</title><script>alert(1)</script></svg>",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(BlogPublishRefused, "SVG refused"):
            BlogPublisher(self.profile, self.website).preview(
                "TASK-900",
                publication_date=date(2026, 8, 10),
            )

    def test_apply_writes_page_index_and_image_on_cmo_changes(self) -> None:
        subprocess.run(
            ["git", "init", "-b", "cmo-changes"],
            cwd=self.website,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "publisher-test@example.invalid"],
            cwd=self.website,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Publisher Test"],
            cwd=self.website,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.website, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fixture"],
            cwd=self.website,
            check=True,
            capture_output=True,
            text=True,
        )

        plan = BlogPublisher(self.profile, self.website).apply(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )

        self.assertEqual(plan.page_path.read_text(encoding="utf-8"), plan.page_source)
        self.assertEqual(plan.image_path.read_bytes(), SVG.encode("utf-8"))
        self.assertEqual(
            (self.website / "src/data/blog-posts.ts").read_text(encoding="utf-8"),
            plan.updated_blog_posts,
        )

    def test_apply_refuses_legacy_artifact_without_recorded_category(self) -> None:
        article_path = self.profile / "artifacts/TASK-900-content.md"
        article_path.write_text(
            ARTICLE.replace("category: financing\n", ""),
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "init", "-b", "cmo-changes"],
            cwd=self.website,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "publisher-test@example.invalid"],
            cwd=self.website,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Publisher Test"],
            cwd=self.website,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.website, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fixture"],
            cwd=self.website,
            check=True,
            capture_output=True,
            text=True,
        )

        with self.assertRaisesRegex(
            BlogPublishRefused,
            "apply requires category in both artifact front matter and task card",
        ):
            BlogPublisher(self.profile, self.website).apply(
                "TASK-900",
                publication_date=date(2026, 8, 10),
            )

    def test_write_preview_materializes_only_beneath_requested_output(self) -> None:
        publisher = BlogPublisher(self.profile, self.website)
        plan = publisher.preview(
            "TASK-900",
            publication_date=date(2026, 8, 10),
        )
        output = self.profile / "tmp/TASK-900-publish-preview"

        paths = publisher.write_preview(plan, output)

        self.assertEqual(
            paths["page"].read_text(encoding="utf-8"),
            plan.page_source,
        )
        self.assertEqual(paths["image"].read_bytes(), plan.image_source)
        self.assertEqual(
            paths["blog_posts"].read_text(encoding="utf-8"),
            plan.updated_blog_posts,
        )
        self.assertFalse(plan.page_path.exists())
        self.assertFalse(plan.image_path.exists())

    def test_cli_defaults_to_non_branch_preview(self) -> None:
        output = self.profile / "tmp/cli-preview"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "TASK-900",
                    "--profile-root",
                    str(self.profile),
                    "--website-root",
                    str(self.website),
                    "--date",
                    "2026-08-10",
                    "--output-dir",
                    str(output),
                ]
            )

        self.assertEqual(result, 0)
        self.assertIn("DRY RUN", stdout.getvalue())
        self.assertIn(
            str(output / "src/app/(marketing)/blog/useful-finance-guide/page.tsx"),
            stdout.getvalue(),
        )
        self.assertFalse(
            (self.website / "src/app/(marketing)/blog/useful-finance-guide/page.tsx").exists()
        )

    def test_script_entrypoint_imports_runtime_from_any_working_directory(self) -> None:
        output = self.profile / "tmp/script-preview"
        script = Path(__file__).resolve().parents[1] / "scripts/blog-publisher.py"

        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "TASK-900",
                "--profile-root",
                str(self.profile),
                "--website-root",
                str(self.website),
                "--date",
                "2026-08-10",
                "--output-dir",
                str(output),
            ],
            cwd=Path(self.temp.name),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("DRY RUN", completed.stdout)


if __name__ == "__main__":
    unittest.main()
