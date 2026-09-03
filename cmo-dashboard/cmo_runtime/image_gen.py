"""Generate blog imagery with Google's Nano Banana models, and pay for it on the record.

The article pipeline already produces one visual: the writer hand-authors an SVG
diagram, which is the right tool for labels and numbers and stays exactly as it is.
This module produces the other kind — the photographic cover that goes on the blog
card and the OG tag, and one in-article illustration. Two different jobs, two
different producers, and this one never touches the diagram path.

Three things are deliberate.

*The prompt is not built here from a topic string.* It comes from the writer, which
has just read the research and written the article, and is passed through
`cover_prompt` / `figure_prompt` only to have the house rules wrapped around it. An
image generated from the headline alone illustrates the headline, not the article.

*No text in the image.* Nano Banana renders labels unreliably, and a wrong number
rendered into a picture is exactly the fabricated claim the writer contract forbids —
except harder to notice, because nobody proofreads a photograph. Text belongs in the
SVG.

*Every call is priced before it is made and recorded after.* These models have no
free tier. The profile runs to a $50 month and warns at $40, so a run that would
cross the warning is refused here rather than discovered in the ledger later.

Costs (standard tier, ai.google.dev/gemini-api/docs/pricing, August 2026) are in
`PER_IMAGE_USD`. Every generated image carries a SynthID watermark.
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from cmo_runtime.env_file import read_env_value

#: The image-generation surface. Not `:generateContent` — image models moved to it.
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

#: Nano Banana 2. Chosen over the legacy `gemini-2.5-flash-image` for quality and
#: over `gemini-3-pro-image` for cost: Pro is 2x per image against a $50 month.
DEFAULT_MODEL = "gemini-3.1-flash-image"
DEFAULT_IMAGE_SIZE = "1K"
DEFAULT_ASPECT_RATIO = "16:9"

#: What the API will hand back. Not a preference — `image/png` is refused outright
#: with "Supported values: 'image/jpeg'", which a live call found and no amount of
#: reading the docs would have. Lossy on the way in is acceptable because the bytes
#: are re-encoded to WebP here anyway and never served as they arrive.
RESPONSE_MIME = "image/jpeg"

ASPECT_RATIOS = frozenset(
    {"1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
)
#: Uppercase K is required by the API; "1k" is rejected upstream.
IMAGE_SIZES = frozenset({"0.5K", "1K", "2K", "4K"})

#: Standard-tier price per generated image, by (model, image_size).
PER_IMAGE_USD: Mapping[tuple[str, str], float] = {
    ("gemini-3.1-flash-image", "0.5K"): 0.045,
    ("gemini-3.1-flash-image", "1K"): 0.067,
    ("gemini-3.1-flash-image", "2K"): 0.101,
    ("gemini-3.1-flash-image", "4K"): 0.151,
    ("gemini-3.1-flash-lite-image", "1K"): 0.0336,
    ("gemini-2.5-flash-image", "1K"): 0.039,
    ("gemini-3-pro-image", "1K"): 0.134,
    ("gemini-3-pro-image", "2K"): 0.134,
    ("gemini-3-pro-image", "4K"): 0.24,
}

#: Mirrors WARNING in scripts/spend-tracker.py. A generation that would start above
#: this is refused; the article itself is never blocked by it.
SPEND_WARNING_USD = 40.0

HTTP_TIMEOUT_SECONDS = 120
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (2.0, 6.0)

#: WebP written into the artifact store. The console upload route caps at 5 MB; this
#: is far below it because the file ends up committed to the website repo and
#: measured by the Lighthouse baseline.
MAX_GENERATED_IMAGE_BYTES = 900_000
TARGET_IMAGE_BYTES = 250_000
WEBP_QUALITY_LADDER = (82, 72, 62, 50)
MAX_LONG_EDGE_PIXELS = 1600

#: Wrapped around every writer-supplied scene description. These are the rules that
#: cannot be left to a prompt the model wrote about itself.
HOUSE_RULES = """
Photographic, natural light, documentary style. Indian urban context.
Hard constraints, all mandatory:
- Render NO text, no words, no letters, no numbers, no labels, no signage, no
  captions, no watermarks and no user-interface anywhere in the image.
