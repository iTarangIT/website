#!/usr/bin/env python3
"""Read-only iTarang CMO monitoring dashboard."""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import fcntl
import html
import json
import os
import re
import secrets
import subprocess
import threading
import time
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from preview_metrics import (METRICS_DIR, affected_pages, capture_metrics, deploy_preview,
                              evidence_message, live_url, post_discord)

PROFILE_DIR = Path(os.getenv('CMO_DASHBOARD_PROFILE_DIR', '/opt/data/profiles/itarang_cmo'))
TASKS_FILE = PROFILE_DIR / 'tasks.md'
STATE_DIR = PROFILE_DIR / 'state'
BOARD_LOCK = STATE_DIR / 'tasks.lock'
APPROVAL_LOG = PROFILE_DIR / 'logs' / 'approvals.log'
ACTIVE_FILE = STATE_DIR / 'hourly-active.json'
HUMAN_APPROVALS = STATE_DIR / 'human-approvals.json'
TMUX_BIN = PROFILE_DIR / 'bin' / 'tmux'
CYCLE_LOG = PROFILE_DIR / 'logs' / 'hourly-cycle.log'
SPEND_LOG = PROFILE_DIR / 'logs' / 'spend.log'
GIT_REPO_DIR = Path(os.getenv('CMO_DASHBOARD_GIT_REPO', str(PROFILE_DIR)))
HOST = os.getenv('CMO_DASHBOARD_HOST', '0.0.0.0')
PORT = int(os.getenv('CMO_DASHBOARD_PORT', '8080'))
SECTION_TO_COLUMN = {
    'Backlog': 'Task List',
    'In Progress': 'Task List',
    'CMO Review': 'Under Review (CMO)',
    'Human Approval': 'Under Review (Human)',
    'Completed': 'Completed',
}


