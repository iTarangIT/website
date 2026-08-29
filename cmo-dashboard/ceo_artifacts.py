from __future__ import annotations

import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import ceo_reader
from cmo_runtime.task_file import TaskFile, TaskFileError

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
COMMITTED_IMAGE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {".svg"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
SLOT_PATTERN = re.compile(r"\{\{image:([a-z0-9][a-z0-9_-]{0,40})(?:\|([^}]+))?\}\}", re.I)


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _resolved_reference(value: str, profile_dir: Path) -> Path | None:
    value = value.strip()
    if not value or value.casefold() in {"none", "n/a", "not attached"}:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = profile_dir / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_file() or not _within(resolved, profile_dir):
        return None
    return resolved


def text_reference(task: dict[str, Any], profile_dir: Path) -> dict[str, Any] | None:
    value = str(task.get("research_brief", "")).strip()
    if not value and not str(task.get("artifact_path", "")).strip():
        value = str(task.get("attachment", "")).strip()
    path = _resolved_reference(value, profile_dir)
    if path is None or path.suffix.casefold() not in TEXT_EXTENSIONS:
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return {"name": path.name, "text": text}


def _front_matter(text: str) -> tuple[dict[str, str], str, str]:
    """One front-matter rule for the whole console — the reader's.

    Three values, not two: the browser's editor needs the header block back as
    text, or the save it posts is refused for having lost it.
    """
    return ceo_reader.split_source(text)


def _slot_key(slot: str) -> str:
    return "image_slot_" + slot.casefold().replace("-", "_")


def image_for(task: dict[str, Any], slot: str, profile_dir: Path) -> Path | None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,40}", slot, re.I):
        return None
    parsed_key = "image_slot_" + slot.casefold()
    value = str(task.get(parsed_key, task.get(_slot_key(slot), ""))).strip()
    path = _resolved_reference(value, profile_dir)
    if path is None or path.suffix.casefold() not in COMMITTED_IMAGE_EXTENSIONS:
        return None
    artifacts = profile_dir / "artifacts"
    return path if _within(path, artifacts) else None


def cover_for(task: dict[str, Any], profile_dir: Path) -> Path | None:
    """The article's cover image, which lives on the card rather than in the body.

    Deliberately not an `Image slot`: the cover is never placed in the prose, it
    goes on the blog card and the social preview. Keeping it a separate field also
    keeps a body slot that happens to be called `cover` from shadowing it.
    """
    value = str(task.get("cover_image", "")).strip()
    path = _resolved_reference(value, profile_dir)
    if path is None or path.suffix.casefold() not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    return path if _within(path, profile_dir / "artifacts") else None


def generate_image(
    profile_dir: Path,
    task_id: str,
    slot: str,
    scene: str,
    *,
    alt_text: str = "",
    client: Any | None = None,
) -> dict[str, Any]:
    """Render one image for a card from a scene a human just typed or edited.

    The same generator the write stage uses, reached by hand. It writes the
    artifact and rebinds the board field in one step, so a regenerated picture is
    bound the moment it exists rather than leaving the card pointing at the one it
    replaced.
    """
    from cmo_runtime import content_flow, image_gen

    if not re.fullmatch(r"TASK-[0-9]+", task_id):
        raise TaskFileError("valid task ID is required")
    is_cover = slot.casefold() == "cover"
    if not is_cover and not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,40}", slot, re.I):
        raise TaskFileError("image slot must use letters, numbers, hyphens, or underscores")
    slot = slot.casefold()
    scene = " ".join(str(scene).split())
    if not scene:
        raise TaskFileError("describe the image before generating it")
    alt_text = " ".join(str(alt_text).split())[:300]
    if not is_cover and not alt_text:
        # The publisher refuses a picture with no alt text, so generating one
        # without it would buy an image that can never be published.
        raise TaskFileError("alt text is required for an in-article illustration")

    tasks_path = profile_dir / "tasks.md"
    if not tasks_path.is_file():
        raise TaskFileError("tasks.md is unavailable")

    try:
        generator = client or image_gen.GeminiImageClient(profile_dir)
        prompt = (image_gen.cover_prompt if is_cover else image_gen.figure_prompt)(scene)
        generated = generator.generate(prompt, task_id=task_id)
    except image_gen.ImageGenRefused as refusal:
        raise TaskFileError(str(refusal)) from refusal

    name = f"{task_id}-cover.webp" if is_cover else f"{task_id}-{slot}.webp"
    destination = content_flow._safe_artifact(profile_dir, name)
    content_flow._atomic_artifact_set({destination: generated.webp})

    reference = f"artifacts/{destination.name}"
    fields = (
        {"Cover image": reference, "Cover prompt": scene[:400]}
        if is_cover
        else {
            f"Image slot {slot}": reference,
            f"Image alt {slot}": alt_text,
            f"Image prompt {slot}": scene[:400],
        }
    )
    TaskFile(tasks_path, lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id, fields
    )
    return {
        "ok": True,
        "slot": slot,
        "filename": destination.name,
        "url": f"/ceo/image?task={task_id}&slot={slot}",
        "cost_usd": round(float(getattr(generated, "estimated_cost_usd", 0.0)), 6),
    }


