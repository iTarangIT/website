"""Publish to LinkedIn, X and Instagram through Buffer, over Buffer's GraphQL API.

Why Buffer and not the networks directly: three OAuth apps, three review
processes and three token-refresh cycles buy exactly the thing one Buffer
connection already provides. Buffer also owns the posting schedule, so a queued
post lands in the slot the humans chose rather than the minute a cron fired.

Why raw `urllib` and not a client library: the dashboard is stdlib-only and runs
under an interpreter we do not install packages into. The queries here are
written against the live schema — `createPost(input: CreatePostInput!)` returning
the `PostActionPayload` union, `channels(input: ChannelsInput!)` — not against
documentation, and the union is unpacked by `__typename` so an
`InvalidInputError` arrives as a refusal with Buffer's own message rather than as
a `KeyError` three frames away.

Nothing here decides *what* to post. Copy comes from `social_copy`, the decision
to send comes from a human pressing a button in the console, and this module is
the wire.

Configuration, all read through `read_env_value` so the profile `.env` works the
same as the process environment:

    BUFFER_ACCESS_TOKEN     required; from publish.buffer.com/settings/api
    BUFFER_ORGANIZATION_ID  required; the 24-hex organization id
    BUFFER_API_URL          optional; defaults to the public endpoint
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from cmo_runtime.env_file import read_env_value

#: Buffer's GraphQL endpoint. Overridable so tests can point at a local socket.
#:
#: It is `api.buffer.com/graphql`, and the two obvious guesses are both wrong:
#: `graphql.buffer.com` has no DNS record at all, and `graph.buffer.com` resolves
#: but answers every request with
#: `401 {"errors":[{"message":"Please use api.buffer.com"}]}`. A wrong host here
#: fails as "Buffer was unreachable", which reads like an outage rather than a
#: typo, so the value is verified against the live endpoint and not re-guessed.
BUFFER_API_URL = "https://api.buffer.com/graphql"

HTTP_TIMEOUT_SECONDS = 20

#: Buffer ids are 24 lowercase hex characters. Validated before a call rather
#: than after, because a malformed id comes back as a generic 400.
_ID = re.compile(r"\A[a-f0-9]{24}\Z")

#: The services this console posts to. Facebook is deliberately absent: the
#: organisation has no Facebook channel connected, and a platform with no
#: channel is a row that can only ever say "not connected".
SUPPORTED_SERVICES = ("linkedin", "twitter", "instagram")

#: Buffer's `Service` enum value -> the platform key used everywhere else in
#: this codebase (`console_db.CROSSPOST_PLATFORMS`, the console, the copy
#: generator). Buffer still says `twitter`; we say `x`.
SERVICE_TO_PLATFORM = {"linkedin": "linkedin", "twitter": "x", "instagram": "instagram"}
PLATFORM_TO_SERVICE = {value: key for key, value in SERVICE_TO_PLATFORM.items()}

#: Only these two share modes are reachable from the console. `shareNow` and
#: `customScheduled` exist in the schema and are not offered: the agreed
#: posture is that an approved post joins the queue Buffer already schedules.
SHARE_MODES = ("addToQueue", "shareNext")

#: Instagram's own carousel ceiling. Buffer surfaces it as a rejection at send
#: time; refusing here names the number instead of relaying "invalid input".
MAX_CAROUSEL_ASSETS = 10

_CHANNELS_QUERY = """
query ConsoleChannels($input: ChannelsInput!) {
  channels(input: $input) {
    id
    name
    displayName
    service
    type
    isDisconnected
    isLocked
    isQueuePaused
    timezone
  }
}
"""

_CREATE_POST_MUTATION = """
mutation ConsoleCreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    __typename
    ... on PostActionSuccess {
      post { id status dueAt channelService text via }
    }
    ... on InvalidInputError { message }
    ... on NotFoundError { message }
    ... on UnauthorizedError { message }
    ... on LimitReachedError { message }
    ... on UnexpectedError { message }
    ... on RestProxyError { message code }
  }
}
"""

_POST_METRICS_QUERY = """
query ConsolePost($input: PostInput!) {
  post(input: $input) {
    id
    status
    dueAt
    sentAt
    channelService
    externalLink
    metricsUpdatedAt
    metrics { name type unit value }
  }
}
"""


def _image_asset(picture: Mapping[str, str]) -> dict[str, Any]:
    """One `AssetInput` for an image Buffer will fetch over the public internet.

    `ImageMetadataInput.altText` is non-null in the schema, so metadata is either
    omitted entirely or carries real alt text — an empty string is a validation
    error dressed up as politeness.
    """
    url = _clean(picture.get("url"))
    if not url:
        raise BufferRefused("An image was given with no URL for Buffer to fetch.")
    if not url.lower().startswith(("http://", "https://")):
        raise BufferRefused(
            f"Buffer fetches images over the internet, so {url!r} cannot be posted."
        )
    image: dict[str, Any] = {"url": url}
    alt = _clean(picture.get("alt"))
    if alt:
        image["metadata"] = {"altText": alt}
    return {"image": image}


class BufferRefused(RuntimeError):
    """Buffer would not do it, and the message is safe to show an operator.

    Every raise carries Buffer's own wording where there is one. A refusal is
    never turned into a silent no-op: a post the console said it sent and Buffer
    never accepted is the one failure this whole module exists to make visible.
    """


@dataclass(frozen=True)
class BufferChannel:
    """One connected social account."""

    id: str
    name: str
    service: str
    platform: str
    disconnected: bool
    locked: bool
    queue_paused: bool

    @property
    def usable(self) -> bool:
        """Whether a post sent to this channel can actually go out."""
        return not (self.disconnected or self.locked)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "service": self.service,
            "platform": self.platform,
            "disconnected": self.disconnected,
            "locked": self.locked,
            "queue_paused": self.queue_paused,
            "usable": self.usable,
        }


@dataclass(frozen=True)
class BufferPost:
    """A post Buffer accepted."""

    id: str
    status: str
    platform: str
    due_at: str
    text: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "platform": self.platform,
            "due_at": self.due_at,
            "text": self.text,
        }


def _clean(value: Any) -> str:
    return str(value or "").strip()


class BufferClient:
    """A thin, testable wrapper over the three Buffer operations we need.

    `transport` is the injection seam: it takes `(url, headers, body_bytes)` and
    returns the decoded JSON object. Tests pass a fake; nothing else does.
    """

    def __init__(
        self,
        *,
        token: str,
        organization_id: str,
        api_url: str = BUFFER_API_URL,
        transport: Callable[[str, Mapping[str, str], bytes], Mapping[str, Any]] | None = None,
    ) -> None:
        token = _clean(token)
        organization_id = _clean(organization_id)
        if not token:
            raise BufferRefused("BUFFER_ACCESS_TOKEN is not set.")
        if not _ID.match(organization_id):
            raise BufferRefused("BUFFER_ORGANIZATION_ID is not a Buffer organization id.")
        self._token = token
        self._organization_id = organization_id
        self._api_url = api_url or BUFFER_API_URL
        self._transport = transport or self._http

    @classmethod
    def from_profile(
        cls,
        profile_dir: str,
        *,
        transport: Callable[[str, Mapping[str, str], bytes], Mapping[str, Any]] | None = None,
    ) -> "BufferClient":
        """Build a client from the profile environment, refusing clearly if unconfigured."""
        return cls(
            token=read_env_value(profile_dir, "BUFFER_ACCESS_TOKEN"),
            organization_id=read_env_value(profile_dir, "BUFFER_ORGANIZATION_ID"),
            api_url=read_env_value(profile_dir, "BUFFER_API_URL") or BUFFER_API_URL,
            transport=transport,
        )

    @staticmethod
    def configured(profile_dir: str) -> bool:
        """Whether both required variables are present, without reading their values out."""
        return bool(
            read_env_value(profile_dir, "BUFFER_ACCESS_TOKEN")
            and read_env_value(profile_dir, "BUFFER_ORGANIZATION_ID")
        )

    # ---- the wire -------------------------------------------------------

    def _http(self, url: str, headers: Mapping[str, str], body: bytes) -> Mapping[str, Any]:
        request = urllib.request.Request(url, data=body, method="POST", headers=dict(headers))
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                decoded = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace").replace("\n", " ")
            raise BufferRefused(f"Buffer returned HTTP {exc.code}: {detail[:300]}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BufferRefused(f"Buffer was unreachable: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise BufferRefused("Buffer returned a response that was not JSON.") from exc
        if not isinstance(decoded, dict):
            raise BufferRefused("Buffer returned a non-object response.")
        return decoded

    def _call(self, query: str, variables: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps({"query": query, "variables": dict(variables)}).encode("utf-8")
        headers = {
            # Header, never a query parameter: a token in a URL lands in logs.
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = self._transport(self._api_url, headers, body)
        errors = payload.get("errors")
        if errors:
            first = errors[0] if isinstance(errors, list) and errors else {}
            message = _clean(first.get("message") if isinstance(first, Mapping) else "")
            raise BufferRefused(f"Buffer refused the request: {message or 'no message given'}")
        data = payload.get("data")
        if not isinstance(data, Mapping):
            raise BufferRefused("Buffer returned no data.")
        return data

    # ---- operations -----------------------------------------------------

    def channels(self) -> list[BufferChannel]:
        """Every channel on the organization, in a stable platform order.

        Unsupported services are dropped rather than surfaced: a Pinterest board
        on the account is not something this console has copy for.
        """
        data = self._call(_CHANNELS_QUERY, {"input": {"organizationId": self._organization_id}})
        rows = data.get("channels") or []
        if not isinstance(rows, list):
            raise BufferRefused("Buffer returned an unexpected channel list.")
        found: list[BufferChannel] = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            service = _clean(row.get("service")).lower()
            if service not in SERVICE_TO_PLATFORM:
                continue
            found.append(
                BufferChannel(
                    id=_clean(row.get("id")),
                    name=_clean(row.get("displayName")) or _clean(row.get("name")),
                    service=service,
                    platform=SERVICE_TO_PLATFORM[service],
                    disconnected=bool(row.get("isDisconnected")),
                    locked=bool(row.get("isLocked")),
                    queue_paused=bool(row.get("isQueuePaused")),
                )
            )
        order = {platform: index for index, platform in enumerate(SERVICE_TO_PLATFORM.values())}
        found.sort(key=lambda channel: (order.get(channel.platform, 99), channel.name))
        return found

    def create_post(
        self,
        *,
        channel_id: str,
        platform: str,
        text: str,
        link: str = "",
        image_url: str = "",
        image_alt: str = "",
        images: Sequence[Mapping[str, str]] = (),
        thread: Sequence[str] = (),
        mode: str = "addToQueue",
    ) -> BufferPost:
        """Queue one post, and refuse loudly rather than half-send it.

        The per-platform shape is not cosmetic — Buffer rejects the wrong one:

        * Instagram requires at least one asset and a `type`/`shouldShareToFeed`
          metadata block. A caption alone is a 400, so it is refused here with a
          sentence a human can act on instead.
        * X carries the thread in `metadata.twitter.thread`, and the first item
          repeats as the outer `text` — confirmed against a real threaded post
          on the account, whose `thread[0]` equals its `text` — so both are set
          from the same string.
        * LinkedIn takes the link as a `linkAttachment`, which is what produces
          the preview card; putting the URL in the body instead gets a bare link.
        """
        if not _ID.match(_clean(channel_id)):
            raise BufferRefused("That is not a Buffer channel id.")
        if platform not in PLATFORM_TO_SERVICE:
            raise BufferRefused(f"{platform} is not a platform this console posts to.")
        if mode not in SHARE_MODES:
            raise BufferRefused(f"{mode} is not an offered share mode.")
        text = _clean(text)
        if not text:
            raise BufferRefused("There is no copy to post.")

        # One image or many. `image_url`/`image_alt` remain the single-image
        # shorthand every existing caller uses; `images` is how a carousel or an
        # infographic arrives.
        pictures = [dict(item) for item in images]
        if image_url:
            pictures.insert(0, {"url": image_url, "alt": image_alt})
        assets = [_image_asset(picture) for picture in pictures]

        metadata: dict[str, Any] = {}
        if platform == "instagram":
            if not assets:
                raise BufferRefused(
                    "Instagram needs a picture. Publish the article so its cover "
                    "image is reachable, or bind a cover on the Files tab."
                )
            if len(assets) > MAX_CAROUSEL_ASSETS:
                raise BufferRefused(
                    f"Instagram takes at most {MAX_CAROUSEL_ASSETS} cards in a "
                    f"carousel; this one has {len(assets)}."
                )
            # `PostType` carries `carousel`, and `InstagramPostMetadataInput.type`
            # is non-null, so the shape is chosen here rather than inferred by
            # Buffer from the asset count.
            metadata["instagram"] = {
                "type": "carousel" if len(assets) > 1 else "post",
                "shouldShareToFeed": True,
            }
        elif platform == "x":
            items = [item for item in (_clean(part) for part in thread) if item]
            if items:
                # The outer text must equal the first item or Buffer rejects the pair.
                text = items[0]
                # `assets` is `[AssetInput!]!` on every thread item — non-null, so
                # an item without one is a validation error, not a picture-less
                # tweet. The empty list is the "no picture" value.
                #
                # The picture belongs on the first item, which is the one that has
                # to earn the rest of the thread. Outer `assets` is left mirroring
                # it for the same reason outer `text` does.
                metadata["twitter"] = {
                    "thread": [
                        {"text": item, "assets": assets if index == 0 else []}
                        for index, item in enumerate(items)
                    ]
                }
        elif platform == "linkedin":
            # LinkedIn renders a link-preview card OR an image, never both, and
            # `linkAttachment` is what produces the card. So an infographic
            # replaces the preview rather than sitting beside it, and the URL
            # travels in the post text instead — which is where `social_copy`
            # already puts it.
            if link and not assets:
                metadata["linkedin"] = {"linkAttachment": {"url": link}}

        variables = {
            "input": {
                "channelId": channel_id,
                "text": text,
                "assets": assets,
                "mode": mode,
                "schedulingType": "automatic",
                "needsApproval": False,
                "source": "itarang-cmo-console",
                **({"metadata": metadata} if metadata else {}),
            }
        }
        data = self._call(_CREATE_POST_MUTATION, variables)
        result = data.get("createPost")
        if not isinstance(result, Mapping):
            raise BufferRefused("Buffer returned no result for the post.")
        kind = _clean(result.get("__typename"))
        if kind != "PostActionSuccess":
            message = _clean(result.get("message")) or kind or "no message given"
            raise BufferRefused(f"Buffer did not queue the post: {message}")
        post = result.get("post")
        if not isinstance(post, Mapping):
            raise BufferRefused("Buffer accepted the post but returned nothing about it.")
        return BufferPost(
            id=_clean(post.get("id")),
            status=_clean(post.get("status")),
            platform=platform,
            due_at=_clean(post.get("dueAt")),
            text=_clean(post.get("text")) or text,
        )

    def post_metrics(self, post_id: str) -> dict[str, Any]:
        """Read one post back, with whatever metrics Buffer has for it.

        Metrics refresh about daily, so `metrics_updated_at` is returned beside
        them — a zero that is eight hours old and a zero that is real look
        identical without it.
        """
        if not _ID.match(_clean(post_id)):
            raise BufferRefused("That is not a Buffer post id.")
        data = self._call(_POST_METRICS_QUERY, {"input": {"id": post_id}})
        post = data.get("post")
        if not isinstance(post, Mapping):
            return {"id": post_id, "status": "", "metrics": {}, "metrics_updated_at": ""}
        metrics: dict[str, float] = {}
        for row in post.get("metrics") or []:
            if not isinstance(row, Mapping) or not _clean(row.get("name")):
                continue
            value = row.get("value")
            # A metric Buffer did not give a value for is left out, not zeroed.
            # This console renders an absent number as "not yet" and a zero as a
            # measurement, and inventing the second from the first is a lie.
            if value is None:
                continue
            try:
                metrics[_clean(row.get("name"))] = float(value)
            except (TypeError, ValueError):
                continue
        return {
            "id": _clean(post.get("id")) or post_id,
            "status": _clean(post.get("status")),
            "sent_at": _clean(post.get("sentAt")),
            "due_at": _clean(post.get("dueAt")),
            "external_link": _clean(post.get("externalLink")),
            "metrics": metrics,
            "metrics_updated_at": _clean(post.get("metricsUpdatedAt")),
        }
