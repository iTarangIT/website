#!/usr/bin/env python3
"""Preview deployment and page evidence for the CMO website workflow.

All credentials are environment-only. The module is intentionally usable from
both the dashboard approval process and the hourly cycle without an always-on
worker.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

REPO = Path(os.getenv("CMO_DASHBOARD_GIT_REPO", "/opt/data/work/itarang-website"))
STATE = Path(os.getenv("CMO_DASHBOARD_PROFILE_DIR", "/opt/data/profiles/itarang_cmo")) / "state"
METRICS_DIR = STATE / "website-metrics"
SPEND_TRACKER = Path(os.getenv("CMO_SPEND_TRACKER", "/opt/data/profiles/itarang_cmo/scripts/spend-tracker.py"))
PREVIEW_HOOK_URL = os.getenv("VERCEL_DEPLOY_HOOK_URL", "").strip()
PREVIEW_URL = os.getenv("CMO_PREVIEW_URL", "https://itarangwebsite.vercel.app").strip().rstrip("/")
LIVE_URL = os.getenv("CMO_LIVE_URL", "https://itarang.com").strip().rstrip("/")
DISCORD_WEBHOOK_URL = os.getenv("CMO_DISCORD_WEBHOOK_URL", "").strip()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def live_url() -> str:
    """Return the configured production URL for reviewer links and evidence."""
    return os.getenv("CMO_LIVE_URL", LIVE_URL).strip().rstrip("/")


def affected_pages(task: dict[str, Any]) -> list[str]:
    """Read page URLs from the task card; never invent a measurement target."""
    for key in ("affected_pages", "page_urls", "urls", "pages"):
        raw = str(task.get(key, "")).strip()
        if raw:
            return [item for item in re.split(r"[\s,]+", raw) if item.startswith(("http://", "https://"))]
    return []


def _record_spend(task_id: str, provider: str, model: str, status: str = "unknown") -> None:
    if not SPEND_TRACKER.exists():
        return
    subprocess.run(
        [str(SPEND_TRACKER), "record", "--provider", provider, "--model", model,
         "--task-id", task_id, "--cost", "none", "--status", status],
        check=False, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _lighthouse(url: str, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    binary = os.getenv("LIGHTHOUSE_BIN", "npx")
    command = [binary]
    if Path(binary).name == "npx":
        command.append("--yes")
    command += [
        "lighthouse", url, "--quiet", "--output=json", "--output-path=stdout",
        "--chrome-flags=--headless --no-sandbox", "--only-categories=performance,seo",
    ]
    result = runner(command, capture_output=True, text=True, timeout=180, check=True)
    report = json.loads(result.stdout)
    audits = report.get("audits", {})
    categories = report.get("categories", {})
    performance = categories.get("performance", {}).get("score")
    load_ms = report.get("timing", {}).get("total")
    weight = audits.get("total-byte-weight", {}).get("numericValue")
    seo_audits = {
        key: {
            "score": value.get("score"),
            "display_value": value.get("displayValue"),
            "details": value.get("details"),
        }
        for key, value in audits.items()
        if key in {"document-title", "meta-description", "h1", "heading-order", "canonical", "robots-txt"}
    }
    return {
        "url": url,
        "performance_score": round(performance * 100, 2) if isinstance(performance, (int, float)) else None,
        "load_time_ms": load_ms,
        "page_weight_bytes": weight,
        "seo": seo_audits,
    }


def capture_metrics(task: dict[str, Any], phase: str, runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    task_id = str(task.get("id", "unknown"))
    urls = affected_pages(task)
    result: dict[str, Any] = {"task_id": task_id, "phase": phase, "captured_at": now(), "pages": []}
    result["requested_seo_elements"] = task.get("seo_elements", task.get("seo_changes", ""))
    if not urls:
        result["status"] = "blocked"
        result["reason"] = "task has no Affected pages/Page URLs field"
    else:
        try:
            result["pages"] = [_lighthouse(url, runner) for url in urls]
            result["status"] = "captured"
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
            result["status"] = "failed"
            result["reason"] = f"{type(exc).__name__}: {exc}"
        _record_spend(task_id, "lighthouse", "lighthouse-ci", result["status"])
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    path = METRICS_DIR / f"{task_id}.{phase}.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def deploy_preview(task_id: str, commit: str) -> dict[str, Any]:
    """Trigger the preconfigured Vercel hook for the cmo-changes branch."""
    hook_url = os.getenv("VERCEL_DEPLOY_HOOK_URL", "").strip()
    token = os.getenv("VERCEL_TOKEN", "").strip()
    if not hook_url or not token:
        raise RuntimeError("VERCEL_DEPLOY_HOOK_URL and VERCEL_TOKEN must be configured")
    payload = json.dumps({"ref": "cmo-changes", "task_id": task_id, "commit": commit}).encode()
    request = Request(hook_url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
    })
    with urlopen(request, timeout=60) as response:
        status = response.status
    _record_spend(task_id, "vercel", "deploy-hook", "success")
    # Never persist or return the hook response: providers may echo request
    # metadata, and the deploy token must not enter task state or Discord.
    return {"status": status, "preview_url": os.getenv("CMO_PREVIEW_URL", PREVIEW_URL).strip().rstrip("/")}


def evidence_message(task: dict[str, Any], commit: str, preview_url: str = PREVIEW_URL) -> str:
    lines = [str(task.get(f"agent_summary_{n}", "")).strip() for n in (1, 2, 3)]
    lines = [line for line in lines if line]
    while len(lines) < 3:
        lines.append("Review the affected page and confirm the approved scope only.")
    return (f"{task.get('id', 'task')}: visual preview ready\n"
            f"Preview: {preview_url}\nLive: {LIVE_URL}\n"
            f"Commit: {commit}\nWhat to look at:\n- {lines[0]}\n- {lines[1]}\n- {lines[2]}")


def post_discord(task_id: str, message: str) -> None:
    """Post review evidence immediately; never persist webhook responses."""
    webhook = os.getenv("CMO_DISCORD_WEBHOOK_URL", DISCORD_WEBHOOK_URL).strip()
    if not webhook:
        raise RuntimeError("CMO_DISCORD_WEBHOOK_URL must be configured for preview approvals")
    request = Request(webhook, data=json.dumps({"content": message}).encode(), method="POST",
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        if response.status >= 300:
            raise RuntimeError(f"Discord webhook returned HTTP {response.status}")
    _record_spend(task_id, "discord", "webhook", "success")


def compare(baseline: dict[str, Any], live: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for before, after in zip(baseline.get("pages", []), live.get("pages", [])):
        for metric, label in (("page_weight_bytes", "page weight"), ("performance_score", "performance score"), ("load_time_ms", "load time")):
            left, right = before.get(metric), after.get(metric)
            rows.append({"metric": f"{label} · {after.get('url')}", "before": left, "after": right,
                         "delta": right - left if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None})
        seo_before, seo_after = before.get("seo", {}), after.get("seo", {})
        changed = sum(1 for key in set(seo_before) | set(seo_after) if seo_before.get(key) != seo_after.get(key))
        rows.append({"metric": f"SEO elements · {after.get('url')}", "before": seo_before, "after": seo_after, "delta": changed})
    return rows


def weekly_summary(_as_of: dt.date | None = None) -> dict[str, Any]:
    totals = {"page_weight_saved_bytes": 0, "performance_score_delta": 0, "seo_fixes_shipped": 0, "changes": 0}
    for path in METRICS_DIR.glob("*.live.json"):
        task_id = path.name.split(".", 1)[0]
        baseline_path = METRICS_DIR / f"{task_id}.baseline.json"
        if not baseline_path.exists():
            continue
        rows = compare(json.loads(baseline_path.read_text()), json.loads(path.read_text()))
        totals["changes"] += 1
        for row in rows:
            if row["metric"].startswith("page weight") and isinstance(row["delta"], (int, float)):
                totals["page_weight_saved_bytes"] -= row["delta"]
            if row["metric"].startswith("performance score") and isinstance(row["delta"], (int, float)):
                totals["performance_score_delta"] += row["delta"]
            if row["metric"].startswith("SEO elements"):
                totals["seo_fixes_shipped"] += row["delta"] if isinstance(row["delta"], int) else 0
    return totals
