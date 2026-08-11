#!/usr/bin/env python3
"""Read-only iTarang CMO monitoring dashboard."""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import fcntl
import html
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from preview_metrics import (METRICS_DIR, affected_pages, capture_metrics, deploy_preview,
                              evidence_message, live_url, post_discord)

PROFILE_DIR = Path(os.getenv('CMO_DASHBOARD_PROFILE_DIR', '/opt/data/profiles/itarang_cmo'))
# cmo_runtime is tracked source, not runtime state: prefer the copy beside this file
# (the repo checkout) and fall back to the profile tree for the legacy layout.
_RUNTIME_BASE = Path(__file__).resolve().parent
if not (_RUNTIME_BASE / 'cmo_runtime').is_dir():
    _RUNTIME_BASE = PROFILE_DIR
sys.path.insert(0, str(_RUNTIME_BASE))
from cmo_runtime.task_file import TaskFile, TaskFileError, validate_structure  # noqa: E402

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
SKILLS = ('seo', 'content', 'social', 'ads', 'ops')
GSC_COLLECTION_START = '2026-08-04'
GSC_CACHE_SECONDS = 900
_gsc_cache: dict[str, Any] = {'expires': 0.0, 'value': None}
_gsc_lock = threading.Lock()
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


def _attachment_path(task: dict[str, Any], profile_dir: Path | None = None) -> Path | None:
    """Resolve a parser-provided attachment without allowing filesystem traversal."""
    root = (profile_dir or PROFILE_DIR).resolve()
    value = str(task.get('attachment', '')).strip()
    if not value or value.lower() in {'none', 'n/a', 'not attached'} or value.startswith(('http://', 'https://')):
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def attachment_url(task: dict[str, Any], profile_dir: Path | None = None) -> str:
    value = str(task.get('attachment', '')).strip()
    if value.startswith(('http://', 'https://')):
        return value
    return f"/api/attachment?task={task['id']}" if _attachment_path(task, profile_dir) else ''


def _render_markdown(text: str, title: str) -> bytes:
    """Render the small artifact Markdown subset while escaping embedded HTML."""
    parts: list[str] = []
    in_list = False
    for raw in text.splitlines():
        line = html.escape(raw)
        heading = re.match(r'^(#{1,4})\s+(.+)$', line)
        bullet = re.match(r'^-\s+(.+)$', line)
        if heading:
            if in_list:
                parts.append('</ul>')
                in_list = False
            level = len(heading.group(1))
            parts.append(f'<h{level}>{heading.group(2)}</h{level}>')
        elif bullet:
            if not in_list:
                parts.append('<ul>')
                in_list = True
            parts.append(f'<li>{bullet.group(1)}</li>')
        elif line:
            if in_list:
                parts.append('</ul>')
                in_list = False
            parts.append(f'<p>{line}</p>')
    if in_list:
        parts.append('</ul>')
    document = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{html.escape(title)}</title><style>'
                'body{max-width:850px;margin:40px auto;padding:0 24px;color:#18202b;'
                'font:16px/1.6 system-ui,sans-serif}h1,h2,h3{line-height:1.25}li{margin:.35rem 0}'
                '</style></head><body>' + ''.join(parts) + '</body></html>')
    return document.encode('utf-8')


def load_task_attachment(task_id: str, tasks_file: Path | None = None,
                         profile_dir: Path | None = None) -> tuple[str, bytes]:
    """Load only the attachment named by the current parser-backed task card."""
    board = tasks_file or TASKS_FILE
    root = profile_dir or PROFILE_DIR
    task = next((item for item in parse_tasks(board.read_text(encoding='utf-8')) if item['id'] == task_id), None)
    if not task:
        raise FileNotFoundError('task not found')
    value = str(task.get('attachment', '')).strip()
    if value.startswith(('http://', 'https://')):
        raise ValueError('external attachment')
    path = _attachment_path(task, root)
    if path is None:
        candidate = Path(value)
        if candidate.is_absolute() and not str(candidate).startswith(str(Path(root).resolve())):
            raise PermissionError('attachment is outside the dashboard profile')
        raise FileNotFoundError('attachment is unavailable')
    if path.suffix.lower() in {'.md', '.markdown'}:
        text = path.read_text(encoding='utf-8', errors='replace')
        return 'text/html; charset=utf-8', _render_markdown(text, task.get('title', task_id))
    content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    if content_type.startswith('text/'):
        body = ('<!doctype html><html><head><meta charset="utf-8"><title>' +
                html.escape(task.get('title', task_id)) + '</title></head><body><pre>' +
                html.escape(path.read_text(encoding='utf-8', errors='replace')) + '</pre></body></html>')
        return 'text/html; charset=utf-8', body.encode('utf-8')
    return content_type, path.read_bytes()


