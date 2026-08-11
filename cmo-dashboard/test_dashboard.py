import base64
import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import dashboard_server
from dashboard_server import apply_approval, build_snapshot, parse_tasks, valid_basic_auth


class DashboardDataTests(unittest.TestCase):
    def test_snapshot_derives_structure_and_reads_live_ledgers(self):
        text = '''# Board\n\n## Backlog\n\n### TASK-1 — Draft\n- ID: TASK-1\n- Owner: new-agent\n- Status: Backlog\n- Latest summary: waiting\n\n## New Column\n\n### TASK-2 — New\n- ID: TASK-2\n- Owner: content\n- Status: New Column\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'tasks.md'
            board.write_text(text, encoding='utf-8')
            cycle = root / 'hourly-cycle.log'
            cycle.write_text('2026-07-27T10:00:00+00:00 cycle changes=1 active=1\n', encoding='utf-8')
            spend = root / 'spend.log'
            spend.write_text(json.dumps({'estimated_cost_usd': 1.25}) + '\n', encoding='utf-8')
            approvals = root / 'approvals.log'
            approvals.write_text(json.dumps({'task_id': 'TASK-1', 'decision': 'approve'}) + '\n', encoding='utf-8')
            with patch.object(dashboard_server, 'CYCLE_LOG', cycle), \
                 patch.object(dashboard_server, 'SPEND_LOG', spend), \
                 patch.object(dashboard_server, 'APPROVAL_LOG', approvals), \
                 patch('dashboard_server.subprocess.run') as run:
                run.return_value.stdout = 'cmo-new-agent: 1 windows\ncmo-watchdog: 1 windows\n'
                run.return_value.returncode = 0
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertIn('content', snapshot['agents'])
        self.assertIn('new-agent', snapshot['agents'])
        self.assertEqual(snapshot['board_columns'], ['Task List', 'New Column'])
        self.assertEqual(snapshot['spend_total'], 1.25)
        self.assertEqual(snapshot['approval_count'], 1)
        self.assertEqual(snapshot['last_cycle_ran'], '2026-07-27T10:00:00+00:00')

    def test_board_counts_match_rendered_columns(self):
        text = '''# Board\n\n## Backlog\n\n### TASK-1 — Draft\n- ID: TASK-1\n- Owner: content\n- Status: Backlog\n\n## In Progress\n\n### TASK-2 — SEO\n- ID: TASK-2\n- Owner: seo\n- Status: In Progress\n\n## New Column\n\n### TASK-3 — New\n- ID: TASK-3\n- Owner: ops\n- Status: New Column\n'''
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp) / 'tasks.md'
            board.write_text(text, encoding='utf-8')
            with patch('dashboard_server.subprocess.run') as run:
                run.return_value.stdout = ''
                run.return_value.returncode = 0
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        counts = snapshot['board_counts']
        self.assertEqual(sorted(counts), sorted(snapshot['board_columns']))
        self.assertEqual(counts['Task List'], 2)
        self.assertEqual(counts['New Column'], 1)
        for column in snapshot['board_columns']:
            self.assertEqual(counts[column], len([t for t in snapshot['tasks'] if t['board_column'] == column]))

    def test_board_counts_are_empty_without_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp) / 'tasks.md'
            board.write_text('## Backlog\n_No tasks._\n', encoding='utf-8')
            with patch('dashboard_server.subprocess.run') as run:
                run.return_value.stdout = ''
                run.return_value.returncode = 0
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertEqual(snapshot['board_counts'], {})
        self.assertEqual(snapshot['board_columns'], [])

    def test_dashboard_ui_renders_singular_and_plural_counts(self):
        self.assertIn("`${n} ${n===1?'task':'tasks'}`", dashboard_server.INDEX_HTML)
        self.assertIn('countLabel(counts[column]||0)', dashboard_server.INDEX_HTML)

    def test_parse_tasks_maps_workflow_columns_and_agent_tasks(self):
        text = '''# Board\n\n## Backlog\n\n### TASK-1 — Draft\n- ID: TASK-1\n- Title: Draft\n- Owner: content\n- Priority: low\n- Status: Backlog\n- Start date: not started\n- Completed date: not completed\n- Objective: Make a draft.\n- Acceptance criteria:\n  - Be concise.\n- Latest summary: waiting\n\n## In Progress\n\n### TASK-2 — SEO\n- ID: TASK-2\n- Title: SEO\n- Owner: seo\n- Status: In Progress\n- Latest summary: researching\n\n## CMO Review\n\n### TASK-3 — Review\n- ID: TASK-3\n- Title: Review\n- Owner: content\n- Status: CMO Review\n- Latest summary: ready\n\n## Human Approval\n\n### TASK-4 — Approve\n- ID: TASK-4\n- Title: Approve\n- Owner: ads\n- Status: Human Approval\n- Latest summary: waiting\n\n## Completed\n\n### TASK-5 — Done\n- ID: TASK-5\n- Title: Done\n- Owner: ops\n- Status: Completed\n- Completed date: 2026-01-01\n- Latest summary: shipped\n'''
        tasks = parse_tasks(text)
        self.assertEqual([t['id'] for t in tasks], ['TASK-1', 'TASK-2', 'TASK-3', 'TASK-4', 'TASK-5'])
        self.assertEqual(tasks[0]['board_column'], 'Task List')
        self.assertEqual(tasks[1]['board_column'], 'Task List')
        self.assertEqual(tasks[2]['board_column'], 'Under Review (CMO)')
        self.assertEqual(tasks[3]['board_column'], 'Under Review (Human)')
        self.assertEqual(tasks[4]['board_column'], 'Completed')
        self.assertEqual([t['id'] for t in tasks if t['owner'] == 'content'], ['TASK-1', 'TASK-3'])

    def test_human_approval_parses_decision_summary_and_risk_detail(self):
        tasks = parse_tasks('''## Human Approval\n\n### TASK-9 — Image delivery\n- ID: TASK-9\n- Owner: seo\n- Status: Human Approval\n- Decision summary:\n  - Four oversized images compress from 2.1MB to 300KB.\n  - Below-fold images lazy-load after the first viewport.\n  - Visible copy and conversion paths remain unchanged.\n- Risk/cost: Reversible; no spend.\n- Branch: cmo-changes\n''')
        self.assertEqual(len(tasks[0]['decision_summary']), 3)
        self.assertEqual(tasks[0]['risk_cost'], 'Reversible; no spend.')
        self.assertIn('approval_valid', dashboard_server.task_change_metadata(tasks[0]))

    def test_human_approval_without_summary_is_invalid(self):
        task = parse_tasks('## Human Approval\n\n### TASK-9 — Missing packet\n- ID: TASK-9\n- Status: Human Approval\n')[0]
        self.assertFalse(dashboard_server.task_change_metadata(task)['approval_valid'])

    def test_snapshot_reports_health_from_tmux_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp) / 'tasks.md'
            board.write_text('## Backlog\n_No tasks._\n', encoding='utf-8')
            with patch('dashboard_server.subprocess.run') as run:
                run.return_value.stdout = 'cmo-content: 1 windows\ncmo-seo: 1 windows\n'
                run.return_value.returncode = 0
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertEqual(snapshot['health']['content'], 'alive')
        self.assertEqual(snapshot['health']['seo'], 'alive')
        self.assertEqual(snapshot['health']['social'], 'dead')
        self.assertEqual(snapshot['health']['watchdog'], 'dead')


