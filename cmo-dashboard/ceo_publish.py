"""Gate 2 — mechanical execution of an authenticated human's publish instruction.

Nothing here decides anything. `preflight` reports whether a human *may* be
offered the instruction; `publish` executes one single-use instruction that a
human has already given. No agent, scheduler or lifecycle check may call
`publish`: it consumes a request ID that only a human page render can mint.

See SOUL.md section 12 clause 4.
"""
from __future__ import annotations

import fcntl
import json
import os
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

BRANCH = "cmo-changes"
BASE = "main"
REPO = os.getenv("CMO_GITHUB_REPO", "iTarangIT/website")


class PublicationRefused(RuntimeError):
    """A fail-closed refusal that is safe to show a human operator."""


class PublicationConflict(PublicationRefused):
    """State moved under the instruction. The caller must answer HTTP 409."""


class GitHub(Protocol):
    def ref_sha(self, ref: str) -> str: ...
    def can_merge(self) -> bool: ...
    def merge(self, *, base: str, head: str, message: str) -> str: ...


class GitHubAPI:
    """The configured repository credential. A deployment mechanism, not authority."""

    def __init__(self, token: str | None = None, repo: str = REPO) -> None:
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        self.repo = repo

    def _call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        if not self.token:
            raise PublicationRefused("no repository credential is configured")
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        call = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(call, timeout=30) as response:
            return json.loads(response.read() or b"null")

    def ref_sha(self, ref: str) -> str:
        return str(self._call("GET", f"/commits/{ref}")["sha"]).lower()

    def can_merge(self) -> bool:
        permissions = (self._call("GET", "") or {}).get("permissions") or {}
        return bool(permissions.get("push") or permissions.get("maintain") or permissions.get("admin"))

    def merge(self, *, base: str, head: str, message: str) -> str:
        try:
            result = self._call("POST", "/merges", {"base": base, "head": head, "commit_message": message})
        except urllib.error.HTTPError as error:
            if error.code in (409, 404, 422):
                raise PublicationConflict(f"GitHub refused the merge ({error.code})") from error
            raise PublicationRefused(f"GitHub merge failed ({error.code})") from error
        if result is None:  # already merged; nothing to do
            raise PublicationConflict("branch is already merged into the base")
        return str(result["sha"]).lower()


@dataclass(frozen=True)
class Preflight:
    task_id: str
    eligible: bool
    blockers: list[str] = field(default_factory=list)
    commit: str = ""
    base_sha: str = ""
    preview_url: str = ""
    approver: str = ""
    comparison: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "eligible": self.eligible,
            "blockers": list(self.blockers),
            "commit": self.commit,
            "base_sha": self.base_sha,
            "preview_url": self.preview_url,
            "approver": self.approver,
            "comparison": list(self.comparison),
        }


def _metrics(profile_dir: Path, task_id: str, phase: str) -> dict[str, Any] | None:
    path = profile_dir / "state" / "website-metrics" / f"{task_id}.{phase}.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(value, dict) or value.get("status") != "captured":
        return None
    return value if isinstance(value.get("pages"), list) and value["pages"] else None