def _ledger_lines(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def spend_total(path: Path = SPEND_LOG) -> float | None:
    records = _ledger_lines(path)
    if not records:
        return None
    return sum(float(item.get('estimated_cost_usd', item.get('cost_usd', 0)) or 0) for item in records)


def approval_count(path: Path = APPROVAL_LOG) -> int:
    return len(_ledger_lines(path))


def git_change_metadata(task: dict[str, Any], repo_dir: Path = GIT_REPO_DIR) -> dict[str, Any]:
    """Read current git evidence at render time; board fields are not evidence."""
    task_id = str(task.get('id', ''))
    try:
        branches = subprocess.run(
            ['git', '-C', str(repo_dir), 'for-each-ref', '--format=%(refname:short)', 'refs/heads/', 'refs/remotes/'],
            capture_output=True, text=True, timeout=3, check=False,
        ).stdout.splitlines()
        log = subprocess.run(
            ['git', '-C', str(repo_dir), 'log', '--all', '--grep', task_id, '-n', '1', '--format=%H%x09%s'],
            capture_output=True, text=True, timeout=3, check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        branches, log = [], ''
    matches = [branch for branch in branches if task_id in branch]
    if not matches and not log:
        return {'branch': '', 'commits': '', 'files_changed': '', 'commit_url': '', 'branch_url': '', 'evidence': 'no branch evidence'}
    commit, _, subject = log.partition('\t')
    return {'branch': matches[0] if matches else '', 'commits': commit, 'files_changed': subject,
            'commit_url': '', 'branch_url': '', 'evidence': 'git evidence'}


def parse_tasks(text: str) -> list[dict[str, Any]]:
    """Parse the owner-facing markdown board without modifying it."""
    tasks: list[dict[str, Any]] = []
    section = ''
    current: dict[str, Any] | None = None
    in_acceptance = False
    in_decision_summary = False

    def finish() -> None:
        nonlocal current
        if current and current.get('id'):
            current.setdefault('title', current['id'])
            current.setdefault('owner', 'unassigned')
            current.setdefault('status', section)
            current.setdefault('latest_summary', '')
            current['board_column'] = SECTION_TO_COLUMN.get(section, section or 'Task List')
            tasks.append(current)
        current = None

    for line in text.splitlines():
        heading = re.match(r'^##\s+(.+?)\s*$', line)
        if heading:
            finish()
            section = heading.group(1).strip()
            in_acceptance = False
            in_decision_summary = False
            continue
        card = re.match(r'^###\s+(TASK-[^\s—-]+)\s+—\s+(.+?)\s*$', line)
        if card:
            finish()
            current = {'id': card.group(1), 'title': card.group(2).strip(), 'acceptance_criteria': [], 'decision_summary': []}
            in_acceptance = False
            in_decision_summary = False
            continue
        if current is None:
            continue
        if re.match(r'^-\s+Acceptance criteria:\s*$', line, re.I):
            in_acceptance = True
            continue
        if re.match(r'^-\s+Decision summary:\s*$', line, re.I):
            in_decision_summary = True
            in_acceptance = False
            continue
        criterion = re.match(r'^\s+-\s+(.+?)\s*$', line)
        if criterion and in_decision_summary:
            current['decision_summary'].append(criterion.group(1).strip())
            continue
        if criterion and in_acceptance:
            current['acceptance_criteria'].append(criterion.group(1).strip())
            continue
        field = re.match(r'^-\s+([A-Za-z0-9][A-Za-z0-9 ()/#-]*):\s*(.*?)\s*$', line)
        if field:
            key = field.group(1).strip().lower().replace(' ', '_').replace('/', '_')
            current[key] = field.group(2)
            in_acceptance = False
            in_decision_summary = False
    finish()
    return tasks


def task_change_metadata(task: dict[str, Any]) -> dict[str, Any]:
    """Combine live git evidence with descriptive fields from the board."""
    evidence = git_change_metadata(task)
    return {
        **evidence,
        'summary_lines': [task.get(f'agent_summary_{n}', '') for n in (1, 2, 3)],
        'change_description': task.get('change_description', ''),
        'change_status': task.get('change_status', ''),
        'diff_summary': task.get('diff_summary', ''),
        'risk_cost': task.get('risk_cost', ''),
        'preview_url': task.get('preview_url', ''),
        'live_url': task.get('live_url', ''),
        'metrics_evidence': task.get('metrics_evidence', ''),
        'metrics_summary': task.get('metrics_summary', ''),
        'metrics_table': task.get('metrics_table', ''),
        'approval_valid': task.get('board_column') != 'Under Review (Human)' or 3 <= len(task.get('decision_summary', [])) <= 5,
    }


def tmux_health(tmux_bin: Path = TMUX_BIN) -> dict[str, str]:
    health: dict[str, str] = {}
    try:
        result = subprocess.run([str(tmux_bin), 'ls'], capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.SubprocessError):
        return health
    for line in result.stdout.splitlines():
        match = re.match(r'^cmo-([^:]+):\s', line)
        if match:
            health[match.group(1)] = 'alive'
    return health


def configured_agents() -> set[str]:
    agents: set[str] = set()
    for dirname in ('dispatch', 'results'):
        root = PROFILE_DIR / dirname
        try:
            agents.update(item.name for item in root.iterdir() if item.is_dir())
        except OSError:
            pass
    return agents


def build_snapshot(tasks_file: Path = TASKS_FILE, tmux_bin: str | Path = TMUX_BIN) -> dict[str, Any]:
    try:
        text = tasks_file.read_text(encoding='utf-8')
        modified = tasks_file.stat().st_mtime
    except OSError as exc:
        text = ''
        modified = None
        read_error = str(exc)
    else:
        read_error = None
    tasks = parse_tasks(text)
    fallback_updated = (
        dt.datetime.fromtimestamp(modified, dt.timezone.utc).replace(microsecond=0).isoformat()
        if modified else ''
    )
    health = tmux_health(Path(tmux_bin))
    for task in tasks:
        task.setdefault('last_updated', fallback_updated)
        task['change'] = task_change_metadata(task)
    cycle_match = re.search(r'(?m)^Last cycle ran:\s*(.*?)\s*$', text)
    if not cycle_match and CYCLE_LOG.exists():
        cycle_lines = CYCLE_LOG.read_text(encoding='utf-8', errors='replace').splitlines()
        timestamps = re.findall(r'(?m)^(20\d{2}-\d{2}-\d{2}T[^ ]+)', '\n'.join(cycle_lines))
        cycle_match_value = timestamps[-1] if timestamps else None
    else:
        cycle_match_value = cycle_match.group(1) if cycle_match else None
    pending_changes = [
        task for task in tasks
        if task.get('status') == 'Human Approval'
        and task.get('change', {}).get('branch')
    ]
    columns = []
    for task in tasks:
        if task['board_column'] not in columns:
            columns.append(task['board_column'])
    agent_names = ({str(task.get('owner', '')).strip().lower() for task in tasks if task.get('owner') and task.get('owner') != 'unassigned'}
                   | set(health) | configured_agents())
    health_names = agent_names | {'watchdog'}
    return {
        'tasks': tasks,
        'pending_changes': pending_changes,
        'last_cycle_ran': cycle_match_value,
        'health': {agent: health.get(agent, 'dead') for agent in sorted(health_names)},
        'agents': sorted(agent_names),
        'board_columns': columns,
        'spend_total': spend_total(SPEND_LOG),
        'approval_count': approval_count(APPROVAL_LOG),
        'tasks_file': str(tasks_file),
        'tasks_mtime': modified,
        'error': read_error,
    }


def valid_basic_auth(header: str | None) -> bool:
    username = os.getenv('CMO_DASHBOARD_USERNAME')
    password = os.getenv('CMO_DASHBOARD_PASSWORD')
    if not username or not password or not header or not header.startswith('Basic '):
        return False
    try:
        raw = base64.b64decode(header[6:], validate=True).decode('utf-8')
        supplied_user, separator, supplied_password = raw.partition(':')
    except (binascii.Error, UnicodeDecodeError):
        return False
    return bool(separator) and secrets.compare_digest(supplied_user, username) and secrets.compare_digest(supplied_password, password)


@contextmanager
def board_lock():
    BOARD_LOCK.parent.mkdir(parents=True, exist_ok=True)
    BOARD_LOCK.touch(exist_ok=True)
    with BOARD_LOCK.open('r+', encoding='utf-8') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _set_card_field(card: str, name: str, value: str) -> str:
    pattern = rf'(?m)^- {re.escape(name)}:\s*.*?$'
    line = f'- {name}: {value}'
    if re.search(pattern, card):
        return re.sub(pattern, line, card, count=1)
    return card.rstrip() + '\n' + line + '\n'


def _move_task(text: str, task_id: str, destination: str, updates: dict[str, str]) -> str:
    heading = re.search(rf'(?m)^### {re.escape(task_id)} — .*?\s*$', text)
    if not heading:
        raise ValueError('task not found')
    next_heading = re.search(r'(?m)^### |^## ', text[heading.end():])
    end = heading.end() + (next_heading.start() if next_heading else len(text) - heading.end())
    card = text[heading.start():end].strip() + '\n\n'
    for name, value in updates.items():
        card = _set_card_field(card, name, value)
    text = text[:heading.start()] + text[end:]
    marker = f'## {destination}\n'
    insert = text.find(marker)
    if insert < 0:
        raise ValueError('destination column not found')
    insert += len(marker)
    remainder = text[insert:]
    empty = re.match(r'\s*_No tasks\._', remainder)
    if empty:
        text = text[:insert] + '\n' + card + remainder[empty.end():]
    else:
        text = text[:insert] + '\n' + card + text[insert:]
    return text


def _queue_approved_work(task_id: str, owner: str, decision: str, comment: str) -> None:
    prompt_dir = PROFILE_DIR / 'dispatch' / owner
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt = prompt_dir / f'{task_id}.dashboard-approval.prompt'
    prompt.write_text(
        f'Human dashboard decision: {decision.upper()}\n'
        f'Task ID: {task_id}\n'
        f'Owner: {owner}\n'
        f'Comment: {comment or "No additional comment."}\n\n'
        'For APPROVE: implement only the approved website change on branch cmo-changes, '
        'use the captured baseline for affected pages, push it, and return the commit hash, changed files, '
        'and a three-line what/why summary. The hourly cycle deploys the branch to the fixed Vercel preview '
        'after the commit; never merge or publish. '
        'For REJECT: revise the work according to the comment and return it to CMO Review. '
        'Do not publish or merge without the required approval.\n',
        encoding='utf-8',
    )
    subprocess.run([str(TMUX_BIN), 'send-keys', '-t', f'cmo-{owner}', f'run {prompt}', 'Enter'], check=True, timeout=30)
    try:
        active = json.loads(ACTIVE_FILE.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        active = {}
    active[task_id] = {
        'owner': owner,
        'dispatched_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        'prompt': str(prompt),
        'implementation': decision == 'approve',
    }
    temporary = ACTIVE_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(active, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(ACTIVE_FILE)


def record_approval(user: str, task_id: str, decision: str, comment: str) -> None:
    APPROVAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    with APPROVAL_LOG.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({
            'timestamp': timestamp, 'user': user, 'task_id': task_id,
            'decision': decision, 'comment': comment,
        }, ensure_ascii=False) + '\n')


def _record_website_approval(task_id: str, owner: str, commit: str, preview_url: str) -> None:
    """Put a Gate 1-approved website change into the merge-waiting state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        active = json.loads(ACTIVE_FILE.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        active = {}
    active[task_id] = {
        'owner': owner,
        'commit': commit,
        'preview_url': preview_url,
        'awaiting_merge': True,
        'approved_at': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    temporary = ACTIVE_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(active, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(ACTIVE_FILE)


def authenticated_user(header: str | None) -> str:
    if not header or not header.startswith('Basic '):
        return ''
    try:
        raw = base64.b64decode(header[6:], validate=True).decode('utf-8')
    except (binascii.Error, UnicodeDecodeError):
        return ''
    return raw.partition(':')[0]


def event_signature() -> tuple[Any, ...]:
    def mtime(path: Path) -> float | None:
        try:
            return path.stat().st_mtime_ns
        except OSError:
            return None
    return (mtime(TASKS_FILE), mtime(APPROVAL_LOG), mtime(CYCLE_LOG), mtime(SPEND_LOG), tuple(sorted(tmux_health().items())))


def write_sse(handler: BaseHTTPRequestHandler, event: str, payload: Any) -> None:
    body = f'event: {event}\ndata: {json.dumps(payload, separators=(",", ":"))}\n\n'.encode()
    handler.wfile.write(body)
    handler.wfile.flush()


def approval_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def apply_approval(task_id: str, decision: str, comment: str, user: str) -> dict[str, Any]:
    if decision not in {'approve', 'reject'}:
        raise ValueError('decision must be approve or reject')
    if decision == 'reject' and not comment.strip():
        raise ValueError('reject requires a comment')
    with board_lock():
        text = TASKS_FILE.read_text(encoding='utf-8')
        task = next((item for item in parse_tasks(text) if item['id'] == task_id), None)
        if not task:
            raise LookupError('task not found')
        try:
            discord_approvals = json.loads(HUMAN_APPROVALS.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            discord_approvals = {}
        existing = discord_approvals.get(task_id)
        if existing is True or existing == 'approved' or (isinstance(existing, dict) and existing.get('approved')):
            raise RuntimeError('task already has a Discord approval; the first decision won')
        if task.get('status') != 'Human Approval':
            raise RuntimeError('task is no longer in Human Approval; an earlier decision already won')
        if not (3 <= len(task.get('decision_summary', [])) <= 5):
            timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
            text = _move_task(text, task_id, 'In Progress', {
                'Status': 'In Progress',
                'Latest summary': 'Returned to agent: Human Approval requires a DECISION SUMMARY with 3–5 concrete bullets.',
                'Last updated': timestamp,
            })
            TASKS_FILE.write_text(text, encoding='utf-8')
            return {'ok': False, 'task_id': task_id, 'returned_to_agent': True, 'reason': 'decision summary must contain 3–5 bullets'}
        owner = task.get('owner', '').lower()
        if not owner or owner == 'unassigned':
            raise ValueError('task has no dispatchable owner')
        website_change = bool(affected_pages(task))
        commit = ''
        preview_url = ''
        if website_change and decision == 'approve':
            baseline_path = METRICS_DIR / f"{task_id}.baseline.json"
            if not baseline_path.exists():
                raise RuntimeError('baseline metrics must be captured before Gate 1 approval')
            baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
            if baseline.get('status') != 'captured':
                raise RuntimeError('baseline metrics must be captured before Gate 1 approval')
            commit = str(task.get('change_commit', '')).strip()
            if not re.fullmatch(r'[0-9a-fA-F]{7,40}', commit):
                raise RuntimeError('website approval requires the implementation commit on cmo-changes')
            preview = deploy_preview(task_id, commit)
            preview_url = preview['preview_url']
            post_discord(task_id, evidence_message(task, commit, preview_url))
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        updates = {
            'Status': 'In Progress',
            'Human decision': decision,
            'Human decision by': user,
            'Human decision at': timestamp,
            'Human decision comment': comment.strip() or 'Approved without comment.',
            'Latest summary': f'Human {decision} via dashboard by {user}: {comment.strip() or "No additional comment."}',
            'Last updated': timestamp,
        }
        if website_change and decision == 'approve':
            updates.update({
                'Preview URL': preview_url,
                'Live URL': live_url(),
                'Change status': 'Gate 1 approved; preview deployed; awaiting human GitHub merge (Gate 2).',
                'Metrics evidence': str(METRICS_DIR / f'{task_id}.baseline.json'),
            })
        text = _move_task(text, task_id, 'In Progress', updates)
        TASKS_FILE.write_text(text, encoding='utf-8')
        record_approval(user, task_id, decision, comment.strip())
        if website_change and decision == 'approve':
            _record_website_approval(task_id, owner, commit, preview_url)
        else:
            _queue_approved_work(task_id, owner, decision, comment.strip())
    return {'ok': True, 'task_id': task_id, 'decision': decision, 'owner': owner}


INDEX_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>iTarang CMO Control Room</title>
<style>
:root{--bg:#0a0d12;--panel:#111722;--panel2:#161e2b;--line:#253043;--text:#edf2f7;--muted:#8e9bad;--green:#35d07f;--amber:#f5b942;--red:#f06d6d;--violet:#9580ff;--cyan:#63d5e8}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 12% 0,#18243b 0,transparent 35%),var(--bg);color:var(--text);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}main{max-width:1500px;margin:auto;padding:28px 28px 48px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:24px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;color:var(--cyan);font-size:11px;font-weight:700}.title{font-size:30px;letter-spacing:-.04em;margin:6px 0}.sub{color:var(--muted);margin:0}.healthbar{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.health{border:1px solid var(--line);background:#0e141e;border-radius:999px;padding:7px 10px;color:var(--muted);font-size:12px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:var(--red)}.dot.alive{background:var(--green);box-shadow:0 0 10px #35d07f99}.meta{color:var(--muted);font-size:12px;margin:12px 0 18px}.cycle-stamp{border:1px solid #31516b;background:#102333;color:var(--cyan);border-radius:10px;padding:10px 12px;margin-bottom:16px}.pending{border:1px solid #6e5520;background:#231d10;border-radius:14px;padding:16px;margin-bottom:18px}.pending h2{margin:0 0 10px;font-size:17px;color:var(--amber)}.pending-card{border-top:1px solid #4a3b20;padding:12px 0}.change-details details{margin-top:10px}.decision-summary{border:1px solid #806020;background:#1b170e;border-radius:10px;padding:10px;margin:10px 0}.decision-summary h4{margin:0 0 6px;color:var(--amber);font-size:12px;letter-spacing:.08em}.decision-summary ul{margin:0;padding-left:20px}.approval-invalid{border-color:var(--red);color:var(--red)}.risk{color:var(--amber);margin-top:8px}.expand{cursor:pointer;color:var(--cyan);margin-top:8px}.tab{color:var(--muted);background:transparent;border:0;border-bottom:2px solid transparent;padding:12px 14px;cursor:pointer;font-weight:700;white-space:nowrap}.tab.active{color:var(--text);border-bottom-color:var(--violet)}.view{display:none}.view.active{display:block}.agent-head{display:flex;justify-content:space-between;align-items:center;margin:22px 0 14px}.agent-head h2{margin:0;font-size:20px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.card,.column{background:linear-gradient(145deg,#121a27,#0e141e);border:1px solid var(--line);border-radius:14px;padding:16px;min-height:130px}.card h3{font-size:15px;margin:0 0 10px}.pill{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:3px 8px;color:var(--muted);font-size:11px;margin:0 5px 8px 0}.summary{color:#c9d2df;margin:8px 0 0}.small{color:var(--muted);font-size:12px}.change-details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px;color:#c9d2df;font-size:12px}.change-details strong{color:var(--cyan)}.change-details div{margin:4px 0}.change-details ul{margin:4px 0 4px 18px;padding:0}.approval-actions{display:flex;gap:8px;margin-top:14px}.approval-actions button{border:0;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer}.approve{background:var(--green);color:#06140c}.reject{background:var(--red);color:#200606}.board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.stack{display:flex;flex-direction:column;gap:12px}.column h3{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}@media(max-width:1000px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){main{padding:18px}.top{display:block}.healthbar{justify-content:flex-start;margin-top:16px}.board{grid-template-columns:1fr}}
.live,.reconnecting{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;text-transform:uppercase;font-size:11px;letter-spacing:.08em;color:var(--green)}.reconnecting{color:var(--amber)}
</style></head>
<body><main>
<section class="top"><div><div class="eyebrow">iTarang / Marketing Operations</div><h1 class="title">CMO Control Room</h1><p class="sub">Read-only task visibility with Human Approval actions only.</p><div id="last-event" class="small"></div></div><div><div id="live-state" class="live">connecting</div><div id="health" class="healthbar"></div></div></section>
<div class="meta" id="meta"></div>
<div class="cycle-stamp" id="cycle-stamp"></div>
<section class="pending" id="pending"></section>
<nav class="tabs" id="tabs"></nav>
<section id="board" class="view active"><div class="board" id="board-grid"></div></section>
<section id="agent-views"></section>
</main>
<script>
let snapshot=null;let active='board';let fallbackTimer=null;let lastEvent=null;const rendered={};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const empty=message=>`<div class="empty">${esc(message)}</div>`;
function preserveOpen(){return [...document.querySelectorAll('details[open][data-task]')].map(x=>x.dataset.task)}
function patch(id,html){if(rendered[id]===html)return;const open=preserveOpen();const node=document.getElementById(id);if(node)node.innerHTML=html;rendered[id]=html;open.forEach(key=>document.querySelectorAll(`details[data-task="${CSS.escape(key)}"]`).forEach(x=>x.open=true))}
function approvalBlock(t){if(t.board_column!=='Under Review (Human)')return '';const summary=t.decision_summary||[];const valid=summary.length>=3&&summary.length<=5;const c=t.change||{};const evidence=c.evidence||'no branch evidence';return `<section class="decision-summary ${valid?'':'approval-invalid'}"><h4>DECISION SUMMARY ${valid?'':'· INVALID — RETURN TO AGENT'}</h4>${valid?`<ul>${summary.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:empty('Approval packet requires 3–5 concrete bullets.') }<div class="risk"><strong>RISK/COST:</strong> ${esc(c.risk_cost||'')}</div><details class="expand" data-task="${esc(t.id)}"><summary>Full change detail</summary><div><strong>Complete change list:</strong> ${esc(c.change_description||'')}</div><div><strong>File-level diff:</strong> ${esc(c.diff_summary||'')}</div><div><strong>Evidence:</strong> ${esc(evidence)}</div></details></section>`}
function changeBlock(t){const c=t.change||{};if(c.evidence==='no branch evidence')return `<div class="change-details">${esc(c.evidence)}</div>`;const lines=(c.summary_lines||[]).filter(Boolean);return `<div class="change-details"><div><strong>Branch:</strong> ${esc(c.branch)}</div><div><strong>Commit:</strong> ${esc(c.commits)}</div>${c.preview_url?`<div><strong>Visual preview:</strong> <a href="${esc(c.preview_url)}" target="_blank" rel="noreferrer">${esc(c.preview_url)}</a></div>`:''}${c.live_url?`<div><strong>Live site:</strong> <a href="${esc(c.live_url)}" target="_blank" rel="noreferrer">${esc(c.live_url)}</a></div>`:''}${c.files_changed?`<div><strong>Files changed:</strong> ${esc(c.files_changed)}</div>`:''}${c.change_description?`<div><strong>Change:</strong> ${esc(c.change_description)}</div>`:''}${c.metrics_evidence?`<details class="expand"><summary>Metrics evidence</summary><pre>${esc(c.metrics_evidence)}</pre></details>`:''}${c.metrics_table?`<details class="expand"><summary>Before / after table</summary><pre>${esc(c.metrics_table)}</pre></details>`:''}${lines.length?`<div><strong>Agent summary:</strong></div><ul>${lines.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}</div>`}
function approvalActions(t){if(t.status!=='Human Approval')return '';return `<div class="approval-actions"><button class="approve" data-approval="approve" data-task="${esc(t.id)}">Approve</button><button class="reject" data-approval="reject" data-task="${esc(t.id)}">Reject</button></div>`}
function card(t){const fields=Object.entries(t).filter(([key])=>!['id','title','status','priority','owner','last_updated','board_column','change','acceptance_criteria','decision_summary'].includes(key));return `<article class="card" data-card="${esc(t.id)}"><h3>${esc(t.title)} <span class="small">${esc(t.id)}</span></h3><span class="pill">${esc(t.status)}</span>${t.priority?`<span class="pill">${esc(t.priority)}</span>`:''}<div class="small">Owner: ${esc(t.owner)}</div><div class="small">Last updated: ${esc(t.last_updated)}</div>${approvalBlock(t)}<p class="summary">${esc(t.latest_summary||'')}</p>${changeBlock(t)}${fields.length?`<details class="expand" data-task="${esc(t.id)}"><summary>Task fields</summary>${fields.map(([key,value])=>`<div><strong>${esc(key)}:</strong> ${esc(Array.isArray(value)?value.join(', '):value)}</div>`).join('')}</details>`:''}${approvalActions(t)}</article>`}
function pendingCard(t){return `<article class="pending-card" data-card="${esc(t.id)}"><h3>${esc(t.title)} <span class="small">${esc(t.id)} · ${esc(t.owner)}</span></h3>${approvalBlock(t)}${changeBlock(t)}${approvalActions(t)}</article>`}
function setStatus(text,live){document.getElementById('meta').textContent=text;document.getElementById('live-state').textContent=live?'live':'reconnecting';document.getElementById('live-state').className=live?'live':'reconnecting'}
function render(next){const nextAgents=new Set(next.agents||[]);document.querySelectorAll('#agent-views .view').forEach(v=>{if(!nextAgents.has(v.id.slice(5)))v.remove()});(next.agents||[]).forEach(a=>{if(!document.getElementById(`view-${a}`)){const v=document.createElement('section');v.id=`view-${a}`;v.className='view';document.getElementById('agent-views').appendChild(v)}});snapshot=next;lastEvent=new Date();const agents=next.agents||[];const health=next.health||{};patch('health',agents.map(a=>`<span class="health"><i class="dot ${health[a]==='alive'?'alive':''}"></i>cmo-${esc(a)}: ${esc(health[a]||'dead')}</span>`).join(''));patch('tabs',[`<button class="tab ${active==='board'?'active':''}" data-view="board">Board</button>`,...agents.map(a=>`<button class="tab ${active===a?'active':''}" data-view="${esc(a)}">${esc(a)}</button>`)].join(''));patch('cycle-stamp',`Last orchestration cycle ran at: ${esc(next.last_cycle_ran||'')}`);const when=next.tasks_mtime?new Date(next.tasks_mtime*1000).toLocaleTimeString():'';document.getElementById('meta').textContent=`Source: ${esc(next.tasks_file||'tasks.md')} · File update: ${esc(when)} · Spend: ${next.spend_total==null?'':esc(next.spend_total)} · Approvals: ${esc(next.approval_count??'')}`;document.getElementById('last-event').textContent=`Last event: ${lastEvent.toLocaleTimeString()}`;patch('pending',`<h2>Pending Changes · Human Approval</h2>${(next.pending_changes||[]).map(pendingCard).join('')||empty('No pending changes.')}`);patch('board-grid',(next.board_columns||[]).map(column=>`<section class="column"><h3>${esc(column)}</h3><div class="stack">${next.tasks.filter(t=>t.board_column===column).map(card).join('')||empty('No tasks.')}</div></section>`).join(''));agents.forEach(agent=>{const tasks=next.tasks.filter(t=>(t.owner||'').toLowerCase()===agent);patch(`view-${agent}`,`<div class="agent-head"><h2>${esc(agent)}</h2><span class="health"><i class="dot ${health[agent]==='alive'?'alive':''}"></i>tmux ${esc(health[agent]||'dead')}</span></div><div class="cards">${tasks.map(card).join('')||empty('No assigned tasks.')}</div>`)});document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id==='board'||v.id===`view-${active}`));document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===active))}
function show(name){active=name;document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id==='board'||v.id===`view-${name}`));document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===name))}
async function decide(task,decision){let comment='';if(decision==='reject'){comment=window.prompt('Reject comment (required):','');if(!comment||!comment.trim())return}else comment=window.prompt('Approval comment (optional):','')||'';const r=await fetch('/api/approval',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task,decision,comment})});if(r.ok)poll()}
async function poll(){try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);render(await r.json())}catch(e){setStatus('Live source unavailable; retrying.',false)}}
function startFallback(){if(fallbackTimer===null)fallbackTimer=setInterval(poll,10000)}function stopFallback(){if(fallbackTimer!==null){clearInterval(fallbackTimer);fallbackTimer=null}}
document.getElementById('tabs').addEventListener('click',e=>{if(e.target.matches('.tab'))show(e.target.dataset.view)});document.addEventListener('click',e=>{const b=e.target.closest('[data-approval]');if(b)decide(b.dataset.task,b.dataset.approval)});
const stream=new EventSource('/api/events');stream.addEventListener('state',e=>{stopFallback();setStatus('Live source connected.',true);render(JSON.parse(e.data))});stream.addEventListener('heartbeat',()=>{document.getElementById('last-event').textContent=`Last event: ${new Date().toLocaleTimeString()}`});stream.onopen=()=>{stopFallback();setStatus('Live source connected.',true)};stream.onerror=()=>{setStatus('Reconnecting to live source.',false);startFallback()};poll();
</script></body></html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = 'CMODashboard/1.0'

    def _auth(self) -> bool:
        if valid_basic_auth(self.headers.get('Authorization')):
            return True
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header('WWW-Authenticate', 'Basic realm="CMO Dashboard"')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        return False

    def do_GET(self) -> None:  # noqa: N802
        if not self._auth():
            return
        path = self.path.split('?', 1)[0]
        if path == '/api/events':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            self.connection.settimeout(1)
            previous = None
            last_heartbeat = time.monotonic()
            try:
                while True:
                    current = event_signature()
                    if current != previous:
                        write_sse(self, 'state', build_snapshot())
                        previous = current
                    if time.monotonic() - last_heartbeat >= 30:
                        write_sse(self, 'heartbeat', {'timestamp': dt.datetime.now(dt.timezone.utc).isoformat()})
                        last_heartbeat = time.monotonic()
                    time.sleep(0.5)
            except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
                return
        if path == '/api/state':
            payload = json.dumps(build_snapshot(), separators=(',', ':')).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        elif path in ('/', '/index.html'):
            payload = INDEX_HTML.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth():
            return
        if self.path.split('?', 1)[0] != '/api/approval':
            approval_response(self, HTTPStatus.NOT_FOUND, {'error': 'not found'})
            return
        if os.getenv('CMO_DASHBOARD_PREVIEW', '').lower() in {'1', 'true', 'yes'}:
            approval_response(self, HTTPStatus.FORBIDDEN, {'error': 'preview mode'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            payload = json.loads(self.rfile.read(length) or b'{}')
            task_id = str(payload.get('task_id', '')).strip()
            decision = str(payload.get('decision', '')).strip().lower()
            comment = str(payload.get('comment', ''))
            if not task_id or not re.fullmatch(r'TASK-[0-9]+', task_id):
                raise ValueError('valid task_id is required')
            result = apply_approval(task_id, decision, comment, authenticated_user(self.headers.get('Authorization')))
        except (ValueError, json.JSONDecodeError) as exc:
            approval_response(self, HTTPStatus.BAD_REQUEST, {'error': str(exc)})
            return
        except LookupError as exc:
            approval_response(self, HTTPStatus.NOT_FOUND, {'error': str(exc)})
            return
        except RuntimeError as exc:
            approval_response(self, HTTPStatus.CONFLICT, {'error': str(exc)})
            return
        except (OSError, subprocess.SubprocessError) as exc:
            approval_response(self, HTTPStatus.BAD_GATEWAY, {'error': f'approval dispatch failed: {exc}'})
            return
        approval_response(self, HTTPStatus.OK, result)

    def do_PUT(self) -> None:  # noqa: N802
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, 'Only POST /api/approval is writable')

    do_PATCH = do_PUT
    do_DELETE = do_PUT

    def log_message(self, fmt: str, *args: object) -> None:
        print(f'[{self.log_date_time_string()}] {fmt % args}')


def main() -> None:
    if not os.getenv('CMO_DASHBOARD_USERNAME') or not os.getenv('CMO_DASHBOARD_PASSWORD'):
        raise SystemExit('Set CMO_DASHBOARD_USERNAME and CMO_DASHBOARD_PASSWORD before starting the dashboard.')
    if not TASKS_FILE.is_file():
        raise SystemExit(f'Missing board file: {TASKS_FILE}')
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f'CMO dashboard listening on http://{HOST}:{PORT} (Human Approval endpoint only)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