class AuthTests(unittest.TestCase):
    def test_basic_auth_uses_environment_credentials(self):
        token = base64.b64encode(b'alice:secret').decode()
        with patch.dict(os.environ, {'CMO_DASHBOARD_USERNAME': 'alice', 'CMO_DASHBOARD_PASSWORD': 'secret'}, clear=False):
            self.assertTrue(valid_basic_auth('Basic ' + token))
            self.assertFalse(valid_basic_auth('Basic ' + base64.b64encode(b'alice:wrong').decode()))


class ApprovalTests(unittest.TestCase):
    def test_task_metadata_exposes_rejection_thread_and_outstanding_round(self):
        task = parse_tasks('''## Human Approval

### TASK-8 — Threaded review
- ID: TASK-8
- Owner: content
- Status: Human Approval
- Approval thread 1 rejection: alice: update the CTA contrast
- Approval thread 1 reply: content: changed CTA contrast and added a regression check
- Approval thread 2 rejection: alice: also verify the mobile breakpoint
''')[0]
        metadata = dashboard_server.task_change_metadata(task)
        self.assertEqual([event['type'] for event in metadata['approval_thread']], ['rejection', 'reply', 'rejection'])
        outstanding = dashboard_server.outstanding_rejection(task)
        self.assertIsNotNone(outstanding)
        self.assertEqual('2', outstanding['round'])

    def test_reject_appends_thread_event_to_task_card(self):
        board = '''## Human Approval

### TASK-8 — Threaded review
- ID: TASK-8
- Owner: content
- Status: Human Approval
- Decision summary:
  - Change one is limited.
  - Change two is reversible.
  - No spend is required.

## In Progress
_No tasks._
'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board_path = root / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            with patch.object(dashboard_server, 'TASKS_FILE', board_path), \
                 patch.object(dashboard_server, 'BOARD_LOCK', root / 'tasks.lock'), \
                 patch.object(dashboard_server, 'APPROVAL_LOG', root / 'approvals.log'), \
                 patch.object(dashboard_server, 'HUMAN_APPROVALS', root / 'approvals.json'), \
                 patch.object(dashboard_server, '_queue_approved_work'):
                result = apply_approval('TASK-8', 'reject', 'Please fix the mobile breakpoint.', 'alice')
            updated = board_path.read_text(encoding='utf-8')
        self.assertTrue(result['ok'])
        self.assertIn('- Approval thread 1 rejection: alice: Please fix the mobile breakpoint.', updated)

    def test_reject_requires_comment_without_touching_board(self):
        with self.assertRaises(ValueError):
            apply_approval('TASK-4', 'reject', '', 'alice')

    def test_invalid_approval_returns_task_to_agent(self):
        board = '''## Human Approval\n\n### TASK-4 — Missing packet\n- ID: TASK-4\n- Owner: ads\n- Status: Human Approval\n\n## In Progress\n_No tasks._\n'''
        with tempfile.TemporaryDirectory() as tmp:
            board_path = Path(tmp) / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            with patch.object(dashboard_server, 'TASKS_FILE', board_path), patch.object(dashboard_server, 'BOARD_LOCK', Path(tmp) / 'tasks.lock'):
                result = apply_approval('TASK-4', 'approve', '', 'alice')
            updated = board_path.read_text(encoding='utf-8')
        self.assertTrue(result['returned_to_agent'])
        self.assertIn('- Status: In Progress', updated)
        self.assertIn('Returned to agent', updated)
    def test_approval_moves_only_human_approval_task_and_records_fields(self):
        board = '''## Human Approval\n\n### TASK-4 — Approve\n- ID: TASK-4\n- Title: Approve\n- Owner: ads\n- Status: Human Approval\n- Decision summary:\n  - The reviewed ad copy changes will be applied.\n  - Tracking remains unchanged.\n  - The branch can be reverted if validation fails.\n- Last updated: old\n\n## In Progress\n_No tasks._\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board_path = root / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            state = root / 'state'
            log = root / 'approvals.log'
            with patch.object(dashboard_server, 'TASKS_FILE', board_path), \
                 patch.object(dashboard_server, 'BOARD_LOCK', state / 'tasks.lock'), \
                 patch.object(dashboard_server, 'APPROVAL_LOG', log), \
                 patch.object(dashboard_server, '_queue_approved_work') as queue:
                result = apply_approval('TASK-4', 'approve', 'ship the reviewed patch', 'alice')
            updated = board_path.read_text(encoding='utf-8')
            approval_log = log.read_text(encoding='utf-8')
        self.assertEqual(result['decision'], 'approve')
        self.assertIn('## In Progress', updated)
        self.assertIn('- Status: In Progress', updated)
        self.assertIn('- Human decision: approve', updated)
        self.assertIn('- Human decision by: alice', updated)
        queue.assert_called_once()
        self.assertIn('"task_id": "TASK-4"', approval_log)
    def test_website_approval_deploys_preview_without_queueing_worker(self):
        board = '''## Human Approval\n\n### TASK-7 — Landing page\n- ID: TASK-7\n- Title: Landing page\n- Owner: content\n- Status: Human Approval\n- Affected pages: https://itarang.com/\n- Change commit: abcdef1234567\n- Decision summary:\n  - Hero copy changes on the landing page.\n  - CTA remains unchanged.\n  - Mobile layout is visually reviewed in preview.\n\n## In Progress\n_No tasks._\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board_path = root / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            metrics = root / 'metrics'
            metrics.mkdir()
            (metrics / 'TASK-7.baseline.json').write_text(json.dumps({'status': 'captured'}), encoding='utf-8')
            active = root / 'active.json'
            with (patch.object(dashboard_server, 'TASKS_FILE', board_path),
                  patch.object(dashboard_server, 'BOARD_LOCK', root / 'tasks.lock'),
                  patch.object(dashboard_server, 'ACTIVE_FILE', active),
                  patch.object(dashboard_server, 'APPROVAL_LOG', root / 'approvals.log'),
                  patch.object(dashboard_server, 'HUMAN_APPROVALS', root / 'approvals.json'),
                  patch.object(dashboard_server, 'METRICS_DIR', metrics),
                  patch.object(dashboard_server, 'deploy_preview', return_value={'preview_url': 'https://itarangwebsite.vercel.app'}) as deploy,
                  patch.object(dashboard_server, 'post_discord') as discord,
                  patch.object(dashboard_server, '_queue_approved_work') as queue):
                result = apply_approval('TASK-7', 'approve', 'looks good', 'alice')
            self.assertTrue(result['ok'])
            deploy.assert_called_once_with('TASK-7', 'abcdef1234567')
            discord.assert_called_once()
            queue.assert_not_called()
            state = json.loads(active.read_text(encoding='utf-8'))
            self.assertTrue(state['TASK-7']['awaiting_merge'])
            self.assertEqual('abcdef1234567', state['TASK-7']['commit'])


if __name__ == '__main__':
    unittest.main()