def _comparison(baseline: dict[str, Any], preview: dict[str, Any]) -> list[dict[str, Any]]:
    """Pair baseline and preview Lighthouse scores by URL path, readably."""
    def by_path(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
        paired: dict[str, dict[str, Any]] = {}
        for page in report["pages"]:
            url = str(page.get("url", ""))
            path = "/" + url.split("//", 1)[-1].split("/", 1)[-1].strip("/") if "//" in url else url
            paired[path.rstrip("/") or "/"] = page.get("metrics") or {}
        return paired

    before, after = by_path(baseline), by_path(preview)
    rows: list[dict[str, Any]] = []
    for path in sorted(set(before) & set(after)):
        rows.append({
            "path": path,
            "performance_before": before[path].get("performance_score"),
            "performance_after": after[path].get("performance_score"),
            "weight_before": before[path].get("page_weight_bytes"),
            "weight_after": after[path].get("page_weight_bytes"),
        })
    return rows


def preflight(
    profile_dir: str | Path,
    task_id: str,
    *,
    github: GitHub,
    branch: str = BRANCH,
    base: str = BASE,
) -> Preflight:
    """Report whether a human may be offered the publish instruction, and why not."""
    from cmo_runtime import decisions

    profile_dir = Path(profile_dir)
    import dashboard_server

    tasks = dashboard_server.parse_tasks((profile_dir / "tasks.md").read_text(encoding="utf-8"))
    card = next((item for item in tasks if item["id"] == task_id), None)
    if card is None:
        return Preflight(task_id, False, [f"no such task: {task_id}"])

    blockers: list[str] = []
    if str(card.get("change_type", "")).strip().casefold() != "website":
        blockers.append("this card is not a website change")

    record = decisions.decision_record(profile_dir, task_id)
    approved = bool(record and record.get("decision") == "approve")
    if not approved:
        blockers.append("no Gate 1 approval is recorded for this card")

    commit = str(record.get("commit_sha", "")).lower() if record else ""
    card_commit = str(card.get("commit_hash(es)", card.get("commit", ""))).strip().lower()
    if approved and not commit:
        blockers.append("the Gate 1 approval carries no commit")
    elif approved and card_commit and commit != card_commit:
        blockers.append(f"card commit {card_commit} does not match the approved commit {commit}")

    preview_url = str(card.get("preview_url", "")).strip()
    if not preview_url:
        blockers.append("no preview deployment is recorded")

    recorded_base = str(card.get("preview_base", "")).strip().lower()
    if not recorded_base:
        blockers.append("the preview base commit was not recorded")

    baseline = _metrics(profile_dir, task_id, "baseline")
    preview_metrics = _metrics(profile_dir, task_id, "preview")
    if baseline is None or preview_metrics is None:
        blockers.append("baseline-to-preview Lighthouse evidence is missing or incomplete")

    # Live re-reads. Any failure is a blocker, never an assumption of success.
    head_sha = base_sha = ""
    try:
        head_sha = github.ref_sha(branch)
        base_sha = github.ref_sha(base)
    except PublicationRefused as error:
        blockers.append(str(error))
    except Exception as error:  # noqa: BLE001 - surfaced to the operator verbatim
        blockers.append(f"could not read remote refs: {error}")
    else:
        if commit and head_sha != commit:
            blockers.append(f"branch moved: approved {commit[:7]}, {branch} is now {head_sha[:7]}")
        if recorded_base and base_sha != recorded_base:
            blockers.append(f"{base} moved since the preview was built; rebuild and reapprove")

    try:
        if not github.can_merge():
            blockers.append("the configured repository credential cannot merge")
    except Exception as error:  # noqa: BLE001
        blockers.append(f"could not verify credential permission: {error}")

    comparison = _comparison(baseline, preview_metrics) if baseline and preview_metrics else []
    return Preflight(
        task_id=task_id,
        eligible=not blockers,
        blockers=blockers,
        commit=commit,
        base_sha=base_sha,
        preview_url=preview_url,
        approver=str(record.get("approver_id", "")) if record else "",
        comparison=comparison,
    )


def _requests_path(profile_dir: Path) -> Path:
    return profile_dir / "state" / "publication-requests.json"


def issue_request(profile_dir: str | Path, task_id: str, *, actor: str, commit: str) -> str:
    """Mint a single-use instruction ID. Only a human page render calls this."""
    profile_dir = Path(profile_dir)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a publish instruction requires an authenticated human")
    request_id = secrets.token_urlsafe(24)
    path = _requests_path(profile_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _locked(profile_dir):
        pending = _read_json(path)
        pending[request_id] = {
            "task_id": task_id,
            "actor": actor,
            "commit": commit.lower(),
            "issued_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _write_json(path, pending)
    return request_id


def publish(
    profile_dir: str | Path,
    task_id: str,
    *,
    actor: str,
    role: str,
    request_id: str,
    github: GitHub,
    branch: str = BRANCH,
    base: str = BASE,
) -> dict[str, Any]:
    """Execute one authenticated human's single-use publish instruction."""
    from cmo_runtime.task_file import TaskFile

    profile_dir = Path(profile_dir)
    actor = actor.strip()
    if not actor:
        raise PublicationRefused("a publish instruction requires an authenticated human")

    # Consume the instruction first: a replay must not even reach the re-check.
    with _locked(profile_dir):
        path = _requests_path(profile_dir)
        pending = _read_json(path)
        instruction = pending.pop(request_id, None)
        if instruction is None:
            raise PublicationConflict("this publish instruction is unknown or already used")
        _write_json(path, pending)
    if instruction["task_id"] != task_id or instruction["actor"] != actor:
        raise PublicationConflict("this publish instruction was issued for a different human or card")

    # Re-check everything immediately before merging.
    check = preflight(profile_dir, task_id, github=github, branch=branch, base=base)
    if not check.eligible:
        raise PublicationConflict("; ".join(check.blockers))
    if check.commit != instruction["commit"]:
        raise PublicationConflict("the approved commit changed after the instruction was issued")

    message = (
        f"Publish {task_id} to production\n\n"
        f"Merges {branch} at {check.commit[:7]} into {base}.\n"
        f"Gate 1 approved by {check.approver}.\n\n"
        f"Published-by: {actor}\n"
        f"Published-via: CEO console ({role})\n"
        f"Publication-request: {request_id}\n"
    )
    outcome: dict[str, Any] = {
        "event": "publication",
        "task_id": task_id,
        "actor": actor,
        "role": role,
        "request_id": request_id,
        "approved_commit": check.commit,
        "observed_head": check.commit,
        "observed_base": check.base_sha,
        "preview_url": check.preview_url,
        "evidence": f"state/website-metrics/{task_id}",
        "credential": f"repository credential for {REPO}",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        merge_sha = github.merge(base=base, head=check.commit, message=message)
    except PublicationRefused as error:
        outcome.update({"result": "refused", "reason": str(error)})
        _append_log(profile_dir, outcome)
        raise
    outcome.update({"result": "merged", "merge_commit": merge_sha})
    _append_log(profile_dir, outcome)

    TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {
            "Change status": "merged to main",
            "Published by": actor,
            "Published at": outcome["timestamp"],
            "Merge commit": merge_sha,
        },
    )
    return outcome


def _locked(profile_dir: Path):
    from contextlib import contextmanager

    @contextmanager
    def guard():
        lock = profile_dir / "state" / "tasks.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.touch(exist_ok=True)
        with lock.open("r+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    return guard()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_log(profile_dir: Path, event: dict[str, Any]) -> None:
    """approvals.log is the authoritative record of who instructed a publication."""
    log = profile_dir / "logs" / "approvals.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