def artifact_payload(task: dict[str, Any], artifact: Path, profile_dir: Path) -> dict[str, Any]:
    try:
        text = artifact.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    metadata, front_matter, body = _front_matter(text)
    words = re.findall(r"\b[\w’'-]+\b", body)
    slots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in SLOT_PATTERN.finditer(body):
        slot = match.group(1).casefold()
        if slot in seen:
            continue
        seen.add(slot)
        bound = image_for(task, slot, profile_dir)
        slots.append(
            {
                "id": slot,
                "caption": (match.group(2) or slot.replace("-", " ").title()).strip(),
                "bound": bound is not None,
                "url": f"/ceo/image?task={task['id']}&slot={slot}" if bound else "",
                "filename": bound.name if bound else "",
                "prompt": str(task.get(f"image_prompt_{slot}", "")).strip(),
                "alt": str(task.get(f"image_alt_{slot}", "")).strip(),
                "kind": "diagram" if bound and bound.suffix.casefold() == ".svg" else "illustration",
            }
        )
    cover_path = cover_for(task, profile_dir)
    cover = {
        "id": "cover",
        "caption": "Cover image — blog card and social preview",
        "bound": cover_path is not None,
        "url": f"/ceo/image?task={task['id']}&slot=cover" if cover_path else "",
        "filename": cover_path.name if cover_path else "",
        "prompt": str(task.get("cover_prompt", "")).strip(),
        "alt": "",
        "kind": "cover",
    }
    files = [{"name": artifact.name, "kind": "article", "bytes": artifact.stat().st_size}]
    for slot in slots:
        bound = image_for(task, slot["id"], profile_dir)
        if bound is not None:
            files.append({"name": bound.name, "kind": f"image:{slot['id']}", "bytes": bound.stat().st_size})
    if cover_path is not None:
        files.append({"name": cover_path.name, "kind": "image:cover", "bytes": cover_path.stat().st_size})
    # The reader is rendered here, in Python, so a test can assert on the HTML the
    # console actually shows. The browser only injects and hydrates it.
    rendered = ceo_reader.render_article(body, slots, cover)
    return {
        "text": body,
        # The header block, kept beside the body rather than folded into `text`.
        # `text` is the prose the Blogs search box reads and the reader renders, and
        # a test asserts the slug never reaches it; the editor concatenates the two
        # to get the file back byte for byte.
        "front_matter": front_matter,
        "metadata": metadata,
        "html": rendered["html"],
        "review_notes_html": rendered["review_notes_html"],
        "review_note_titles": rendered["review_note_titles"],
        "word_count": len(words),
        "read_minutes": max(1, math.ceil(len(words) / 220)) if words else 0,
        "image_slots": slots,
        "cover": cover,
        "files": files,
        "revisions": _revisions(artifact),
    }


def _revisions(artifact: Path) -> list[dict[str, Any]]:
    """Previous versions kept beside the article as `<stem>.r<n>.md`."""
    found: list[dict[str, Any]] = []
    for path in artifact.parent.glob(f"{artifact.stem}.r*{artifact.suffix}"):
        match = re.fullmatch(rf"{re.escape(artifact.stem)}\.r(\d+)", path.stem)
        if match is None:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        found.append({"round": int(match.group(1)), "name": path.name, "bytes": size})
    return sorted(found, key=lambda item: item["round"])


def save_upload(
    profile_dir: Path,
    task_id: str,
    slot: str,
    filename: str,
    payload: bytes,
) -> Path:
    if not re.fullmatch(r"TASK-[0-9]+", task_id):
        raise TaskFileError("valid task ID is required")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,40}", slot, re.I):
        raise TaskFileError("image slot must use letters, numbers, hyphens, or underscores")
    if not filename or Path(filename).name != filename:
        raise TaskFileError("a plain image filename is required")
    extension = Path(filename).suffix.casefold()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise TaskFileError("image type is not allowed; use PNG, JPG, JPEG, WEBP, or GIF (SVG is not allowed)")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise TaskFileError("image exceeds the 5 MB upload limit")
    if not payload:
        raise TaskFileError("image upload is empty")
    tasks_path = profile_dir / "tasks.md"
    if not tasks_path.is_file():
        raise TaskFileError("tasks.md is unavailable")
    import dashboard_server

    task = next(
        (item for item in dashboard_server.parse_tasks(tasks_path.read_text(encoding="utf-8")) if item["id"] == task_id),
        None,
    )
    if task is None:
        raise TaskFileError(f"task not found: {task_id}")
    uploads = profile_dir / "artifacts" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    destination = uploads / f"{task_id}-{slot.casefold()}{extension}"
    descriptor, temporary = tempfile.mkstemp(prefix=destination.name + ".", dir=uploads)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        directory_fd = os.open(uploads, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    relative = destination.relative_to(profile_dir).as_posix()
    TaskFile(tasks_path, lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {f"Image slot {slot.casefold()}": relative},
    )
    return destination