def summarize_gsc(rows: list[dict[str, Any]], sitemaps: dict[str, Any],
                  page_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    indexed_values = []
    submitted_values = []
    for sitemap in sitemaps.get('sitemap', []):
        for content in sitemap.get('contents', []):
            if content.get('type') == 'WEB' and str(content.get('indexed', '')).isdigit():
                indexed_values.append(int(content['indexed']))
            if content.get('type') == 'WEB' and str(content.get('submitted', '')).isdigit():
                submitted_values.append(int(content['submitted']))
    row = rows[0] if rows else None
    has_search_data = bool(row)
    has_index_data = bool(indexed_values)
    pages = []
    for page in page_rows or []:
        keys = page.get('keys', [])
        pages.append({
            'page': keys[0] if isinstance(keys, list) and keys else None,
            'impressions': page.get('impressions'),
            'clicks': page.get('clicks'),
            'average_position': page.get('position'),
        })
    return {
        'status': 'ready' if has_search_data or has_index_data else 'collecting',
        'collection_start': GSC_COLLECTION_START,
        'impressions': row.get('impressions') if row else None,
        'clicks': row.get('clicks') if row else None,
        'average_position': row.get('position') if row else None,
        'indexed_pages': sum(indexed_values) if indexed_values else None,
        'submitted_pages': sum(submitted_values) if submitted_values else None,
        'indexation_coverage': (
            sum(indexed_values) / sum(submitted_values) * 100
            if indexed_values and submitted_values and sum(submitted_values) else None
        ),
        'pages': pages,
        'message': '' if has_search_data or has_index_data else 'No Search Console data yet — collecting since 4 August 2026.',
    }


def _fetch_gsc() -> dict[str, Any]:
    credentials_path = os.getenv('GSC_CREDENTIALS_PATH', '')
    property_name = os.getenv('GSC_PROPERTY', '')
    if not credentials_path or not property_name:
        return {**summarize_gsc([], {}), 'status': 'unavailable', 'message': 'Search Console configuration is unavailable.'}
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
        service = build('searchconsole', 'v1', credentials=credentials, cache_discovery=False)
        result = service.searchanalytics().query(
            siteUrl=property_name,
            body={'startDate': GSC_COLLECTION_START, 'endDate': dt.date.today().isoformat(), 'rowLimit': 1},
        ).execute()
        page_result = service.searchanalytics().query(
            siteUrl=property_name,
            body={'startDate': GSC_COLLECTION_START, 'endDate': dt.date.today().isoformat(),
                  'dimensions': ['page'], 'rowLimit': 250},
        ).execute()
        sitemaps = service.sitemaps().list(siteUrl=property_name).execute()
        return summarize_gsc(result.get('rows', []), sitemaps, page_result.get('rows', []))
    except (ImportError, OSError) as exc:
        return {**summarize_gsc([], {}), 'status': 'unavailable',
                'message': f'Search Console collector unavailable: {type(exc).__name__}.'}
    except Exception as exc:  # provider errors must not blank the rest of the board
        return {**summarize_gsc([], {}), 'status': 'error',
                'message': f'Search Console read failed: {type(exc).__name__}.'}


def gsc_summary() -> dict[str, Any]:
    now = time.monotonic()
    with _gsc_lock:
        if _gsc_cache['value'] is None or now >= _gsc_cache['expires']:
            _gsc_cache['value'] = _fetch_gsc()
            _gsc_cache['expires'] = now + GSC_CACHE_SECONDS
        return dict(_gsc_cache['value'])


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
        'approval_thread': approval_thread(task),
        'approval_valid': task.get('board_column') != 'Under Review (Human)' or 3 <= len(task.get('decision_summary', [])) <= 5,
        'metrics': task_metrics(task),
    }


def _read_metric_phase(task_id: str, phase: str) -> dict[str, Any] | None:
    path = METRICS_DIR / f'{task_id}.{phase}.json'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) and value.get('status') == 'captured' else None


def _metric_value(page: dict[str, Any], key: str) -> Any:
    return (page.get('metrics') or {}).get(key)


def _format_metric_value(key: str, value: Any) -> str:
    if value is None:
        return 'awaiting measurement'
    if key.endswith('_bytes'):
        return f'{value:,} bytes'
    if key.endswith('_ms'):
        return f'{value:,.0f} ms' if isinstance(value, (int, float)) else str(value)
    if key == 'cumulative_layout_shift' and isinstance(value, (int, float)):
        return f'{value:.3f}'
    if isinstance(value, float):
        return f'{value:.2f}'
    return str(value)


def _metric_label(key: str) -> str:
    return key.replace('_', ' ').strip().title()


def task_metrics(task: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get('id', ''))
    baseline = _read_metric_phase(task_id, 'baseline')
    preview = _read_metric_phase(task_id, 'preview')
    live = _read_metric_phase(task_id, 'live')
    phases = [item for item in (baseline, preview, live) if item]
    urls = []
    for phase in phases:
        urls.extend(page.get('url', '') for page in phase.get('pages', []))
    urls = list(dict.fromkeys(urls))
    keys: list[str] = []
    for phase in phases:
        for page in phase.get('pages', []):
            for key in (page.get('metrics') or {}):
                if key not in keys:
                    keys.append(key)
    rows = []
    for url in urls:
        row_pages = {phase: next((p for p in (phase_data or {}).get('pages', []) if p.get('url') == url), {})
                     for phase, phase_data in (('baseline', baseline), ('preview', preview), ('live', live))}
        for key in keys:
            before = _metric_value(row_pages['baseline'], key)
            preview_value = _metric_value(row_pages['preview'], key)
            after = _metric_value(row_pages['live'], key)
            comparison = preview_value if preview_value is not None and after is None else after
            change = comparison - before if isinstance(before, (int, float)) and isinstance(comparison, (int, float)) else None
            rows.append({'metric': f'{_metric_label(key)} · {url.split("itarang.com", 1)[-1] or "/"}',
                         'key': key, 'before': _format_metric_value(key, before),
                         'preview': _format_metric_value(key, preview_value),
                         'after': _format_metric_value(key, after), 'change': change,
                         'change_display': _format_metric_value(key, change),
                         'percent_change': (float(change) / before * 100) if isinstance(change, (int, float)) and isinstance(before, (int, float)) and isinstance(after, (int, float)) and before != 0 else None})
    raw_runs = sum(int((phase or {}).get('raw_runs', 0)) for phase in (baseline, preview, live))
    return {'declared_metric': task.get('declared_metric', ''), 'measurement_method': task.get('measurement_method', ''),
            'rows': rows, 'raw_runs': raw_runs, 'has_data': bool(rows), 'merged': bool(live)}


