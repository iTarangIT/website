from __future__ import annotations

import base64
import http.server
import io
import json
import threading
import tempfile
import unittest
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

from cmo_runtime.image_gen import (
    DEFAULT_MODEL,
    GeminiImageClient,
    ImageGenRefused,
    cover_prompt,
    figure_prompt,
    month_to_date_usd,
    to_webp,
)


def png_bytes(width: int = 1344, height: int = 768) -> bytes:
    """A real PNG, so the conversion path is exercised rather than mocked away."""
    from PIL import Image

    image = Image.new("RGB", (width, height), (12, 84, 60))
    for x in range(0, width, 7):
        for y in range(0, height, 11):
            image.putpixel((x, y), ((x * 5) % 256, (y * 3) % 256, (x + y) % 256))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def response_with_image(raw: bytes | None = None) -> dict[str, object]:
    encoded = base64.b64encode(raw if raw is not None else png_bytes()).decode("ascii")
    return {"output_image": {"mime_type": "image/png", "data": encoded}}


class ImageGenTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "logs").mkdir()
        self.recorded: list[dict[str, object]] = []
        self.requests: list[tuple[str, dict[str, object]]] = []

    def _record(self, root, *, task_id, model, cost_usd, status) -> None:
        self.recorded.append(
            {"root": root, "task_id": task_id, "model": model, "cost": cost_usd, "status": status}
        )

    def client(
        self,
        *,
        response: object = None,
        spent: float = 0.0,
        **kwargs,
    ) -> GeminiImageClient:
        payload = response if response is not None else response_with_image()

        def request_json(url, body):
            self.requests.append((url, dict(body)))
            if isinstance(payload, Exception):
                raise payload
            return payload

        options = {
            "api_key": "test-key",
            "request_json": request_json,
            "spend_recorder": self._record,
            "month_to_date": lambda: spent,
            "sleep": lambda _seconds: None,
        }
        options.update(kwargs)
        return GeminiImageClient(self.root, **options)


class GenerateTest(ImageGenTestCase):
    def test_generate_returns_sized_webp_and_records_one_priced_call(self) -> None:
        image = self.client().generate("a quiet depot at dawn", task_id="TASK-900")

        self.assertEqual(image.webp[:4], b"RIFF")
        self.assertEqual(image.webp[8:12], b"WEBP")
        self.assertEqual((image.width, image.height), (1344, 768))
        self.assertEqual(image.model, DEFAULT_MODEL)
        self.assertAlmostEqual(image.estimated_cost_usd, 0.067)
        self.assertEqual(image.accounting()["image_cost_usd"], 0.067)

        self.assertEqual(len(self.recorded), 1)
        self.assertEqual(self.recorded[0]["task_id"], "TASK-900")
        self.assertEqual(self.recorded[0]["status"], "estimated")
        self.assertAlmostEqual(float(self.recorded[0]["cost"]), 0.067)

    def test_request_carries_model_aspect_ratio_and_size(self) -> None:
        self.client().generate("a depot", aspect_ratio="4:3", image_size="2K")

        url, body = self.requests[0]
        self.assertIn("/v1beta/interactions", url)
        self.assertEqual(body["model"], DEFAULT_MODEL)
        self.assertEqual(body["input"], [{"type": "text", "text": "a depot"}])
        self.assertEqual(body["response_format"]["aspect_ratio"], "4:3")
        self.assertEqual(body["response_format"]["image_size"], "2K")

    def test_step_content_response_shape_is_accepted(self) -> None:
        response = {
            "steps": [
                {"content": [{"type": "text", "text": "thinking"}]},
                {"content": [{"type": "image", "data": base64.b64encode(png_bytes(640, 360)).decode()}]},
            ]
        }
        image = self.client(response=response).generate("a depot")
        self.assertEqual((image.width, image.height), (640, 360))

    def test_missing_key_refuses_without_reaching_the_api(self) -> None:
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(ImageGenRefused) as caught:
                GeminiImageClient(self.root, api_key="")
        self.assertIn("Gemini not connected", str(caught.exception))
        self.assertEqual(self.requests, [])

    def test_key_is_read_from_the_profile_env_file(self) -> None:
        (self.root / ".env").write_text("GEMINI_API_KEY=from-env-file\n", encoding="utf-8")
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            client = GeminiImageClient(self.root, request_json=lambda url, body: response_with_image())
        self.assertEqual(client.api_key, "from-env-file")

    def test_unknown_aspect_ratio_and_size_are_refused(self) -> None:
        for kwargs in ({"aspect_ratio": "7:3"}, {"image_size": "1k"}):
            with self.subTest(**kwargs):
                with self.assertRaises(ImageGenRefused):
                    self.client().generate("a depot", **kwargs)
        self.assertEqual(self.requests, [])

    def test_empty_prompt_is_refused(self) -> None:
        with self.assertRaises(ImageGenRefused):
            self.client().generate("   ")
        self.assertEqual(self.requests, [])

    def test_unpriced_model_refuses_rather_than_spending_blind(self) -> None:
        client = self.client(model="gemini-9-imaginary-image")
        with self.assertRaises(ImageGenRefused) as caught:
            client.generate("a depot")
        self.assertIn("no recorded price", str(caught.exception))
        self.assertEqual(self.requests, [])


