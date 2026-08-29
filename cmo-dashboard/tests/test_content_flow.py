from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from cmo_runtime.agent_runtime import BoardStore, RunAccountant
from cmo_runtime.cmo_agent import run_content_execution
from cmo_runtime.content_flow import (
    ArticlePackage,
    ContentRunResult,
    ContentRunRefused,
    ContentRuntime,
    FirecrawlResearcher,
    ResearchBundle,
    ResearchSource,
    _frontmatter,
    _normalise_package_slot,
)
from cmo_runtime.image_gen import ImageGenRefused
from cmo_runtime.task_file import TaskFile


BOARD = """# CMO Task Board

## Backlog

### TASK-100 — Explain battery range loss in hot weather
- Owner: content
- Priority: high
- Objective: Give electric two-wheeler owners a useful explanation.
- Status: Backlog
- Topic stage: proposed

### TASK-101 — A lower-priority content topic
- Owner: content
- Priority: medium
- Objective: Explain a second concept.
- Status: Backlog

### TASK-102 — Blocked content commissioning card
- Owner: content
- Priority: critical
- Objective: Internal commissioning only.
- Status: Backlog
- Change status: blocked
- Work type: commissioning

## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

_No tasks._

## Completed

_No tasks._
"""


class RecordingSkillLoader:
    def __init__(self) -> None:
        self.loaded: list[str] = []

    def load(self, name: str) -> str:
        self.loaded.append(name)
        if name != "content":
            raise AssertionError(f"unexpected skill: {name}")
        return "SKILL: content\nKPIS: approved\nOUTPUT: article\n"


class RecordingTaskFile(TaskFile):
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.set_calls: list[tuple[str, dict[str, str]]] = []
        self.move_calls: list[tuple[str, str]] = []

    def set_board_fields(self, task_id: str, fields: dict[str, str]) -> None:
        self.set_calls.append((task_id, dict(fields)))
        super().set_board_fields(task_id, fields)

    def move(
        self,
        task_id: str,
        target_section: str,
        *,
        change_status: str | None = None,
        tag: str | None = None,
    ) -> None:
        self.move_calls.append((task_id, target_section))
        super().move(
            task_id,
            target_section,
            change_status=change_status,
            tag=tag,
        )


class FakeResearcher:
    def __init__(self, bundle: ResearchBundle | Exception) -> None:
        self.bundle = bundle
        self.calls: list[tuple[str, str]] = []

    def research(self, task_id: str, topic: str) -> ResearchBundle:
        self.calls.append((task_id, topic))
        if isinstance(self.bundle, Exception):
            raise self.bundle
        return self.bundle


class FakeWriter:
    def __init__(self, package: ArticlePackage) -> None:
        self.package = package
        self.calls: list[dict[str, str]] = []

    def write(
        self,
        *,
        task_id: str,
        topic: str,
        research_markdown: str,
        skill_text: str,
        writer_contract: str,
        topic_outline: str = "",
        topic_keywords: str = "",
        section_outline: Sequence[str] = (),
    ) -> ArticlePackage:
        self.calls.append(
            {
                "task_id": task_id,
                "topic": topic,
                "research_markdown": research_markdown,
                "skill_text": skill_text,
                "writer_contract": writer_contract,
                "topic_outline": topic_outline,
                "topic_keywords": topic_keywords,
                "section_outline": tuple(section_outline),
            }
        )
        return self.package


def article_markdown(task_id: str = "TASK-100") -> str:
    paragraphs = []
    for index in range(16):
        paragraphs.append(
            "Heat changes how electrochemical reactions behave inside a battery pack, "
            "so riders need to separate temporary range variation from permanent ageing. "
            "A useful diagnosis compares the same route, payload, tyre pressure, charging "
            "pattern, and ambient conditions instead of treating one dashboard estimate "
            "as proof that a pack has failed. This plain comparison helps an owner ask a "
            "service technician a precise question and avoids an unsupported conclusion. "
            f"The explanation step shown here is number {index + 1} in the reader journey."
        )
    body = "\n\n".join(paragraphs)
    return f"""---
title: Why electric-vehicle range changes in hot weather
meta_title: EV battery range in hot weather, explained
meta_description: A plain-language guide to temporary range change and battery ageing.
slug: ev-battery-range-hot-weather
category: charging-maintenance
audience: Electric two-wheeler owners
source_urls: https://example.org/source-one, https://example.org/source-two, https://example.org/source-three
---

# Why electric-vehicle range changes in hot weather

{body}

{{{{image:heat-flow|How heat, usage and battery controls affect usable range}}}}

## Decision bullets:

- The article explains a useful battery concept rather than reporting news.
- Every factual source comes from the retained research brief.
- The diagram gives the reader a compact diagnostic flow.
"""