- No recognisable faces; people, if present, are incidental, distant, or turned away.
- No real or invented brand marks, logos, wordmarks, badges or company names.
- No documents, forms, invoices, certificates, dashboards or charts.
- No named third party, competitor, vehicle marque, or government insignia.
- No stock-photo staging: no handshakes, no thumbs-up, no pointing at screens.
Composition: one clear subject, generous negative space, unhurried framing.
""".strip()

COVER_DIRECTION = (
    "A cover image for one article. It must read at thumbnail size on a blog card "
    "and as a social preview: a single subject, strong silhouette, no busy detail."
)
FIGURE_DIRECTION = (
    "An illustration placed inside the body of one article, beside the paragraph it "
    "belongs to. It supports the reading; it does not summarise the whole piece."
)


#: Social cards are the one place where the house rules above are wrong.
#:
#: `HOUSE_RULES` forbids text, numbers, labels and charts, because an article
#: illustration carrying baked-in words is unusable — it cannot be translated,
#: it duplicates the caption, and the model spells it wrong. A social card is the
#: opposite object: it is text, set in a picture, because that is the only thing
#: a feed renders at full size. So it gets its own rules rather than an exception
#: bolted onto the others.
#:
#: What stays forbidden is everything that made the first set strict: invented
#: numbers, invented marks, invented sources. The copy is supplied verbatim and
#: the model's job is to set it, not to write it.
SOCIAL_CARD_RULES = """
Typographic design card. Flat vector composition, no photography.
Palette: deep navy-to-teal gradient background (#0A2A43 to #0E4059), off-white
text, one cyan accent (#38A9DC) used at most once per card.
Hard constraints, all mandatory:
- Render the supplied text EXACTLY as given, spelled exactly, word for word.
  Do not paraphrase it, do not translate it, do not add words to it.
- Add NO text of your own: no extra headline, no invented statistic, no caption,
  no page number, no source line, no watermark.
- Set the wordmark as the plain word "iTarang" only. No logo, no icon, no
  monogram, no emblem, and no other brand mark anywhere.
- No photographs, no faces, no vehicles, no stock imagery, no 3D renders.
- No charts, graphs, axes or data plots: the number in the copy is the graphic.
- No UI, no browser frames, no device mockups, no drop shadows on text.
Composition: generous margins, strong left alignment, one clear typographic
hierarchy, large areas of empty background. The headline is the loudest thing
on the card by a wide margin.
""".strip()

SOCIAL_CARD_DIRECTION = (
    "A branded social card for one published article, to be read at a glance in a "
    "feed on a phone. It carries a short piece of supplied copy and nothing else. "
    "It is a typographic layout, not an illustration."
)

#: What each card is for, appended to the direction so the model lays out the
#: three shapes differently rather than producing one template three times.
CARD_ROLE_DIRECTION = {
    "hook": "This is the first card a reader sees. The headline dominates; it must "
            "stop a thumb. The supporting line is small and secondary.",
    "point": "This is one card in the middle of a swipeable set. It makes a single "
             "point. It must feel like part of the same set as the others.",
    "close": "This is the last card in a swipeable set. It is the call to action, so "
             "it is quiet and uncluttered: mostly empty space around one line.",
    "wide": "This is a single wide card shown inline in a feed, not swiped. It "
            "carries the whole claim on its own, so it must read complete.",
}


def social_card_prompt(
    *,
    role: str,
    kicker: str,
    headline: str,
    support: str = "",
    footer: str = "itarang.com",
) -> str:
    """The prompt for one social card, with the copy quoted for the model to set.

    Each line is labelled and quoted rather than run together into a sentence,
    because an unlabelled blob is how a model decides the footer is a subheading.
    """
    direction = CARD_ROLE_DIRECTION.get(role)
    if direction is None:
        raise ImageGenRefused(f"unknown social card role: {role}")
    headline = " ".join(str(headline).split())
    if not headline:
        raise ImageGenRefused("a social card needs a headline")

    lines = [f'EYEBROW, small letterspaced capitals at the top: "{_quotable(kicker)}"']
    lines.append(f'HEADLINE, the largest text on the card: "{_quotable(headline)}"')
    if str(support).strip():
        lines.append(f'SUPPORTING PARAGRAPH, small, below the headline: "{_quotable(support)}"')
    lines.append(f'FOOTER, small, bottom left: "iTarang"   bottom right: "{_quotable(footer)}"')
    copy = "\n".join(lines)
    return (
        f"{SOCIAL_CARD_DIRECTION} {direction}\n\n"
        f"Set exactly this copy, and no other words:\n{copy}\n\n"
        f"{SOCIAL_CARD_RULES}"
    )


def _quotable(value: str) -> str:
    """Collapse whitespace and neutralise quotes that would break the prompt."""
    return " ".join(str(value or "").split()).replace('"', "'")


class ImageGenRefused(Exception):
    """Raised for every refusal, with whatever was measured before the stop.

    Carries `accounting` for the same reason `ContentRunRefused` does: the caller
    logs a refusal to the spend ledger and needs the numbers that existed at the
    moment it happened.
    """

    def __init__(self, message: str, *, accounting: Mapping[str, object] | None = None) -> None:
        super().__init__(message)
        self.accounting: dict[str, object] = dict(accounting or {})


@dataclass(frozen=True)
class GeneratedImage:
    """One image, already converted to what the website will actually serve."""

    webp: bytes
    width: int
    height: int
    model: str
    image_size: str
    aspect_ratio: str
    prompt: str
    estimated_cost_usd: float

    def accounting(self) -> dict[str, object]:
        return {
            "image_model": self.model,
            "image_size": self.image_size,
            "image_bytes": len(self.webp),
            "image_width": self.width,
            "image_height": self.height,
            "image_cost_usd": self.estimated_cost_usd,
        }


def cover_prompt(scene: str) -> str:
    """Wrap the writer's cover scene in the direction and the house rules."""
    return _wrap(scene, COVER_DIRECTION, "cover scene")


def figure_prompt(scene: str) -> str:
    """Wrap the writer's in-article scene in the direction and the house rules."""
    return _wrap(scene, FIGURE_DIRECTION, "figure scene")


def _wrap(scene: str, direction: str, label: str) -> str:
    cleaned = " ".join(str(scene).split())
    if not cleaned:
        raise ImageGenRefused(f"{label} is empty; nothing to generate from")
    if len(cleaned) > 1200:
        cleaned = cleaned[:1200].rstrip()
    return f"{direction}\n\nSubject: {cleaned}\n\n{HOUSE_RULES}"


def month_to_date_usd(root: str | Path, *, now: Callable[[], datetime] | None = None) -> float:
    """Sum this month's recorded API spend from the profile ledger.

    Reads the same records `scripts/spend-tracker.py` counts: JSON lines whose
    `record_type` is absent or `call`. A missing or unreadable ledger reads as zero
    rather than as a refusal — a first run on a fresh profile has no ledger yet, and
    that is not a budget problem.
    """
    stamp = (now or (lambda: datetime.now(UTC)))()
    month = stamp.strftime("%Y-%m")
    ledger = Path(root) / "logs" / "spend.log"
    if not ledger.is_file():
        return 0.0
    total = 0.0
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if record.get("record_type", "call") != "call":
            continue
        if not str(record.get("date", "")).startswith(month):
            continue
        try:
            total += float(record.get("estimated_cost_usd") or 0)
        except (TypeError, ValueError):
            continue
    return total


def record_spend(
    root: str | Path,
    *,
    task_id: str,
    model: str,
    cost_usd: float,
    status: str,
) -> None:
    """Append one priced call through the ledger's own writer.

    Shelling out rather than appending here is on purpose: `spend-tracker.py record`
    holds the lock, and it is the code that decides when the $40 and $50 alerts fire.
    A second writer would eventually disagree with the first. Same shape as
    `preview_metrics._record_spend`. A missing tracker is silent — the image is
    already generated and paid for, and losing the article over a bookkeeping path
    would be the more expensive failure.
    """
    tracker = Path(
        os.getenv("CMO_SPEND_TRACKER", str(Path(root) / "scripts" / "spend-tracker.py"))
    )
    if not tracker.exists():
        return
    subprocess.run(
        [
            str(tracker), "record",
            "--provider", "gemini",
            "--model", model,
            "--task-id", task_id or "unknown",
            "--cost", f"{cost_usd:.6f}",
            "--status", status,
        ],
        check=False,
        timeout=30,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class GeminiImageClient:
    """One image per call, priced, converted, and recorded.

    `request_json` is injectable for the same reason `FirecrawlResearcher` makes it
    injectable: every test in this repo runs without network and without spending,
    and a client that can only be exercised against the live API is a client nobody
    tests.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        api_key: str | None = None,
        model: str | None = None,
        request_json: Callable[[str, Mapping[str, object]], Mapping[str, Any]] | None = None,
        spend_recorder: Callable[..., None] | None = None,
        month_to_date: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.api_key = api_key or read_env_value(self.root, "GEMINI_API_KEY")
        if not self.api_key:
            raise ImageGenRefused("blocked — Gemini not connected")
        self.model = model or os.getenv("GEMINI_IMAGE_MODEL", DEFAULT_MODEL)
        self.endpoint = os.getenv("GEMINI_API_URL", GEMINI_ENDPOINT)
        self._request_json = request_json or self._http_json
        self._record = spend_recorder or record_spend
        self._month_to_date = month_to_date or (lambda: month_to_date_usd(self.root))
        self._sleep = sleep or time.sleep

    # -- pricing ---------------------------------------------------------------

    def price(self, image_size: str = DEFAULT_IMAGE_SIZE) -> float:
        try:
            return PER_IMAGE_USD[(self.model, image_size)]
        except KeyError:
            raise ImageGenRefused(
                f"no recorded price for {self.model} at {image_size}; refusing to spend blind"
            ) from None

    def budget_headroom(self, image_size: str = DEFAULT_IMAGE_SIZE) -> float:
        """Dollars left below the warning threshold after one image at this size."""
        return SPEND_WARNING_USD - (self._month_to_date() + self.price(image_size))

    # -- generation ------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        task_id: str = "",
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        image_size: str = DEFAULT_IMAGE_SIZE,
    ) -> GeneratedImage:
        if aspect_ratio not in ASPECT_RATIOS:
            raise ImageGenRefused(f"unsupported aspect ratio: {aspect_ratio}")
        if image_size not in IMAGE_SIZES:
            raise ImageGenRefused(f"unsupported image size: {image_size}")
        text = " ".join(str(prompt).split())
        if not text:
            raise ImageGenRefused("image prompt is empty")

        cost = self.price(image_size)
        spent = self._month_to_date()
        if spent + cost > SPEND_WARNING_USD:
            raise ImageGenRefused(
                f"blocked — month-to-date spend ${spent:.2f} plus ${cost:.3f} crosses "
                f"the ${SPEND_WARNING_USD:.0f} warning threshold",
                accounting={"image_cost_usd": 0.0, "spend_mtd_usd": round(spent, 4)},
            )

        payload = {
            "model": self.model,
            "input": [{"type": "text", "text": text}],
            "response_format": {
                "type": "image",
                "mime_type": RESPONSE_MIME,
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
            },
        }
        try:
            response = self._request_json(self.endpoint, payload)
            raw = _decode_image(response)
        except ImageGenRefused as refusal:
            self._record(
                self.root, task_id=task_id, model=self.model, cost_usd=0.0, status="failed"
            )
            refusal.accounting.setdefault("image_cost_usd", 0.0)
            raise

        # Recorded before conversion: the call happened and is billable whatever
        # Pillow makes of the bytes.
        self._record(
            self.root, task_id=task_id, model=self.model, cost_usd=cost, status="estimated"
        )
        webp, width, height = to_webp(raw)
        return GeneratedImage(
            webp=webp,
            width=width,
            height=height,
            model=self.model,
            image_size=image_size,
            aspect_ratio=aspect_ratio,
            prompt=text,
            estimated_cost_usd=cost,
        )

    # -- transport -------------------------------------------------------------

    def _http_json(self, url: str, payload: Mapping[str, object]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        last: str = "no attempt was made"
        for attempt in range(MAX_ATTEMPTS):
            request = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    # Header, never a query parameter: a key in a URL lands in logs.
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                    decoded = json.loads(response.read())
                if not isinstance(decoded, dict):
                    raise ImageGenRefused("Gemini returned a non-object response")
                return decoded
            except urllib.error.HTTPError as exc:
                detail = exc.read(500).decode("utf-8", errors="replace").replace("\n", " ")
                last = f"HTTP {exc.code}: {detail[:300]}"
                retryable = exc.code == 429 or 500 <= exc.code < 600
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last = f"{type(exc).__name__}: {exc}"
                retryable = True
            if not retryable or attempt == MAX_ATTEMPTS - 1:
                break
            self._sleep(RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)])
        raise ImageGenRefused(f"Gemini image request failed: {last}")


def _decode_image(response: Mapping[str, Any]) -> bytes:
    """Pull the image bytes out of an interactions response.

    Two shapes are documented — the convenience `output_image` and the step content
    it is derived from — and both are accepted so a response-shape change does not
    silently turn every generation into a refusal.
    """
    encoded = ""
    output = response.get("output_image")
    if isinstance(output, Mapping):
        encoded = str(output.get("data", "") or "")
    elif isinstance(output, str):
        encoded = output
    if not encoded:
        for step in response.get("steps", []) or []:
            if not isinstance(step, Mapping):
                continue
            for item in step.get("content", []) or []:
                if isinstance(item, Mapping) and item.get("type") == "image" and item.get("data"):
                    encoded = str(item["data"])
                    break
            if encoded:
                break
    if not encoded:
        raise ImageGenRefused("Gemini response carried no image")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageGenRefused(f"Gemini image data is not valid base64: {exc}") from exc
    if not raw:
        raise ImageGenRefused("Gemini returned an empty image")
    return raw


def to_webp(raw: bytes) -> tuple[bytes, int, int]:
    """Convert generated bytes to a website-sized WebP, and report its dimensions.

    Quality steps down rather than the image being rejected outright: a cover that
    lands at 300 KB is worth re-encoding, not worth losing.
    """
    from PIL import Image  # Pillow 12 lives in the runtime venv; imported late so
                           # that a caller only pricing or prompting never needs it.

    try:
        with Image.open(io.BytesIO(raw)) as opened:
            image = opened.convert("RGB")
    except Exception as exc:  # Pillow raises a wide family for malformed input
        raise ImageGenRefused(f"generated bytes are not a readable image: {exc}") from exc

    long_edge = max(image.size)
    if long_edge > MAX_LONG_EDGE_PIXELS:
        scale = MAX_LONG_EDGE_PIXELS / long_edge
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.LANCZOS,
        )

    encoded = b""
    for quality in WEBP_QUALITY_LADDER:
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=quality, method=6)
        encoded = buffer.getvalue()
        if len(encoded) <= TARGET_IMAGE_BYTES:
            break
    if len(encoded) > MAX_GENERATED_IMAGE_BYTES:
        raise ImageGenRefused(
            f"generated image is {len(encoded)} bytes after re-encoding; "
            f"the cap is {MAX_GENERATED_IMAGE_BYTES}"
        )
    return encoded, image.width, image.height