class BudgetTest(ImageGenTestCase):
    def test_generation_that_would_cross_the_warning_is_refused_before_the_call(self) -> None:
        with self.assertRaises(ImageGenRefused) as caught:
            self.client(spent=39.98).generate("a depot", task_id="TASK-900")

        self.assertIn("crosses the $40 warning", str(caught.exception))
        self.assertEqual(self.requests, [], "no paid call may be made after a budget refusal")
        self.assertEqual(self.recorded, [], "a refused call is not a spend record")

    def test_generation_below_the_warning_proceeds(self) -> None:
        image = self.client(spent=39.90).generate("a depot")
        self.assertTrue(image.webp)

    def test_budget_headroom_reports_the_remaining_dollars(self) -> None:
        self.assertAlmostEqual(self.client(spent=12.0).budget_headroom(), 40.0 - 12.067, places=4)

    def test_month_to_date_counts_only_this_month_and_only_call_records(self) -> None:
        ledger = self.root / "logs" / "spend.log"
        ledger.write_text(
            "\n".join(
                json.dumps(item)
                for item in (
                    {"record_type": "call", "date": "2026-08-02T10:00:00+00:00", "estimated_cost_usd": 1.5},
                    {"date": "2026-08-03T10:00:00+00:00", "estimated_cost_usd": 0.5},
                    {"record_type": "run", "date": "2026-08-04T10:00:00+00:00", "estimated_cost_usd": 99},
                    {"record_type": "call", "date": "2026-07-31T10:00:00+00:00", "estimated_cost_usd": 7},
                    {"record_type": "call", "date": "2026-08-05T10:00:00+00:00", "estimated_cost_usd": None},
                    "not json",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        total = month_to_date_usd(self.root, now=lambda: datetime(2026, 8, 27, tzinfo=UTC))
        self.assertAlmostEqual(total, 2.0)

    def test_missing_ledger_reads_as_zero(self) -> None:
        self.assertEqual(month_to_date_usd(self.root / "nowhere"), 0.0)


class FailureTest(ImageGenTestCase):
    def test_response_without_an_image_refuses_and_records_a_failed_call(self) -> None:
        with self.assertRaises(ImageGenRefused) as caught:
            self.client(response={"output_text": "I cannot draw that"}).generate(
                "a depot", task_id="TASK-900"
            )

        self.assertIn("carried no image", str(caught.exception))
        self.assertEqual(caught.exception.accounting["image_cost_usd"], 0.0)
        self.assertEqual([item["status"] for item in self.recorded], ["failed"])

    def test_invalid_base64_refuses(self) -> None:
        with self.assertRaises(ImageGenRefused) as caught:
            self.client(response={"output_image": {"data": "!!!not base64!!!"}}).generate("a depot")
        self.assertIn("not valid base64", str(caught.exception))

    def test_bytes_that_are_not_an_image_refuse(self) -> None:
        with self.assertRaises(ImageGenRefused) as caught:
            self.client(response=response_with_image(b"plain text, not a picture")).generate("a depot")
        self.assertIn("not a readable image", str(caught.exception))

    def test_http_429_is_retried_and_then_refused(self) -> None:
        attempts: list[int] = []

        def urlopen(request, timeout=None):
            attempts.append(1)
            raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", {}, io.BytesIO(b"slow down"))

        client = GeminiImageClient(
            self.root,
            api_key="test-key",
            spend_recorder=self._record,
            month_to_date=lambda: 0.0,
            sleep=lambda _seconds: None,
        )
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(ImageGenRefused) as caught:
                client.generate("a depot", task_id="TASK-900")

        self.assertEqual(len(attempts), 3, "429 is retried to the attempt cap")
        self.assertIn("HTTP 429", str(caught.exception))
        self.assertEqual([item["status"] for item in self.recorded], ["failed"])

    def test_http_400_is_not_retried(self) -> None:
        attempts: list[int] = []

        def urlopen(request, timeout=None):
            attempts.append(1)
            raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b"bad prompt"))

        client = GeminiImageClient(
            self.root,
            api_key="test-key",
            spend_recorder=self._record,
            month_to_date=lambda: 0.0,
            sleep=lambda _seconds: None,
        )
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(ImageGenRefused):
                client.generate("a depot")

        self.assertEqual(len(attempts), 1, "a client error is not worth a second call")

    def test_the_api_key_travels_as_a_header_not_in_the_url(self) -> None:
        seen: list[object] = []

        def urlopen(request, timeout=None):
            seen.append(request)
            raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b""))

        client = GeminiImageClient(
            self.root, api_key="secret-key", month_to_date=lambda: 0.0,
            spend_recorder=self._record, sleep=lambda _s: None,
        )
        with mock.patch("urllib.request.urlopen", urlopen):
            with self.assertRaises(ImageGenRefused):
                client.generate("a depot")

        request = seen[0]
        self.assertNotIn("secret-key", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "secret-key")