def package() -> ArticlePackage:
    return ArticlePackage(
        markdown=article_markdown(),
        slot_id="heat-flow",
        slot_caption="How heat, usage and battery controls affect usable range",
        svg="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420" role="img">
<title>Battery heat and range flow</title><desc>A three-step explanatory flow.</desc>
<rect width="900" height="420" fill="#fff"/><text x="50" y="80">Heat</text>
<path d="M120 75 H360" stroke="#222"/><text x="390" y="80">Battery controls</text>
<path d="M560 75 H760" stroke="#222"/><text x="770" y="80">Usable range</text>
</svg>""",
        usage={"total_tokens": 1234, "estimated_cost_usd": 0.02},
    )


def bundle(*, sources: tuple[ResearchSource, ...] | None = None) -> ResearchBundle:
    if sources is None:
        sources = (
            ResearchSource("Source one", "https://example.org/source-one", "2026-07-01", "2026-08-10", "Evidence one."),
            ResearchSource("Source two", "https://example.org/source-two", "2026-07-02", "2026-08-10", "Evidence two."),
            ResearchSource("Source three", "https://example.org/source-three", "2026-07-03", "2026-08-10", "Evidence three."),
        )
    return ResearchBundle(
        sources=sources,
        pages_requested=8,
        pages_fetched=len(sources),
        credits_before=100,
        credits_after=108,
        credits_used=8,
        credits_remaining=892,
    )


class ContentFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        (self.root / "logs").mkdir()
        (self.root / "state").mkdir()
        (self.root / "cmo_skills").mkdir()
        (self.root / "tasks.md").write_text(BOARD, encoding="utf-8")
        (self.root / "WRITER_CONTRACT.md").write_text("Writer contract for tests.\n", encoding="utf-8")
        self.task_file = RecordingTaskFile(self.root / "tasks.md")
        self.loader = RecordingSkillLoader()

    def runtime(self, research: ResearchBundle | Exception = bundle()) -> ContentRuntime:
        return ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=FakeResearcher(research),
            writer=FakeWriter(package()),
        )

    def test_frontmatter_requires_category(self) -> None:
        markdown = article_markdown().replace("category: charging-maintenance\n", "")

        with self.assertRaisesRegex(ContentRunRefused, "missing: category"):
            _frontmatter(markdown)

    def test_frontmatter_rejects_unknown_category(self) -> None:
        markdown = article_markdown().replace(
            "category: charging-maintenance",
            "category: mobility-news",
        )

        with self.assertRaisesRegex(ContentRunRefused, "unknown blog category: mobility-news"):
            _frontmatter(markdown)

    def test_execute_researches_first_writes_real_artifacts_and_moves_to_review(self) -> None:
        runtime = self.runtime()
        result = runtime.execute()

        self.assertEqual(result.task_id, "TASK-100")
        self.assertEqual(self.loader.loaded, ["content"])
        self.assertTrue(result.research_path.is_file())
        self.assertTrue(result.article_path.is_file())
        self.assertTrue(result.diagram_path.is_file())
        self.assertIn("https://example.org/source-one", result.research_path.read_text(encoding="utf-8"))
        self.assertIn("{{image:heat-flow|", result.article_path.read_text(encoding="utf-8"))
        self.assertIn("<svg", result.diagram_path.read_text(encoding="utf-8"))

        card = BoardStore(self.root).get("TASK-100")
        self.assertEqual(card.section, "CMO Review")
        self.assertEqual(card.fields["Status"], "CMO Review")
        self.assertEqual(card.fields["Attachment"], "artifacts/TASK-100-content.md")
        self.assertEqual(card.fields["Category"], "charging-maintenance")
        self.assertEqual(card.fields["Research brief"], "artifacts/TASK-100-research.md")
        self.assertEqual(card.fields["Image slot heat-flow"], "artifacts/TASK-100-heat-flow.svg")
        self.assertEqual(card.fields["Source fetch success rate"], "3/8 (37.5%)")
        self.assertEqual(card.fields["Firecrawl credits per article"], "8 measured credits")
        self.assertEqual(card.fields["Change status"], "pending CMO review")
        self.assertEqual(card.fields["Tag"], "action to be taken by: cmo")

        content_updates = [
            fields
            for _, fields in self.task_file.set_calls
            if "Attachment" in fields
        ]
        self.assertEqual(len(content_updates), 1)
        self.assertEqual(
            set(content_updates[0]),
            # `Change type: website` is what makes approving the article Gate 1
            # rather than completion. A blog post adds a route, a registry entry
            # and a sitemap URL; a card left unclassified was approved straight
            # into Completed, past the publish step entirely.
            {"Attachment", "Category", "Change type", "Description", "Metric", "Image slot heat-flow"},
        )
        self.assertEqual(
            self.task_file.move_calls,
            [("TASK-100", "In Progress"), ("TASK-100", "CMO Review")],
        )

    def test_execute_refuses_without_sources_and_does_not_write_a_brief_or_article(self) -> None:
        runtime = self.runtime(bundle(sources=()))

        with self.assertRaisesRegex(ContentRunRefused, "no source pages"):
            runtime.execute()

        self.assertEqual(self.loader.loaded, ["content"])
        self.assertFalse((self.root / "artifacts" / "TASK-100-research.md").exists())
        self.assertFalse((self.root / "artifacts" / "TASK-100-content.md").exists())
        card = BoardStore(self.root).get("TASK-100")
        self.assertEqual(card.section, "Backlog")
        # `write failed`, not `blocked`: nobody chose this, so the console may offer
        # a retry. `blocked` stays reserved for a card a human deliberately held.
        self.assertEqual(card.fields["Change status"], "write failed")

    def test_credit_ceiling_refuses_before_any_search_request(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def request_json(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            return {"data": {"planCredits": 1000, "remainingCredits": 199}}

        researcher = FirecrawlResearcher(self.root, api_key="test-key", request_json=request_json)

        with self.assertRaisesRegex(ContentRunRefused, "801 measured credits"):
            researcher.research("TASK-100", "battery range")

        self.assertEqual(calls, [("GET", "/v2/team/credit-usage", None)])

    def test_firecrawl_search_requests_no_more_than_eight_pages_and_measures_usage(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []
        credit_reads = iter((100, 108))

        def request_json(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            if method == "GET":
                used = next(credit_reads)
                return {"data": {"planCredits": 1000, "remainingCredits": 1000 - used}}
            limit = int((payload or {})["limit"])
            prefix = "site" if "site:itarang.com" in str((payload or {})["query"]) else "web"
            return {
                "success": True,
                "data": {
                    "web": [
                        {
                            "title": f"{prefix} source {index}",
                            "url": f"https://{prefix}.example/{index}",
                            "markdown": f"Evidence page {index}",
                            "metadata": {"publishedTime": f"2026-07-{index + 1:02d}"},
                        }
                        for index in range(limit)
                    ]
                },
            }

        researcher = FirecrawlResearcher(self.root, api_key="test-key", request_json=request_json)
        result = researcher.research("TASK-100", "battery range")

        search_payloads = [payload for method, _, payload in calls if method == "POST"]
        self.assertEqual([payload["limit"] for payload in search_payloads], [5, 3])
        self.assertEqual(sum(int(payload["limit"]) for payload in search_payloads), 8)
        self.assertEqual(result.pages_requested, 8)
        self.assertEqual(result.pages_fetched, 8)
        self.assertEqual(result.credits_used, 8)
        self.assertEqual(result.credits_remaining, 892)

    def test_run_accountant_records_measured_content_health_without_inventing_rupee_cost(self) -> None:
        ledger = self.root / "logs" / "spend.log"
        accountant = RunAccountant(ledger)

        accountant.append(
            run_type="content-execute",
            skill_loaded="content",
            approximate_tokens=1234,
            approximate_cost_inr=None,
            status="completed",
            extra={
                "task_id": "TASK-100",
                "firecrawl_pages_fetched": 8,
                "firecrawl_credits_used": 8,
                "firecrawl_credits_remaining": 892,
                "source_fetch_success_rate": 1.0,
                "outcome": "article written",
            },
        )

        record = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertIsNone(record["approximate_cost_inr"])
        self.assertEqual(record["firecrawl_credits_used"], 8)
        self.assertEqual(record["outcome"], "article written")

    def test_content_command_accounts_only_after_the_runtime_returns(self) -> None:
        events: list[str] = []
        research = bundle()
        expected = ContentRunResult(
            task_id="TASK-100",
            research_path=self.root / "artifacts" / "TASK-100-research.md",
            article_path=self.root / "artifacts" / "TASK-100-content.md",
            diagram_path=self.root / "artifacts" / "TASK-100-heat-flow.svg",
            research=research,
            usage={"total_tokens": 1234, "estimated_cost_usd": 0.02},
        )

        class Runtime:
            def execute(self) -> ContentRunResult:
                events.append("runtime returned")
                return expected

        class Accountant:
            def append(self, *args: object, **kwargs: object) -> None:
                events.append("spend appended")
                self.args = args
                self.kwargs = kwargs

        accountant = Accountant()
        result = run_content_execution(
            self.root,
            runtime=Runtime(),
            accountant=accountant,
        )

        self.assertIs(result, expected)
        self.assertEqual(events, ["runtime returned", "spend appended"])
        self.assertEqual(accountant.args[:2], ("content-execute", "content"))
        self.assertEqual(accountant.args[2], 1234)
        self.assertIsNone(accountant.args[3])
        self.assertEqual(accountant.args[4], "completed")
        self.assertEqual(accountant.kwargs["extra"]["firecrawl_credits_used"], 8)

    def test_live_content_skill_records_only_the_approved_kpis_and_run_health_metrics(self) -> None:
        path = Path(__file__).resolve().parent.parent / "cmo_skills" / "content.skill"
        skill = path.read_text(encoding="utf-8")

        for expected in (
            "Organic clicks to published blog pages — Google Search Console Search Analytics API",
            "Search impressions for published blog pages — Google Search Console Search Analytics API",
            "Average search position for published blog pages — Google Search Console Search Analytics API",
            "First-pass human approval rate — DecisionStore records in approvals.log",
        ):
            self.assertIn(expected, skill)
        self.assertIn(
            "Source-fetch success rate — Firecrawl search/scrape result counts",
            skill,
        )
        self.assertIn(
            "Firecrawl credits per article — Firecrawl /v2/team/credit-usage",
            skill,
        )
        self.assertNotIn("research mode", skill.casefold())


def illustrated_package() -> ArticlePackage:
    """The writer's output when it also directs the two photographic images."""
    base = package()
    markdown = base.markdown.replace(
        "## Decision bullets:",
        "{{image:depot-evening|A depot at the end of a working day}}\n\n## Decision bullets:",
    )
    return replace(
        base,
        markdown=markdown,
        cover_scene="A charged e-rickshaw at a kerbside charging point at dusk.",
        photo_slot_id="depot-evening",
        photo_scene="A small fleet depot with vehicles parked in a row after dark.",
        photo_alt="E-rickshaws parked in a row at a depot after dark",
    )


class FakeGeneratedImage:
    def __init__(self, prompt: str, index: int) -> None:
        self.webp = f"webp-bytes-{index}".encode()
        self.prompt = prompt
        self.estimated_cost_usd = 0.067
        self.width, self.height = 1344, 768


class FakeImageClient:
    def __init__(self, failures: int = 0) -> None:
        self.calls: list[tuple[str, str]] = []
        self.failures = failures

    def generate(self, prompt: str, *, task_id: str = "", **_options):
        self.calls.append((prompt, task_id))
        if len(self.calls) <= self.failures:
            raise ImageGenRefused("blocked — the image model said no")
        return FakeGeneratedImage(prompt, len(self.calls))


class GeneratedImageryTest(unittest.TestCase):
    """The cover and the illustration, alongside a diagram that must not change."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("artifacts", "logs", "state", "cmo_skills"):
            (self.root / name).mkdir()
        (self.root / "tasks.md").write_text(BOARD, encoding="utf-8")
        (self.root / "WRITER_CONTRACT.md").write_text("Writer contract for tests.\n", encoding="utf-8")
        self.task_file = RecordingTaskFile(self.root / "tasks.md")
        self.loader = RecordingSkillLoader()

    def runtime(self, *, client: object | None, package_: ArticlePackage | None = None) -> ContentRuntime:
        return ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=FakeResearcher(bundle()),
            writer=FakeWriter(package_ or illustrated_package()),
            image_client=client,
        )

    def test_both_images_are_written_bound_and_priced(self) -> None:
        client = FakeImageClient()

        result = self.runtime(client=client).execute()

        cover = self.root / "artifacts/TASK-100-cover.webp"
        figure = self.root / "artifacts/TASK-100-depot-evening.webp"
        self.assertTrue(cover.is_file())
        self.assertTrue(figure.is_file())

        card = BoardStore(self.root).get("TASK-100")
        self.assertEqual(card.fields["Cover image"], "artifacts/TASK-100-cover.webp")
        self.assertEqual(
            card.fields["Image slot depot-evening"], "artifacts/TASK-100-depot-evening.webp"
        )
        self.assertEqual(
            card.fields["Image alt depot-evening"],
            "E-rickshaws parked in a row at a depot after dark",
        )
        # The diagram slot is still bound to the writer's SVG, untouched.
        self.assertEqual(card.fields["Image slot heat-flow"], "artifacts/TASK-100-heat-flow.svg")
        self.assertTrue(result.diagram_path.read_text(encoding="utf-8").startswith("<svg"))

        self.assertEqual(result.usage["image_calls"], 2)
        self.assertAlmostEqual(float(result.usage["image_cost_usd"]), 0.134)

    def test_the_writers_scene_reaches_the_model_inside_the_house_rules(self) -> None:
        client = FakeImageClient()

        self.runtime(client=client).execute()

        prompts = [prompt for prompt, _task in client.calls]
        self.assertEqual([task for _prompt, task in client.calls], ["TASK-100", "TASK-100"])
        self.assertIn("A charged e-rickshaw at a kerbside charging point at dusk.", prompts[0])
        self.assertIn("A small fleet depot with vehicles parked in a row after dark.", prompts[1])
        for prompt in prompts:
            self.assertIn("Render NO text", prompt)

    def test_a_refused_image_does_not_cost_the_article(self) -> None:
        client = FakeImageClient(failures=2)

        result = self.runtime(client=client).execute()

        self.assertTrue(result.article_path.is_file())
        self.assertTrue(result.diagram_path.is_file())
        card = BoardStore(self.root).get("TASK-100")
        self.assertNotIn("Cover image", card.fields)
        self.assertNotIn("Image slot depot-evening", card.fields)
        self.assertEqual(card.section, "CMO Review")
        self.assertEqual(result.usage["image_calls"], 0)
        self.assertIn("the image model said no", str(result.usage["image_outcome"]))

    def test_a_half_failed_run_keeps_the_image_it_did_get(self) -> None:
        client = FakeImageClient(failures=1)

        result = self.runtime(client=client).execute()

        card = BoardStore(self.root).get("TASK-100")
        self.assertNotIn("Cover image", card.fields)
        self.assertEqual(
            card.fields["Image slot depot-evening"], "artifacts/TASK-100-depot-evening.webp"
        )
        self.assertEqual(result.usage["image_calls"], 1)

    def test_a_profile_with_no_gemini_key_still_publishes_articles(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            result = self.runtime(client=None).execute()

        self.assertTrue(result.article_path.is_file())
        card = BoardStore(self.root).get("TASK-100")
        self.assertNotIn("Cover image", card.fields)
        self.assertEqual(result.usage["image_calls"], 0)

    def test_an_article_that_directs_no_imagery_calls_nothing(self) -> None:
        client = FakeImageClient()

        result = self.runtime(client=client, package_=package()).execute()

        self.assertEqual(client.calls, [])
        self.assertEqual(result.usage["image_calls"], 0)
        self.assertTrue(result.article_path.is_file())

    def test_a_photo_slot_with_no_alt_text_is_not_generated(self) -> None:
        # The publisher refuses a raster slot with no alt text, so paying for one
        # would buy a picture that can never be published.
        client = FakeImageClient()
        directed = replace(illustrated_package(), photo_alt="")

        self.runtime(client=client, package_=directed).execute()

        self.assertEqual(len(client.calls), 1, "only the cover is worth generating")
        self.assertNotIn("Image slot depot-evening", BoardStore(self.root).get("TASK-100").fields)

    def test_the_second_marker_is_recognised_as_the_photo_slot(self) -> None:
        normalised = _normalise_package_slot(illustrated_package())

        self.assertEqual(normalised.slot_id, "heat-flow")
        self.assertEqual(normalised.photo_slot_id, "depot-evening")
        self.assertEqual(normalised.cover_scene, illustrated_package().cover_scene)


if __name__ == "__main__":
    unittest.main()
