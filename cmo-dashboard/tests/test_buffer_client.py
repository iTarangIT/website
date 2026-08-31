"""The Buffer client: what it sends per platform, and what it refuses.

Nothing here touches the network. `transport` is the seam — it is handed the URL,
the headers and the request body, and returns whatever the test wants Buffer to
have said. So a failure here means the request we build moved, never that Buffer
was down.

The per-platform shape is the point. Buffer rejects the wrong one with a generic
400, which is exactly the kind of failure that is discovered by a human pressing
a button rather than by a suite, so every branch is asserted on the argv we send.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime import buffer_client  # noqa: E402
from cmo_runtime.buffer_client import (  # noqa: E402
    SERVICE_TO_PLATFORM,
    BufferClient,
    BufferRefused,
)

ORG = "a" * 24
CHANNEL = "b" * 24
POST = "c" * 24


class Recorder:
    """A fake Buffer that records every call and answers from a queue."""

    def __init__(self, *answers: dict) -> None:
        self.answers = list(answers)
        self.calls: list[dict] = []

    def __call__(self, url, headers, body):
        payload = json.loads(body)
        self.calls.append({"url": url, "headers": dict(headers), "payload": payload})
        return self.answers.pop(0) if self.answers else {"data": {}}

    @property
    def last_input(self) -> dict:
        return self.calls[-1]["payload"]["variables"]["input"]


def success(post_id: str = POST, status: str = "queued", due: str = "2026-09-01T10:00:00Z") -> dict:
    return {
        "data": {
            "createPost": {
                "__typename": "PostActionSuccess",
                "post": {
                    "id": post_id,
                    "status": status,
                    "dueAt": due,
                    "channelService": "linkedin",
                    "text": "copy",
                    "via": "api",
                },
            }
        }
    }


def client(transport: Recorder) -> BufferClient:
    return BufferClient(token="token", organization_id=ORG, transport=transport)


class Configuration(unittest.TestCase):
    def test_a_missing_token_refuses_before_any_call(self):
        with self.assertRaises(BufferRefused) as caught:
            BufferClient(token="", organization_id=ORG)
        self.assertIn("BUFFER_ACCESS_TOKEN", str(caught.exception))

    def test_an_organization_id_that_is_not_one_is_refused_here(self):
        """A malformed id comes back from Buffer as a generic 400, so it is caught here."""
        with self.assertRaises(BufferRefused) as caught:
            BufferClient(token="token", organization_id="my-org")
        self.assertIn("organization id", str(caught.exception))

    def test_the_default_endpoint_is_the_one_buffer_actually_answers_on(self):
        """A wrong host fails as "unreachable", which reads like an outage, not a typo.

        `graphql.buffer.com` does not resolve and `graph.buffer.com` answers 401
        with "Please use api.buffer.com". Both were tried; this is the one that
        returned data, so it is pinned rather than left to be re-guessed.
        """
        self.assertEqual(buffer_client.BUFFER_API_URL, "https://api.buffer.com/graphql")

    def test_the_token_travels_in_a_header_and_never_in_the_url(self):
        recorder = Recorder({"data": {"channels": []}})
        client(recorder).channels()
        call = recorder.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Bearer token")
        self.assertNotIn("token", call["url"])


class Channels(unittest.TestCase):
    def answer(self, *rows) -> dict:
        return {"data": {"channels": list(rows)}}

    def row(self, service: str, **overrides) -> dict:
        base = {
            "id": CHANNEL,
            "name": service,
            "displayName": service.title(),
            "service": service,
            "isDisconnected": False,
            "isLocked": False,
            "isQueuePaused": False,
        }
        base.update(overrides)
        return base

    def test_services_this_console_has_no_copy_for_are_dropped(self):
        recorder = Recorder(
            self.answer(self.row("linkedin"), self.row("pinterest"), self.row("twitter"))
        )
        found = client(recorder).channels()
        self.assertEqual([channel.service for channel in found], ["linkedin", "twitter"])

    def test_buffer_says_twitter_and_the_rest_of_this_codebase_says_x(self):
        recorder = Recorder(self.answer(self.row("twitter")))
        self.assertEqual(client(recorder).channels()[0].platform, "x")
        self.assertEqual(SERVICE_TO_PLATFORM["twitter"], "x")

    def test_a_disconnected_or_locked_channel_is_returned_and_marked_unusable(self):
        """Dropping it would leave the console unable to say why a platform is missing."""
        recorder = Recorder(
            self.answer(self.row("linkedin", isDisconnected=True), self.row("twitter", isLocked=True))
        )
        found = client(recorder).channels()
        self.assertEqual([channel.usable for channel in found], [False, False])
        self.assertEqual(len(found), 2)


class PostShape(unittest.TestCase):
    def test_linkedin_carries_the_link_as_an_attachment_not_in_the_body(self):
        """The attachment is what draws the preview card; a pasted URL is a bare link."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL, platform="linkedin", text="A claim.", link="https://x/y"
        )
        sent = recorder.last_input
        self.assertEqual(sent["metadata"]["linkedin"]["linkAttachment"]["url"], "https://x/y")
        self.assertEqual(sent["text"], "A claim.")
        self.assertEqual(sent["assets"], [])

    def test_an_x_thread_repeats_its_first_item_as_the_outer_text(self):
        """Buffer rejects the pair when they disagree, so they are set from one string."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="x",
            text="ignored",
            thread=("Hook.", "Second.", "  ", "Third."),
        )
        sent = recorder.last_input
        self.assertEqual(sent["text"], "Hook.")
        self.assertEqual(
            sent["metadata"]["twitter"]["thread"],
            [
                {"text": "Hook.", "assets": []},
                {"text": "Second.", "assets": []},
                {"text": "Third.", "assets": []},
            ],
            "every thread item carries `assets`, which the schema marks non-null",
        )

    def test_instagram_without_a_picture_is_refused_here_with_a_reason(self):
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused) as caught:
            client(recorder).create_post(channel_id=CHANNEL, platform="instagram", text="Caption.")
        self.assertIn("needs a picture", str(caught.exception))
        self.assertEqual(recorder.calls, [], "Buffer must not be asked for a post it cannot take")

    def test_instagram_with_a_picture_carries_the_metadata_buffer_requires(self):
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="instagram",
            text="Caption.",
            image_url="https://itarang.com/images/blog/a-cover.webp",
            image_alt="A depot at dusk",
        )
        sent = recorder.last_input
        self.assertEqual(
            sent["assets"],
            [
                {
                    "image": {
                        "url": "https://itarang.com/images/blog/a-cover.webp",
                        "metadata": {"altText": "A depot at dusk"},
                    }
                }
            ],
        )
        self.assertEqual(sent["metadata"]["instagram"], {"type": "post", "shouldShareToFeed": True})

    def test_a_second_instagram_picture_makes_it_a_carousel(self):
        """`InstagramPostMetadataInput.type` is non-null, so the shape is chosen
        here rather than inferred by Buffer from the asset count."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="instagram",
            text="Caption.",
            images=[
                {"url": "https://itarang.com/images/social/a-ig-cover.webp", "alt": "Cover"},
                {"url": "https://itarang.com/images/social/a-ig-1.webp", "alt": "One"},
                {"url": "https://itarang.com/images/social/a-ig-close.webp", "alt": "Close"},
            ],
        )
        sent = recorder.last_input
        self.assertEqual(sent["metadata"]["instagram"]["type"], "carousel")
        self.assertEqual(len(sent["assets"]), 3)

    def test_the_carousel_keeps_the_order_it_was_given(self):
        """Swipe order is the content: the close card cannot arrive second."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="instagram",
            text="Caption.",
            images=[
                {"url": "https://i/1.webp", "alt": "one"},
                {"url": "https://i/2.webp", "alt": "two"},
                {"url": "https://i/3.webp", "alt": "three"},
            ],
        )
        self.assertEqual(
            [asset["image"]["url"] for asset in recorder.last_input["assets"]],
            ["https://i/1.webp", "https://i/2.webp", "https://i/3.webp"],
        )

    def test_one_picture_is_still_a_plain_post_not_a_one_card_carousel(self):
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="instagram",
            text="Caption.",
            images=[{"url": "https://i/1.webp", "alt": "one"}],
        )
        self.assertEqual(recorder.last_input["metadata"]["instagram"]["type"], "post")

    def test_a_carousel_past_instagram_s_ceiling_is_refused_by_number(self):
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused) as caught:
            client(recorder).create_post(
                channel_id=CHANNEL,
                platform="instagram",
                text="Caption.",
                images=[{"url": f"https://i/{n}.webp", "alt": str(n)} for n in range(11)],
            )
        self.assertIn("at most 10", str(caught.exception))
        self.assertEqual(recorder.calls, [], "Buffer was asked for a post it cannot take")

    def test_an_image_with_no_alt_text_omits_metadata_rather_than_sending_empty(self):
        """`ImageMetadataInput.altText` is non-null; an empty string is a 400."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL, platform="instagram", text="C.",
            images=[{"url": "https://i/1.webp", "alt": ""}],
        )
        self.assertEqual(recorder.last_input["assets"], [{"image": {"url": "https://i/1.webp"}}])

    def test_an_image_buffer_could_never_fetch_is_refused_before_the_call(self):
        """Buffer fetches over the internet, so a profile-local path is not an image."""
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused) as caught:
            client(recorder).create_post(
                channel_id=CHANNEL, platform="instagram", text="C.",
                images=[{"url": "/opt/data/profiles/itarang_cmo/artifacts/a.webp", "alt": "a"}],
            )
        self.assertIn("over the internet", str(caught.exception))
        self.assertEqual(recorder.calls, [])

    def test_the_x_infographic_rides_the_first_thread_item(self):
        """The first item has to earn the rest of the thread, so it carries the picture."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="x",
            text="ignored",
            thread=("Hook.", "Second."),
            images=[{"url": "https://i/x.webp", "alt": "The claim"}],
        )
        thread = recorder.last_input["metadata"]["twitter"]["thread"]
        self.assertEqual(len(thread[0]["assets"]), 1)
        self.assertEqual(thread[0]["assets"][0]["image"]["url"], "https://i/x.webp")
        self.assertEqual(thread[1]["assets"], [], "the picture was repeated down the thread")

    def test_a_linkedin_infographic_replaces_the_link_preview_card(self):
        """LinkedIn renders one or the other. The image wins; `social_copy` has
        already put the URL in the body text."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL,
            platform="linkedin",
            text="A claim. Read it: https://x/y",
            link="https://x/y",
            images=[{"url": "https://i/li.webp", "alt": "The claim"}],
        )
        sent = recorder.last_input
        self.assertEqual(len(sent["assets"]), 1)
        self.assertNotIn(
            "linkedin", sent.get("metadata", {}),
            "the preview card and the image cannot both be rendered",
        )

    def test_linkedin_without_an_infographic_still_gets_its_preview_card(self):
        """The behaviour every existing article relies on is unchanged."""
        recorder = Recorder(success())
        client(recorder).create_post(
            channel_id=CHANNEL, platform="linkedin", text="A claim.", link="https://x/y"
        )
        self.assertEqual(
            recorder.last_input["metadata"]["linkedin"]["linkAttachment"]["url"], "https://x/y"
        )

    def test_every_post_joins_the_queue_and_needs_no_approval_in_buffer(self):
        """The approval happened in the console. A second one in Buffer would strand it."""
        recorder = Recorder(success())
        client(recorder).create_post(channel_id=CHANNEL, platform="linkedin", text="Copy.")
        sent = recorder.last_input
        self.assertEqual(sent["mode"], "addToQueue")
        self.assertEqual(sent["schedulingType"], "automatic")
        self.assertIs(sent["needsApproval"], False)
        self.assertEqual(sent["source"], "itarang-cmo-console")