def impact_metrics(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    changes = []
    for task in tasks:
        data = task.get('change', {}).get('metrics', {})
        if not data.get('merged'):
            continue
        baseline = _read_metric_phase(task['id'], 'baseline')
        live = _read_metric_phase(task['id'], 'live')
        if not baseline or not live:
            continue
        changes.append({'task_id': task['id'], 'title': task.get('title', task['id']), 'merge_date': live.get('captured_at', ''),
                        'declared_metric': data.get('declared_metric', ''), 'rows': data.get('rows', [])})
    weight_deltas, load_deltas, score_deltas = [], [], []
    for change in changes:
        for row in change['rows']:
            if row['key'] == 'page_weight_bytes' and isinstance(row.get('change'), (int, float)):
                weight_deltas.append(row['change'])
            elif row['key'] == 'load_time_ms' and isinstance(row.get('change'), (int, float)):
                load_deltas.append(row['change'])
            elif row['key'] == 'performance_score' and isinstance(row.get('change'), (int, float)):
                score_deltas.append(row['change'])
    return {'changes_shipped': len(changes), 'total_page_weight_saved': -sum(weight_deltas),
            'avg_load_time_delta': sum(load_deltas) / len(load_deltas) if load_deltas else None,
            'score_improvement': sum(score_deltas), 'changes': sorted(changes, key=lambda x: x['merge_date'], reverse=True)}


def approval_thread(task: dict[str, Any]) -> list[dict[str, str]]:
    """Read rejection/reply events stored as fields on the task card."""
    events: list[dict[str, str]] = []
    for key, value in task.items():
        match = re.fullmatch(r'approval_thread_(\d+)_(rejection|reply)', str(key))
        if match and str(value).strip():
            events.append({'round': match.group(1), 'type': match.group(2), 'text': str(value).strip()})
    return sorted(events, key=lambda item: (int(item['round']), 0 if item['type'] == 'rejection' else 1))


def outstanding_rejection(task: dict[str, Any]) -> dict[str, str] | None:
    events = approval_thread(task)
    replied_rounds = {event['round'] for event in events if event['type'] == 'reply'}
    for event in reversed([event for event in events if event['type'] == 'rejection']):
        if event['round'] not in replied_rounds:
            return event
    return None


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
        task['skill'] = str(task.get('skill') or task.get('owner') or 'unassigned').strip().lower()
        task['attachment_url'] = attachment_url(task)
        task['change'] = task_change_metadata(task)
    cycle_match = re.search(r'(?m)^Last cycle ran:\s*(.*?)\s*$', text)
    if not cycle_match and CYCLE_LOG.exists():
        cycle_lines = CYCLE_LOG.read_text(encoding='utf-8', errors='replace').splitlines()
        timestamps = re.findall(r'(?m)^(20\d{2}-\d{2}-\d{2}T[^ ]+)', '\n'.join(cycle_lines))
        cycle_match_value = timestamps[-1] if timestamps else None
    else:
        cycle_match_value = cycle_match.group(1) if cycle_match else None
    pending_changes = [task for task in tasks if task.get('status') == 'Human Approval']
    columns = []
    counts: dict[str, int] = {}
    for task in tasks:
        if task['board_column'] not in columns:
            columns.append(task['board_column'])
        counts[task['board_column']] = counts.get(task['board_column'], 0) + 1
    agent_names = ({str(task.get('owner', '')).strip().lower() for task in tasks if task.get('owner') and task.get('owner') != 'unassigned'}
                   | set(health) | configured_agents())
    health_names = agent_names | {'watchdog'}
    active_tasks = [task for task in tasks if task.get('status') == 'In Progress']
    drafts = []
    artifacts_root = (PROFILE_DIR / 'artifacts').resolve()
    for task in tasks:
        path = _attachment_path(task)
        if path and path.is_relative_to(artifacts_root):
            drafts.append(task)
    skill_lanes = {}
    priority_rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    for skill in SKILLS:
        skill_tasks = [task for task in tasks if task.get('skill') == skill]
        queue = [task for task in skill_tasks if task.get('board_column') != 'Completed']
        queue.sort(key=lambda task: priority_rank.get(str(task.get('priority', '')).lower(), 4))
        skill_lanes[skill] = {
            'queue': queue,
            'completed': [task for task in skill_tasks if task.get('board_column') == 'Completed'],
        }
    return {
        'tasks': tasks,
        'current_work': active_tasks[0] if active_tasks else None,
        'active_task_count': len(active_tasks),
        'drafts': drafts,
        'skill_lanes': skill_lanes,
        'pending_changes': pending_changes,
        'last_cycle_ran': cycle_match_value,
        'health': {agent: health.get(agent, 'dead') for agent in sorted(health_names)},
        'agents': sorted(agent_names),
        'board_columns': columns,
        'board_counts': counts,
        'spend_total': spend_total(SPEND_LOG),
        'approval_count': approval_count(APPROVAL_LOG),
        'impact_metrics': impact_metrics(tasks),
        'website_analytics': gsc_summary(),
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


def _commit_board(original: str, candidate: str, operation: str) -> None:
    task_file = TaskFile(TASKS_FILE, lock_path=BOARD_LOCK)
    original_order_issues = {
        issue.message for issue in task_file._validate_candidate(original)
        if 'out of lifecycle order' in issue.message
    }
    issues = [
        issue for issue in task_file._validate_candidate(candidate)
        if not ('out of lifecycle order' in issue.message and issue.message in original_order_issues)
    ]
    if issues:
        detail = '; '.join(issue.message for issue in issues)
        raise TaskFileError(f'{operation} would make tasks.md invalid: {detail}')
    task_file._atomic_write(candidate)
    written = TASKS_FILE.read_text(encoding='utf-8')
    post_issues = [
        issue for issue in task_file._validate_candidate(written)
        if not ('out of lifecycle order' in issue.message and issue.message in original_order_issues)
    ]
    if written != candidate or post_issues:
        task_file._atomic_write(original)
        raise TaskFileError(f'{operation} verification failed; original tasks.md restored')


def _post_discord(message: str) -> None:
    """Compatibility seam for evidence posting; derive the task id from its first line."""
    task_id = message.partition(':')[0].strip()
    post_discord(task_id, message)


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
    if 'Last updated' in updates and 'Updated' not in updates:
        updates = {**updates, 'Updated': updates['Last updated']}
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
        'Reply to the outstanding rejection comment in the same format, explicitly stating what changed in response. '
        'A resubmission without that reply is invalid and will be bounced back automatically. '
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
    gsc_refresh_bucket = int(time.time() // GSC_CACHE_SECONDS)
    return (mtime(TASKS_FILE), mtime(APPROVAL_LOG), mtime(CYCLE_LOG), mtime(SPEND_LOG),
            tuple(sorted(tmux_health().items())), gsc_refresh_bucket)


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
        original = TASKS_FILE.read_text(encoding='utf-8')
        text = original
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
            _commit_board(original, text, 'approval packet return')
            return {'ok': False, 'task_id': task_id, 'returned_to_agent': True, 'reason': 'decision summary must contain 3–5 bullets'}
        owner = task.get('owner', '').lower()
        if not owner or owner == 'unassigned':
            raise ValueError('task has no dispatchable owner')
        website_change = str(task.get('change_type', '')).casefold() == 'website' or bool(affected_pages(task))
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
            _post_discord(evidence_message(task, commit, preview_url))
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
                'Change status': 'Preview ready; awaiting human merge to main.',
                'Gate status': 'awaiting Gate 2',
                'Metrics evidence': str(METRICS_DIR / f'{task_id}.baseline.json'),
            })
        if decision == 'reject':
            rounds = [int(event['round']) for event in approval_thread(task)]
            round_number = max(rounds or [0]) + 1
            updates[f'Approval thread {round_number} rejection'] = f'{user}: {comment.strip()}'
        text = _move_task(text, task_id, 'In Progress', updates)
        _commit_board(original, text, 'dashboard approval')
        record_approval(user, task_id, decision, comment.strip())
        if website_change and decision == 'approve':
            _record_website_approval(task_id, owner, commit, preview_url)
        else:
            _queue_approved_work(task_id, owner, decision, comment.strip())
    result = {'ok': True, 'task_id': task_id, 'decision': decision, 'owner': owner}
    if preview_url:
        result['preview_url'] = preview_url
    return result


INDEX_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>iTarang CMO Control Room</title>
<style>
:root{--bg:#0a0d12;--panel:#111722;--panel2:#161e2b;--line:#253043;--text:#edf2f7;--muted:#8e9bad;--green:#35d07f;--amber:#f5b942;--red:#f06d6d;--violet:#9580ff;--cyan:#63d5e8}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 12% 0,#18243b 0,transparent 35%),var(--bg);color:var(--text);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}main{max-width:1500px;margin:auto;padding:28px 28px 48px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:24px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;color:var(--cyan);font-size:11px;font-weight:700}.title{font-size:30px;letter-spacing:-.04em;margin:6px 0}.sub{color:var(--muted);margin:0}.healthbar{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.health{border:1px solid var(--line);background:#0e141e;border-radius:999px;padding:7px 10px;color:var(--muted);font-size:12px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;background:var(--red)}.dot.alive{background:var(--green);box-shadow:0 0 10px #35d07f99}.meta{color:var(--muted);font-size:12px;margin:12px 0 18px}.cycle-stamp{border:1px solid #31516b;background:#102333;color:var(--cyan);border-radius:10px;padding:10px 12px;margin-bottom:16px}.pending{border:1px solid #6e5520;background:#231d10;border-radius:14px;padding:16px;margin-bottom:18px}.pending h2{margin:0 0 10px;font-size:17px;color:var(--amber)}.pending-card{border-top:1px solid #4a3b20;padding:12px 0}.change-details details{margin-top:10px}.decision-summary{border:1px solid #806020;background:#1b170e;border-radius:10px;padding:10px;margin:10px 0}.decision-summary h4{margin:0 0 6px;color:var(--amber);font-size:12px;letter-spacing:.08em}.decision-summary ul{margin:0;padding-left:20px}.approval-invalid{border-color:var(--red);color:var(--red)}.risk{color:var(--amber);margin-top:8px}.expand{cursor:pointer;color:var(--cyan);margin-top:8px}.tab{color:var(--muted);background:transparent;border:0;border-bottom:2px solid transparent;padding:12px 14px;cursor:pointer;font-weight:700;white-space:nowrap}.tab.active{color:var(--text);border-bottom-color:var(--violet)}.view{display:none}.view.active{display:block}.agent-head{display:flex;justify-content:space-between;align-items:center;margin:22px 0 14px}.agent-head h2{margin:0;font-size:20px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}.card,.column{background:linear-gradient(145deg,#121a27,#0e141e);border:1px solid var(--line);border-radius:14px;padding:16px;min-height:130px}.card h3{font-size:15px;margin:0 0 10px}.pill{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:3px 8px;color:var(--muted);font-size:11px;margin:0 5px 8px 0}.summary{color:#c9d2df;margin:8px 0 0}.small{color:var(--muted);font-size:12px}.change-details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px;color:#c9d2df;font-size:12px}.change-details strong{color:var(--cyan)}.change-details div{margin:4px 0}.change-details ul{margin:4px 0 4px 18px;padding:0}.approval-actions{display:flex;gap:8px;margin-top:14px}.approval-actions button{border:0;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer}.approve{background:var(--green);color:#06140c}.reject{background:var(--red);color:#200606}.board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.stack{display:flex;flex-direction:column;gap:12px}.column h3{margin:0 0 12px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}.column-count{border:1px solid var(--line);border-radius:999px;padding:2px 8px;margin-left:6px;color:var(--cyan);font-size:11px;letter-spacing:.04em;white-space:nowrap}@media(max-width:1000px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){main{padding:18px}.top{display:block}.healthbar{justify-content:flex-start;margin-top:16px}.board{grid-template-columns:1fr}}
.live,.reconnecting{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;text-transform:uppercase;font-size:11px;letter-spacing:.08em;color:var(--green)}.reconnecting{color:var(--amber)}
.overview-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}.overview-panel{border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:16px}.overview-panel h2{font-size:17px;margin:0 0 10px}.draft-link,.attachment-link{color:var(--cyan)}.single-agent{border:1px solid #31516b;background:#102333;color:var(--cyan);border-radius:10px;padding:10px 12px;margin-bottom:16px}.skill-heading{display:flex;justify-content:space-between;align-items:center}.skill-group{margin:14px 0 24px}.skill-group h3{color:var(--cyan)}.card{cursor:pointer}.card a,.card button,.card summary{cursor:pointer}dialog{width:min(760px,calc(100% - 32px));border:1px solid var(--line);border-radius:14px;background:var(--panel);color:var(--text);padding:0}dialog::backdrop{background:#000b}.detail-head{display:flex;justify-content:space-between;gap:16px;padding:18px;border-bottom:1px solid var(--line)}.detail-body{padding:18px}.detail-body dt{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-top:14px}.detail-body dd{margin:5px 0}.close-detail{background:transparent;border:1px solid var(--line);color:var(--text);border-radius:8px;padding:7px 10px}.analytics-note{color:var(--amber);margin:10px 0}.analytics-cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:16px 0}@media(max-width:800px){.overview-grid{grid-template-columns:1fr}.analytics-cards{grid-template-columns:repeat(2,minmax(0,1fr))}}
.metrics-section{border-top:1px solid var(--line);margin-top:14px;padding-top:12px}.metrics-section h4{margin:0 0 7px;color:var(--cyan);font-size:12px;letter-spacing:.08em}.metrics-meta{color:var(--muted);font-size:12px;margin:7px 0}.metrics-table-wrap{overflow-x:auto}.metrics-table{width:100%;border-collapse:collapse;font-size:12px;min-width:620px}.metrics-table th,.metrics-table td{border-bottom:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}.metrics-table th{color:var(--muted);font-weight:600}.metric-rollups{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:16px 0}.metric-rollup{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px}.metric-rollup strong{display:block;font-size:20px}.metric-rollup span{color:var(--muted);font-size:12px}.metric-list{overflow-x:auto}.metric-list table{width:100%;border-collapse:collapse;min-width:780px}.metric-list th,.metric-list td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}.metric-list th{color:var(--muted);cursor:pointer}.metric-list a{color:var(--cyan)}@media(max-width:700px){main{padding:18px 12px 36px}.metric-rollups{grid-template-columns:repeat(2,minmax(0,1fr))}.metrics-table{min-width:0}.metrics-table thead{display:none}.metrics-table,.metrics-table tbody,.metrics-table tr,.metrics-table td{display:block;width:100%}.metrics-table tr{border:1px solid var(--line);border-radius:8px;margin-bottom:8px;padding:5px}.metrics-table td{border:0;padding:4px 6px}.metrics-table td:before{content:attr(data-label);display:inline-block;color:var(--muted);font-weight:600;width:78px}.metric-list{margin:0 -4px;padding:0 4px}}
</style></head>
<body><main>
<section class="top"><div><div class="eyebrow">iTarang / Marketing Operations</div><h1 class="title">CMO Control Room</h1><p class="sub">Read-only task visibility with Human Approval actions only.</p><div id="last-event" class="small"></div></div><div><div id="live-state" class="live">connecting</div><div id="health" class="healthbar"></div></div></section>
<div class="meta" id="meta"></div>
<div class="cycle-stamp" id="cycle-stamp"></div>
<div class="single-agent" id="single-agent"></div>
<div class="overview-grid"><section class="overview-panel" id="current-work"></section><section class="overview-panel" id="drafts"></section></div>
<section class="pending" id="pending"></section>
<nav class="tabs" id="tabs"></nav>
<section id="board" class="view active"><div class="board" id="board-grid"></div></section>
<section id="analytics" class="view"><h2>Website analytics</h2><p class="sub">Read-only Google Search Console reporting.</p><div id="analytics-content"></div></section>
<section id="metrics" class="view"><h2>Metrics</h2><p class="sub">Measured impact from merged changes only.</p><div id="metrics-content"></div></section>
<section id="skill-views"></section>
<dialog id="task-detail"><div class="detail-head"><strong>Task detail</strong><button class="close-detail" type="button">Close</button></div><div class="detail-body" id="detail-content"></div></dialog>
</main>
<script>
let snapshot=null;let active='board';let fallbackTimer=null;let lastEvent=null;const rendered={};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const empty=message=>`<div class="empty">${esc(message)}</div>`;
const countLabel=n=>`${n} ${n===1?'task':'tasks'}`;
function preserveOpen(){return [...document.querySelectorAll('details[open][data-task]')].map(x=>x.dataset.task)}
function patch(id,html){if(rendered[id]===html)return;const open=preserveOpen();const node=document.getElementById(id);if(node)node.innerHTML=html;rendered[id]=html;open.forEach(key=>document.querySelectorAll(`details[data-task="${CSS.escape(key)}"]`).forEach(x=>x.open=true))}
function metricsBlock(t){const m=(t.change||{}).metrics||{};if(!m.has_data&&!t.declared_metric)return '';const rows=m.rows||[];return `<section class="metrics-section"><h4>METRICS</h4><div><strong>Declared metric:</strong> ${esc(m.declared_metric||'no quantifiable metric declared')}</div><div><strong>Measurement method:</strong> ${esc(m.measurement_method||'awaiting measurement')}</div>${rows.length?`<div class="metrics-table-wrap"><table class="metrics-table"><thead><tr><th>Metric</th><th>Before</th><th>Preview</th><th>After</th><th>Change</th></tr></thead><tbody>${rows.map(r=>`<tr><td data-label="Metric">${esc(r.metric)}</td><td data-label="Before">${esc(r.before)}</td><td data-label="Preview">${esc(r.preview)}</td><td data-label="After">${esc(r.after)}</td><td data-label="Change">${esc(r.change_display||'awaiting measurement')}</td></tr>`).join('')}</tbody></table></div>`:empty('awaiting measurement')}<div class="metrics-meta">${esc(m.raw_runs||0)} raw runs stored</div></section>`}
function approvalBlock(t){if(t.board_column!=='Under Review (Human)')return '';const summary=t.decision_summary||[];const valid=summary.length>=3&&summary.length<=5;const c=t.change||{};const evidence=c.evidence||'no branch evidence';const thread=c.approval_thread||[];return `<section class="decision-summary ${valid?'':'approval-invalid'}"><h4>DECISION SUMMARY ${valid?'':'· INVALID — RETURN TO AGENT'}</h4>${valid?`<ul>${summary.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:empty('Approval packet requires 3–5 concrete bullets.') }${thread.length?`<div class="approval-thread"><strong>REJECTION THREAD</strong><ol>${thread.map(x=>`<li><b>Round ${esc(x.round)} ${esc(x.type)}:</b> ${esc(x.text)}</li>`).join('')}</ol></div>`:''}<div class="risk"><strong>RISK/COST:</strong> ${esc(c.risk_cost||'')}</div><details class="expand" data-task="${esc(t.id)}"><summary>Full change detail</summary><div><strong>Complete change list:</strong> ${esc(c.change_description||'')}</div><div><strong>File-level diff:</strong> ${esc(c.diff_summary||'')}</div><div><strong>Evidence:</strong> ${esc(evidence)}</div></details></section>`}
function changeBlock(t){const c=t.change||{};if(c.evidence==='no branch evidence')return `<div class="change-details">${esc(c.evidence)}</div>`;const lines=(c.summary_lines||[]).filter(Boolean);return `<div class="change-details"><div><strong>Branch:</strong> ${esc(c.branch)}</div><div><strong>Commit:</strong> ${esc(c.commits)}</div>${c.preview_url?`<div><strong>Visual preview:</strong> <a href="${esc(c.preview_url)}" target="_blank" rel="noreferrer">${esc(c.preview_url)}</a></div>`:''}${c.live_url?`<div><strong>Live site:</strong> <a href="${esc(c.live_url)}" target="_blank" rel="noreferrer">${esc(c.live_url)}</a></div>`:''}${c.files_changed?`<div><strong>Files changed:</strong> ${esc(c.files_changed)}</div>`:''}${c.change_description?`<div><strong>Change:</strong> ${esc(c.change_description)}</div>`:''}${c.metrics_evidence?`<details class="expand"><summary>Metrics evidence</summary><pre>${esc(c.metrics_evidence)}</pre></details>`:''}${c.metrics_table?`<details class="expand"><summary>Before / after table</summary><pre>${esc(c.metrics_table)}</pre></details>`:''}${lines.length?`<div><strong>Agent summary:</strong></div><ul>${lines.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}</div>`}
function approvalActions(t){if(t.status!=='Human Approval')return '';return `<div class="approval-actions"><button class="approve" data-approval="approve" data-task="${esc(t.id)}">Approve</button><button class="reject" data-approval="reject" data-task="${esc(t.id)}">Reject</button></div>`}
function card(t){const fields=Object.entries(t).filter(([key])=>!['id','title','status','priority','owner','last_updated','board_column','change','acceptance_criteria','decision_summary'].includes(key));return `<article id="${esc(t.id)}" class="card" data-card="${esc(t.id)}"><h3>${esc(t.title)} <span class="small">${esc(t.id)}</span></h3><span class="pill">${esc(t.status)}</span>${t.priority?`<span class="pill">${esc(t.priority)}</span>`:''}<div class="small">Owner: ${esc(t.owner)}</div><div class="small">Last updated: ${esc(t.last_updated)}</div>${approvalBlock(t)}${metricsBlock(t)}<p class="summary">${esc(t.latest_summary||'')}</p>${changeBlock(t)}${fields.length?`<details class="expand" data-task="${esc(t.id)}"><summary>Task fields</summary>${fields.map(([key,value])=>`<div><strong>${esc(key)}:</strong> ${esc(Array.isArray(value)?value.join(', '):value)}</div>`).join('')}</details>`:''}${approvalActions(t)}</article>`}
function pendingCard(t){return `<article class="pending-card" data-card="${esc(t.id)}"><h3>${esc(t.title)} <span class="small">${esc(t.id)} · ${esc(t.owner)}</span></h3>${approvalBlock(t)}${metricsBlock(t)}${changeBlock(t)}${approvalActions(t)}</article>`}
function setStatus(text,live){document.getElementById('meta').textContent=text;document.getElementById('live-state').textContent=live?'live':'reconnecting';document.getElementById('live-state').className=live?'live':'reconnecting'}
function metricsView(data){const fmt=(v,suffix='')=>v==null?'awaiting measurement':`${Number(v).toLocaleString()}${suffix}`;const roll=data||{};const cards=`<div class="metric-rollups"><div class="metric-rollup"><strong>${fmt(roll.changes_shipped)}</strong><span>Changes shipped</span></div><div class="metric-rollup"><strong>${fmt(roll.total_page_weight_saved,' bytes')}</strong><span>Total page-weight saved</span></div><div class="metric-rollup"><strong>${roll.avg_load_time_delta==null?'awaiting measurement':`${Number(roll.avg_load_time_delta).toFixed(0)} ms`}</strong><span>Average load-time delta</span></div><div class="metric-rollup"><strong>${fmt(roll.score_improvement)}</strong><span>Performance-score improvement</span></div></div>`;const changes=roll.changes||[];if(!changes.length)return cards+empty('No measured changes yet — metrics appear when changes merge.');return cards+`<div class="metric-list"><table><thead><tr><th data-sort="date">Merge date ↕</th><th>Task</th><th>Declared metric</th><th>Before → After</th><th data-sort="impact">Impact ↕</th></tr></thead><tbody>${changes.map(c=>{const row=(c.rows||[]).find(r=>r.key==='page_weight_bytes')||(c.rows||[])[0]||{};return `<tr><td>${esc(c.merge_date)}</td><td><a href="#${esc(c.task_id)}">${esc(c.task_id)} · ${esc(c.title)}</a></td><td>${esc(c.declared_metric||'no quantifiable metric declared')}</td><td>${esc(row.before||'awaiting measurement')} → ${esc(row.after||'awaiting measurement')}</td><td>${row.percent_change==null?'awaiting measurement':`${Number(row.percent_change).toFixed(1)}%`}</td></tr>`}).join('')}</tbody></table></div>`}
function render(next){const nextAgents=new Set(next.agents||[]);document.querySelectorAll('#agent-views .view').forEach(v=>{if(!nextAgents.has(v.id.slice(5)))v.remove()});(next.agents||[]).forEach(a=>{if(!document.getElementById(`view-${a}`)){const v=document.createElement('section');v.id=`view-${a}`;v.className='view';document.getElementById('agent-views').appendChild(v)}});snapshot=next;lastEvent=new Date();const agents=next.agents||[];const health=next.health||{};patch('health',agents.map(a=>`<span class="health"><i class="dot ${health[a]==='alive'?'alive':''}"></i>cmo-${esc(a)}: ${esc(health[a]||'dead')}</span>`).join(''));patch('tabs',[`<button class="tab ${active==='board'?'active':''}" data-view="board">Board</button>`,`<button class="tab ${active==='metrics'?'active':''}" data-view="metrics">Metrics</button>`,...agents.map(a=>`<button class="tab ${active===a?'active':''}" data-view="${esc(a)}">${esc(a)}</button>`)].join(''));patch('cycle-stamp',`Last orchestration cycle ran at: ${esc(next.last_cycle_ran||'')}`);const when=next.tasks_mtime?new Date(next.tasks_mtime*1000).toLocaleTimeString():'';document.getElementById('meta').textContent=`Source: ${esc(next.tasks_file||'tasks.md')} · File update: ${esc(when)} · Spend: ${next.spend_total==null?'':esc(next.spend_total)} · Approvals: ${esc(next.approval_count??'')}`;document.getElementById('last-event').textContent=`Last event: ${lastEvent.toLocaleTimeString()}`;patch('pending',`<h2>Pending Changes · Human Approval</h2>${(next.pending_changes||[]).map(pendingCard).join('')||empty('No pending changes.')}`);patch('board-grid',(next.board_columns||[]).map(column=>`<section class="column"><h3>${esc(column)}</h3><div class="stack">${next.tasks.filter(t=>t.board_column===column).map(card).join('')||empty('No tasks.')}</div></section>`).join(''));patch('metrics-content',metricsView(next.impact_metrics));agents.forEach(agent=>{const tasks=next.tasks.filter(t=>(t.owner||'').toLowerCase()===agent);patch(`view-${agent}`,`<div class="agent-head"><h2>${esc(agent)}</h2><span class="health"><i class="dot ${health[agent]==='alive'?'alive':''}"></i>tmux ${esc(health[agent]||'dead')}</span></div><div class="cards">${tasks.map(card).join('')||empty('No assigned tasks.')}</div>`)});document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===active||v.id===`view-${active}`));document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===active))}
function show(name){active=name;document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===name||v.id===`view-${name}`));document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===name))}
async function decide(task,decision){let comment='';if(decision==='reject'){comment=window.prompt('Reject comment (required):','');if(!comment||!comment.trim())return}else comment=window.prompt('Approval comment (optional):','')||'';const r=await fetch('/api/approval',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task_id:task,decision,comment})});if(r.ok)poll()}
async function poll(){try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);render(await r.json())}catch(e){setStatus('Live source unavailable; retrying.',false)}}
function startFallback(){if(fallbackTimer===null)fallbackTimer=setInterval(poll,10000)}function stopFallback(){if(fallbackTimer!==null){clearInterval(fallbackTimer);fallbackTimer=null}}
document.getElementById('tabs').addEventListener('click',e=>{if(e.target.matches('.tab'))show(e.target.dataset.view)});document.addEventListener('click',e=>{const b=e.target.closest('[data-approval]');if(b)decide(b.dataset.task,b.dataset.approval);const h=e.target.closest('[data-sort]');if(h){const table=h.closest('table');const rows=[...table.tBodies[0].rows];const col=h.cellIndex;const numeric=h.dataset.sort==='impact';rows.sort((a,b)=>{const av=numeric?parseFloat(a.cells[col].textContent):a.cells[col].textContent;const bv=numeric?parseFloat(b.cells[col].textContent):b.cells[col].textContent;if(numeric)return (Number.isFinite(bv)?bv:-Infinity)-(Number.isFinite(av)?av:-Infinity);return String(bv).localeCompare(String(av))});rows.forEach(r=>table.tBodies[0].appendChild(r))}});
card=function(t){const attachment=t.attachment_url?`<div><a class="attachment-link" href="${esc(t.attachment_url)}" target="_blank" rel="noreferrer">Open attachment</a></div>`:'';return `<article id="${esc(t.id)}" class="card" data-card="${esc(t.id)}" tabindex="0"><h3>${esc(t.title)} <span class="small">${esc(t.id)}</span></h3><span class="pill">${esc(t.status)}</span>${t.priority?`<span class="pill">${esc(t.priority)}</span>`:''}<div class="small">Skill: ${esc(t.skill)}</div><p class="summary">${esc(t.description||t.objective||t.latest_summary||'')}</p>${attachment}${approvalBlock(t)}${metricsBlock(t)}${approvalActions(t)}</article>`};
function analyticsView(data){const a=data||{};const value=v=>v==null?'collecting':Number(v).toLocaleString(undefined,{maximumFractionDigits:2});return `<div class="analytics-note">Collection started 4 August 2026. Empty results mean data is still collecting — not a decline or a flat line.</div><div class="analytics-cards"><div class="metric-rollup"><strong>${value(a.impressions)}</strong><span>Impressions</span></div><div class="metric-rollup"><strong>${value(a.clicks)}</strong><span>Clicks</span></div><div class="metric-rollup"><strong>${value(a.average_position)}</strong><span>Average position</span></div><div class="metric-rollup"><strong>${value(a.indexed_pages)}</strong><span>Indexed pages</span></div></div>${a.message?`<div class="empty">${esc(a.message)}</div>`:''}`}
function showDetail(taskId){const t=(snapshot?.tasks||[]).find(item=>item.id===taskId);if(!t)return;const link=t.attachment_url?`<a class="attachment-link" href="${esc(t.attachment_url)}" target="_blank" rel="noreferrer">Open and view in browser</a>`:'No browser-viewable attachment';const metric=t.metric||t.declared_metric||(t.change?.metrics?.declared_metric)||'No metric stated';patch('detail-content',`<h2>${esc(t.title)}</h2><div class="small">${esc(t.id)} · ${esc(t.skill)} · ${esc(t.status)}</div><dl><dt>Description</dt><dd>${esc(t.description||t.objective||t.latest_summary||'No description')}</dd><dt>Attachment</dt><dd>${link}</dd><dt>Metric — what this helps</dt><dd>${esc(metric)}</dd></dl>`);document.getElementById('task-detail').showModal()}
render=function(next){snapshot=next;lastEvent=new Date();const skills=Object.keys(next.skill_lanes||{});skills.forEach(skill=>{if(!document.getElementById(`view-${skill}`)){const view=document.createElement('section');view.id=`view-${skill}`;view.className='view';document.getElementById('skill-views').appendChild(view)}});document.querySelectorAll('#skill-views .view').forEach(view=>{if(!skills.includes(view.id.slice(5)))view.remove()});if(!['board','analytics','metrics',...skills].includes(active))active='board';patch('health','<span class="health"><i class="dot alive"></i>one CMO agent</span>');patch('tabs',[`<button class="tab ${active==='board'?'active':''}" data-view="board">Board</button>`,`<button class="tab ${active==='analytics'?'active':''}" data-view="analytics">Website analytics</button>`,`<button class="tab ${active==='metrics'?'active':''}" data-view="metrics">Impact</button>`,...skills.map(skill=>`<button class="tab ${active===skill?'active':''}" data-view="${esc(skill)}">${esc(skill)}</button>`)].join(''));patch('cycle-stamp',`Last orchestration cycle ran at: ${esc(next.last_cycle_ran||'not recorded')}`);patch('single-agent',`One agent across five skills · ${esc(next.active_task_count||0)} active task${next.active_task_count===1?'':'s'} globally${next.active_task_count>1?' · INVARIANT WARNING: more than one task is active':''}`);const current=next.current_work;patch('current-work',`<h2>Working on right now</h2>${current?card(current):empty('No task is currently in progress.')}`);patch('drafts',`<h2>Drafts produced</h2>${(next.drafts||[]).map(t=>`<div class="pending-card"><strong>${esc(t.title)}</strong><div class="small">${esc(t.id)} · ${esc(t.skill)}</div><a class="draft-link" href="${esc(t.attachment_url)}" target="_blank" rel="noreferrer">Open draft in browser</a></div>`).join('')||empty('No artifacts are currently attached from artifacts/.')}`);patch('pending',`<h2>Pending Human Approvals</h2>${(next.pending_changes||[]).map(pendingCard).join('')||empty('No pending approvals.')}`);const counts=next.board_counts||{};patch('board-grid',(next.board_columns||[]).map(column=>`<section class="column"><h3>${esc(column)} <span class="column-count">${esc(countLabel(counts[column]||0))}</span></h3><div class="stack">${next.tasks.filter(t=>t.board_column===column).map(card).join('')||empty('No tasks.')}</div></section>`).join(''));patch('analytics-content',analyticsView(next.website_analytics));patch('metrics-content',metricsView(next.impact_metrics));skills.forEach(skill=>{const lane=next.skill_lanes[skill]||{queue:[],completed:[]};patch(`view-${skill}`,`<div class="skill-heading"><h2>${esc(skill)} skill lane</h2><span class="small">One shared CMO agent · ${lane.queue.length} queued · ${lane.completed.length} completed</span></div><section class="skill-group"><h3>Queue · priority order</h3><div class="cards">${lane.queue.map(card).join('')||empty('No queued tasks.')}</div></section><section class="skill-group"><h3>Completed</h3><div class="cards">${lane.completed.map(card).join('')||empty('No completed tasks.')}</div></section>`)});const when=next.tasks_mtime?new Date(next.tasks_mtime*1000).toLocaleTimeString():'';document.getElementById('meta').textContent=`Source: tasks.md · ${next.tasks.length}-card live parser view · File update: ${when} · Spend: ${next.spend_total==null?'':next.spend_total} · Approvals: ${next.approval_count??''}`;document.getElementById('last-event').textContent=`Last event: ${lastEvent.toLocaleTimeString()}`;show(active)};
document.addEventListener('click',e=>{const close=e.target.closest('.close-detail');if(close){document.getElementById('task-detail').close();return}const article=e.target.closest('[data-card]');if(article&&!e.target.closest('a,button,summary,details'))showDetail(article.dataset.card)});document.addEventListener('keydown',e=>{const article=e.target.closest?.('[data-card]');if(article&&(e.key==='Enter'||e.key===' ')){e.preventDefault();showDetail(article.dataset.card)}});
const stream=new EventSource('/api/events');stream.addEventListener('state',e=>{stopFallback();setStatus('Live source connected.',true);render(JSON.parse(e.data))});stream.addEventListener('heartbeat',()=>{document.getElementById('last-event').textContent=`Last event: ${new Date().toLocaleTimeString()}`});stream.onopen=()=>{stopFallback();setStatus('Live source connected.',true)};stream.onerror=()=>{setStatus('Reconnecting to live source.',false);startFallback()};poll();
</script></body></html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = 'CMODashboard/1.0'

    def _console_dispatch(self, method: str) -> bool:
        import ceo_console
        import front_door
        import tech_console

        if front_door.handles(self.path):
            return front_door.dispatch(self, method)
        if ceo_console.handles(self.path):
            return ceo_console.dispatch(self, method)
        if tech_console.handles(self.path):
            return tech_console.dispatch(self, method)
        return False

    def _auth(self) -> bool:
        if valid_basic_auth(self.headers.get('Authorization')):
            return True
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header('WWW-Authenticate', 'Basic realm="CMO Dashboard"')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        return False

    def do_GET(self) -> None:  # noqa: N802
        if self._console_dispatch('GET'):
            return
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == '/index.html':
            self.send_response(HTTPStatus.FOUND)
            self.send_header('Location', '/team')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        if not self._auth():
            return
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
        if path == '/api/attachment':
            task_id = parse_qs(parsed_url.query).get('task', [''])[0]
            if not re.fullmatch(r'TASK-[0-9]+', task_id):
                self.send_error(HTTPStatus.BAD_REQUEST, 'valid task is required')
                return
            try:
                content_type, payload = load_task_attachment(task_id)
            except PermissionError:
                self.send_error(HTTPStatus.FORBIDDEN, 'attachment is outside the dashboard profile')
                return
            except (FileNotFoundError, ValueError):
                self.send_error(HTTPStatus.NOT_FOUND, 'attachment is unavailable')
                return
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:")
            self.send_header('Content-Disposition', 'inline')
        elif path == '/api/state':
            payload = json.dumps(build_snapshot(), separators=(',', ':')).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        elif path in ('/team', '/team/'):
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
        if self._console_dispatch('POST'):
            return
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