class ConversionTest(unittest.TestCase):
    def test_oversized_image_is_downscaled_and_dimensions_reported(self) -> None:
        webp, width, height = to_webp(png_bytes(2400, 1350))
        self.assertEqual((width, height), (1600, 900))
        self.assertEqual(webp[8:12], b"WEBP")

    def test_small_image_is_not_upscaled(self) -> None:
        _webp, width, height = to_webp(png_bytes(800, 450))
        self.assertEqual((width, height), (800, 450))

    def test_unreadable_bytes_refuse(self) -> None:
        with self.assertRaises(ImageGenRefused):
            to_webp(b"\x00\x01\x02not an image")


class PromptTest(unittest.TestCase):
    def test_cover_and_figure_prompts_carry_the_house_rules(self) -> None:
        for builder in (cover_prompt, figure_prompt):
            with self.subTest(builder=builder.__name__):
                prompt = builder("an e-rickshaw parked beside a charging point at dusk")
                self.assertIn("an e-rickshaw parked beside a charging point", prompt)
                self.assertIn("Render NO text", prompt)
                self.assertIn("No recognisable faces", prompt)
                self.assertIn("No real or invented brand marks", prompt)

    def test_cover_and_figure_directions_differ(self) -> None:
        self.assertNotEqual(cover_prompt("a depot"), figure_prompt("a depot"))

    def test_empty_scene_is_refused(self) -> None:
        with self.assertRaises(ImageGenRefused):
            cover_prompt("   ")


class LiveTransportTest(ImageGenTestCase):
    """The real urllib path, over a real socket, against a stand-in for the API.

    Every other test here injects `request_json` and so never executes the
    transport. This one does: it proves the request that leaves the process is the
    one the API documents, and that a documented response comes back as a WebP.
    """

    def test_a_documented_response_over_a_socket_becomes_a_webp(self) -> None:
        received: dict[str, object] = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - http.server's name
                length = int(self.headers.get("Content-Length", "0"))
                received["body"] = json.loads(self.rfile.read(length))
                received["key"] = self.headers.get("x-goog-api-key")
                received["path"] = self.path
                payload = json.dumps(response_with_image(png_bytes(1200, 675))).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_args) -> None:
                return

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)

        endpoint = f"http://127.0.0.1:{server.server_address[1]}/v1beta/interactions"
        with mock.patch.dict("os.environ", {"GEMINI_API_URL": endpoint}, clear=False):
            client = GeminiImageClient(
                self.root,
                api_key="live-transport-key",
                spend_recorder=self._record,
                month_to_date=lambda: 0.0,
            )
            image = client.generate("a depot at dusk", task_id="TASK-900")

        self.assertEqual(received["key"], "live-transport-key")
        self.assertEqual(received["path"], "/v1beta/interactions")
        body = received["body"]
        self.assertEqual(body["model"], DEFAULT_MODEL)
        self.assertEqual(body["input"], [{"type": "text", "text": "a depot at dusk"}])
        self.assertEqual(
            body["response_format"],
            {
                # The API refuses image/png outright; only jpeg comes back.
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "16:9",
                "image_size": "1K",
            },
        )
        self.assertEqual(image.webp[8:12], b"WEBP")
        self.assertEqual((image.width, image.height), (1200, 675))
        self.assertEqual([item["status"] for item in self.recorded], ["estimated"])


if __name__ == "__main__":
    unittest.main()