class Refusals(unittest.TestCase):
    def test_a_union_error_member_becomes_a_refusal_carrying_buffers_words(self):
        recorder = Recorder(
            {
                "data": {
                    "createPost": {
                        "__typename": "LimitReachedError",
                        "message": "You have reached your scheduled post limit.",
                    }
                }
            }
        )
        with self.assertRaises(BufferRefused) as caught:
            client(recorder).create_post(channel_id=CHANNEL, platform="linkedin", text="Copy.")
        self.assertIn("scheduled post limit", str(caught.exception))

    def test_a_graphql_errors_array_is_a_refusal_not_a_silent_empty_result(self):
        recorder = Recorder({"errors": [{"message": "Not authorised"}], "data": None})
        with self.assertRaises(BufferRefused) as caught:
            client(recorder).channels()
        self.assertIn("Not authorised", str(caught.exception))

    def test_an_unknown_platform_never_reaches_the_wire(self):
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused):
            client(recorder).create_post(channel_id=CHANNEL, platform="tiktok", text="Copy.")
        self.assertEqual(recorder.calls, [])

    def test_empty_copy_is_refused_rather_than_posted(self):
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused):
            client(recorder).create_post(channel_id=CHANNEL, platform="linkedin", text="   ")
        self.assertEqual(recorder.calls, [])

    def test_share_now_is_not_reachable_from_this_client(self):
        """The agreed posture is the queue. A mode outside it is refused, not passed on."""
        recorder = Recorder(success())
        with self.assertRaises(BufferRefused):
            client(recorder).create_post(
                channel_id=CHANNEL, platform="linkedin", text="Copy.", mode="shareNow"
            )
        self.assertEqual(recorder.calls, [])


class Metrics(unittest.TestCase):
    def test_metrics_come_back_keyed_with_the_freshness_beside_them(self):
        """A zero eight hours old and a real zero read the same without the stamp."""
        recorder = Recorder(
            {
                "data": {
                    "post": {
                        "id": POST,
                        "status": "sent",
                        "sentAt": "2026-09-01T10:00:00Z",
                        "dueAt": "2026-09-01T10:00:00Z",
                        "externalLink": "https://linkedin.com/feed/update/1",
                        "metricsUpdatedAt": "2026-09-02T04:00:00Z",
                        "metrics": [
                            {"name": "impressions", "value": 412.0},
                            {"name": "reactions", "value": 9.0},
                            {"name": "unreported", "value": None},
                        ],
                    }
                }
            }
        )
        read = client(recorder).post_metrics(POST)
        # `unreported` is absent, not zero: this console draws those differently.
        self.assertEqual(read["metrics"], {"impressions": 412.0, "reactions": 9.0})
        self.assertEqual(read["metrics_updated_at"], "2026-09-02T04:00:00Z")


if __name__ == "__main__":
    unittest.main()
