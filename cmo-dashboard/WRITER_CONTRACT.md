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

## Article shape

The body is written to a **structural** budget, because that is the only budget a writer can hold to while writing:

```text
an introduction of 2–3 paragraphs
4–6 sections, each with a `##` heading and 2–4 paragraphs
a closing section
`## Decision bullets:` with 3–5 bullets
```

Prose paragraphs run 60–90 words. A section is 2–4 of them, so a section is roughly 150–300 words and the article lands in the band below without anyone counting.

If the approved outline cannot be covered in 4–6 sections, the writer does not extend the article. It returns the `OUTLINE TOO BROAD:` refusal naming what needs a separate article, and the content contract splits the task.

### The band is the validator's check, not the writing instruction

```text
900–1,400 words
```

This is measured in Python after the article exists, and it is not the instruction given to the writer. A model cannot count words while generating them, so a numeric target is unverifiable at the point of writing and enforceable only after the fact — which is how thirteen attempts across three scopings all landed between 1,442 and 1,806 words while being told the number every time.

An article that validates long is **not** regenerated against a smaller number. It is trimmed section by section: the section word counts are measured in Python, the longest sections are identified, and each is handed back to the writer on its own with its current count and the count it must come back at. Cutting one named section by a named amount is a task a writer can do reliably; hitting a global total is not.

## Image-slot declaration

Declare each intended visual at its exact reading position in the Markdown body:

```text
{{image:<slot-id>|<reader-facing caption>}}
```

An article declares **two** slots, of two different kinds:

| Kind | Who makes it | File | Belongs to |
| --- | --- | --- | --- |
| Diagram | the writer, as SVG | `artifacts/<TASK-ID>-<slot-id>.svg` | labels, numbers, steps, comparisons |
| Illustration | the image model, from a scene the writer describes | `artifacts/<TASK-ID>-<slot-id>.webp` | atmosphere, place, the human situation |

Rules:

- `<slot-id>` uses letters, numbers, hyphens, or underscores, starts with a letter or number, and is at most 41 characters.
- A repeated slot ID is rendered once.
- An unbound slot remains a captioned placeholder; it is not silently removed.
- One diagram slot and one illustration slot is the most an article may publish. Two of either kind is refused rather than numbered.
- Bind a committed diagram with board field `Image slot <slot-id>: artifacts/<TASK-ID>-<slot-id>.svg`.
- An illustration also needs `Image alt <slot-id>`. A picture with no alt text is refused at publish, because a screen reader would reach it and find nothing.
- Browser uploads remain limited to PNG, JPG/JPEG, WEBP, or GIF and 5 MB. SVG is never accepted through the upload route.

## Describing an image the writer does not draw

Two scenes are written per article: one for the illustration, one for the cover that
goes on the blog card and the social preview. Both are one or two sentences describing
**what is visible** — not what it means, not what it proves.

Nothing measurable goes in a picture. Every number, label, brand, document, screen and
recognisable face belongs in the diagram or the prose. An image model renders text
wrong, and a wrong figure inside a photograph is a fabricated claim that nobody
proofreads. The generator enforces this in the prompt it sends; the writer's job is not
to ask for it in the first place.

Alt text says what the illustration shows, in one line, for a reader who cannot see it.

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

The generated imagery is bound by the pipeline rather than by the writer, in the same
`set_board_fields()` call:

```text
Image slot <slot-id>: artifacts/<TASK-ID>-<slot-id>.webp   # the illustration
Image alt <slot-id>: <one line of alt text>
Image prompt <slot-id>: <the scene it was drawn from>
Cover image: artifacts/<TASK-ID>-cover.webp
Cover prompt: <the scene it was drawn from>
```

A generation that fails binds nothing and does not stop the article: the slot stays
empty, the console shows an unbound frame, and a human can generate or upload one from
the Files tab.

It preserves `Topic stage: approved`, acceptance criteria, and every human-authored field. It does not set approval fields or claim publication.

Lifecycle transitions use `TaskFile.move()` so the physical section and mirrored lifecycle fields change together:

1. Move the accepted card to `In Progress` before execution.
2. Write only the artifact and non-lifecycle fields above.
3. Move completed work to `CMO Review`; this produces the required `pending CMO review` lifecycle state and CMO action tag.

The KPI gate currently blocks step 1 for content work. This contract is readiness work only.
