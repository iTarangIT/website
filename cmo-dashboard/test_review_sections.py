"""The console and the publisher agree about what a reader may see.

They did not. The console matched five heading patterns; the publisher matched
three different ones and had never heard of `Decision bullets:` — so that heading,
and the paragraph of internal-link proposals and access dates after it, went to
the website under a URL anyone can open. The page published the sentence "Non-
published call to action for review".

This is the same failure as the two Markdown renderers: two definitions of one
rule, drifting until the difference reached a reader. So the definition is one
object and both consumers import it, and the first test here fails if either one
grows its own copy again.
"""

from __future__ import annotations

import re
import unittest

import ceo_reader
from cmo_runtime import blog_publisher, review_sections

ARTICLE_TAIL = """## When replacement is the safer long-term choice

Replacement becomes the safer choice when the battery is no longer predictable.

## Decision bullets:

Before approving either, write the decision down in plain numbers.

- Choose repair when the fault is clear and limited.
- Choose replacement when the same battery repeatedly reduces range.

## Closing: think beyond today's cash bill

The best decision is practical, not emotional.

For iTarang, this fits the wider lifecycle view. Claims requiring human verification before publication: any iTarang-specific repair programme or warranty promise.

Proposed internal links: iTarang Blog, the Battery Passport article. Non-published call to action for review: "Talk to iTarang before replacing a weak battery." Source notes: retained pages were accessed on 2026-08-11.
"""


class OneDefinitionTwoConsumers(unittest.TestCase):
    def test_the_console_uses_the_shared_patterns_rather_than_its_own(self) -> None:
        self.assertIs(ceo_reader.REVIEW_HEADINGS, review_sections.HEADING_PATTERNS)

    def test_the_publisher_uses_the_shared_stripper_rather_than_its_own(self) -> None:
        source = blog_publisher._public_body.__code__.co_names
        self.assertIn("strip_scaffolding", source, "the publisher grew its own copy again")
        self.assertFalse(
            hasattr(blog_publisher, "_REVIEW_ONLY_HEADINGS"),
            "the publisher still carries a second list of review headings",
        )

    def test_both_consumers_answer_the_same_for_every_label(self) -> None:
        for label in review_sections.REVIEW_LABELS:
            with self.subTest(label=label):
                self.assertTrue(ceo_reader._is_review_heading(label))
                self.assertTrue(review_sections.is_review_heading(label + ":"))
                self.assertNotIn(
                    label.casefold(),
                    review_sections.strip_scaffolding(f"## {label}\n\nnotes here\n").casefold(),
                )

    def test_an_ordinary_heading_is_not_mistaken_for_scaffolding(self) -> None:
        for heading in ("Start with the warning signs", "Closing: think beyond the bill",
                        "What a repair costs", "Sources of finance"):
            with self.subTest(heading=heading):
                self.assertFalse(review_sections.is_review_heading(heading))
                self.assertIn(heading, review_sections.strip_scaffolding(f"## {heading}\n\nbody\n"))


class NothingAddressedToAReviewerReachesTheReader(unittest.TestCase):
    def clean(self) -> str:
        return review_sections.strip_scaffolding(ARTICLE_TAIL)

    def test_the_decision_bullets_section_goes_entirely(self) -> None:
        clean = self.clean()

        self.assertNotIn("Decision bullets", clean)
        self.assertNotIn("Choose repair when the fault is clear", clean, "its bullets survived")
        self.assertNotIn("Before approving either", clean, "its prose survived")

    def test_a_labelled_sentence_inside_a_paragraph_is_cut(self) -> None:
        """The form the writer actually used, which nothing was stripping."""
        clean = self.clean()

        self.assertIn("For iTarang, this fits the wider lifecycle view.", clean)
        self.assertNotIn("Claims requiring human verification", clean)

    def test_a_paragraph_that_is_entirely_scaffolding_disappears(self) -> None:
        clean = self.clean()

        for phrase in ("Proposed internal links", "Non-published call to action",
                       "Source notes", "accessed on 2026-08-11"):
            self.assertNotIn(phrase, clean, phrase)

    def test_the_article_itself_is_untouched(self) -> None:
        clean = self.clean()

        self.assertIn("## When replacement is the safer long-term choice", clean)
        self.assertIn("## Closing: think beyond today's cash bill", clean)
        self.assertIn("Replacement becomes the safer choice", clean)
        self.assertIn("The best decision is practical, not emotional.", clean)

    def test_no_run_of_blank_lines_is_left_where_a_section_was(self) -> None:
        self.assertIsNone(re.search(r"\n{3,}", self.clean()))

    def test_a_fenced_block_is_never_reinterpreted(self) -> None:
        body = "## Real\n\n```\n## Decision bullets:\nSource notes: inside a fence\n```\n"

        self.assertIn("Source notes: inside a fence", review_sections.strip_scaffolding(body))


if __name__ == "__main__":
    unittest.main()
