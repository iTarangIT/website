"""The one definition of an in-article image marker.

There were two, and they disagreed. `ceo_artifacts.SLOT_PATTERN` accepted an
underscore in a slot id and made the caption optional; `content_flow.IMAGE_MARKER`
-- which the publisher imports -- allowed hyphens only and required the caption.
A slot named `swap_loop`, or one written without a caption, therefore appeared in
the console's Files tab with an upload button and was invisible to the publisher:
a picture a human could bind to a slot that could never publish.

`WRITER_CONTRACT.md` already documents the permissive charset, so that is what
this accepts. The caption stays required, because the publisher renders it into
the `<figcaption>` and a figure with no caption is not publishable either way --
refusing it in both places is the point.

This module is deliberately import-free: `ceo_artifacts` runs in the dashboard
tree and cannot afford to pull `content_flow` (and Pillow, through `image_gen`)
at module scope just to read a regex.
"""

from __future__ import annotations

import re

#: `{{image:<slot-id>|<caption>}}` at its exact reading position in the body.
#: Group 1 is the slot id, group 2 the caption.
IMAGE_MARKER = re.compile(r"\{\{image:([a-z0-9][a-z0-9_-]{0,40})\|([^}]+)\}\}", re.I)

#: The charset a slot id must match on its own -- the same one the marker embeds.
#: Used where a slot arrives as a bare value rather than inside a marker: an
#: upload's query string, a generate request, a board field name.
SLOT_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,40}", re.I)

#: The one slot id that is not a body marker. The cover has no reading position:
#: it goes on the blog card and the social preview, and lives on its own board
#: fields so a body slot that happens to be called `cover` cannot shadow it.
COVER_SLOT = "cover"

#: The most image slots one article may declare. Two of these are a diagram and
#: an illustration in the common case; the cap is on slots, not on kinds, because
#: files are named by slot id and so two of a kind cannot collide.
MAX_IMAGE_SLOTS = 4
