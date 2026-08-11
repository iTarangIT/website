# Approved Topic → Blog Artifact Contract

This is the writer seam for iTarang content. It does not authorize content generation, approval, publication, or a live website change.

## Input gate

The writer may accept only an existing board card whose exact board field is:

```text
Topic stage: approved
```

The content KPI set must also have human approval recorded for the task. Until that gate is satisfied, the writer does not draft content.

## The one blog-row rule

A card becomes a CEO-console blog row only when its `Attachment` resolves to an existing text artifact beneath the profile's `artifacts/` directory. No separate blog registry exists.

The conventional article path is:

```text
artifacts/<TASK-ID>-content.md
```

The writer must create that artifact first and then set the card's `Attachment` to the same relative path. A title, topic stage, board status, or unattached file never creates a blog row.

## Article format

The artifact is UTF-8 Markdown. It begins with flat front matter that the console can parse:

```text
---
title: <reader-facing title>
meta_title: <search title>
meta_description: <search description>
slug: <proposed-slug>
category: <financing | battery-selection | charging-maintenance | safety | lifecycle-recycling | partners-industry>
audience: <intended reader>
source_urls: <comma-separated dated source URLs>
---
```

The body follows the front matter. The writer keeps claims and source links in the artifact; the console does not infer them from the board.

## Image-slot declaration

Declare each intended visual at its exact reading position in the Markdown body:

```text
{{image:<slot-id>|<reader-facing caption>}}
```

Rules:

- `<slot-id>` uses letters, numbers, hyphens, or underscores, starts with a letter or number, and is at most 41 characters.
- A repeated slot ID is rendered once.
- An unbound slot remains a captioned placeholder; it is not silently removed.
- A writer-produced diagram uses `artifacts/<TASK-ID>-<slot-id>.svg`.
- Bind a committed diagram with board field `Image slot <slot-id>: artifacts/<TASK-ID>-<slot-id>.svg`.
- Browser uploads remain limited to PNG, JPG/JPEG, WEBP, or GIF and 5 MB. SVG is never accepted through the upload route.

## Board fields written by the writer

The writer changes board state only through `TaskFile` methods. It never edits `tasks.md` text directly and never calls `DecisionStore`.

After the artifact and any committed diagrams exist, the writer calls `TaskFile.set_board_fields()` for:

```text
Attachment: artifacts/<TASK-ID>-content.md
Category: <the exact allowed category slug emitted in front matter>
Description: <one-line functional description of the completed article>
Metric: <the approved content KPI and its measurement method>
Image slot <slot-id>: artifacts/<TASK-ID>-<slot-id>.svg   # one per committed diagram, when present
```

It preserves `Topic stage: approved`, acceptance criteria, and every human-authored field. It does not set approval fields or claim publication.

Lifecycle transitions use `TaskFile.move()` so the physical section and mirrored lifecycle fields change together:

1. Move the accepted card to `In Progress` before execution.
2. Write only the artifact and non-lifecycle fields above.
3. Move completed work to `CMO Review`; this produces the required `pending CMO review` lifecycle state and CMO action tag.

The KPI gate currently blocks step 1 for content work. This contract is readiness work only.
