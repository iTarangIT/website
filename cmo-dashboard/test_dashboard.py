import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dashboard_server
from dashboard_server import (apply_approval, build_snapshot, load_task_attachment,
                              parse_tasks, summarize_gsc, valid_basic_auth)


class DashboardDataTests(unittest.TestCase):
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
            with patch('dashboard_server.subprocess.run') as run, \
                 patch('dashboard_server.gsc_summary',
                       return_value=summarize_gsc([], {})):
                run.return_value.stdout = 'cmo-content: 1 windows\ncmo-seo: 1 windows\n'
                run.return_value.returncode = 0
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertEqual(snapshot['health']['content'], 'alive')
        self.assertEqual(snapshot['health']['seo'], 'alive')
        self.assertEqual(snapshot['health']['social'], 'dead')
        self.assertEqual(snapshot['health']['watchdog'], 'dead')


    def test_snapshot_exposes_one_active_task_drafts_and_skill_lanes(self):
        board_text = '''## Backlog\n\n### TASK-1 — Queue\n- ID: TASK-1\n- Owner: seo\n- Skill: seo\n- Priority: high\n- Status: Backlog\n- Attachment: none\n\n## In Progress\n\n### TASK-2 — Active\n- ID: TASK-2\n- Owner: content\n- Skill: content\n- Priority: critical\n- Status: In Progress\n- Attachment: artifacts/TASK-2.md\n\n## CMO Review\n_No tasks._\n\n## Human Approval\n_No tasks._\n\n## Completed\n\n### TASK-3 — Done\n- ID: TASK-3\n- Owner: content\n- Skill: content\n- Priority: low\n- Status: Completed\n- Attachment: none\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'tasks.md'
            board.write_text(board_text, encoding='utf-8')
            (root / 'artifacts').mkdir()
            (root / 'artifacts' / 'TASK-2.md').write_text('# Draft', encoding='utf-8')
            with patch.object(dashboard_server, 'PROFILE_DIR', root), \
                 patch.object(dashboard_server, 'git_change_metadata', return_value={
                     'branch': '', 'commits': '', 'files_changed': '', 'commit_url': '',
                     'branch_url': '', 'evidence': 'no branch evidence'}), \
                 patch.object(dashboard_server, 'tmux_health', return_value={}), \
                 patch.object(dashboard_server, 'gsc_summary',
                              return_value=summarize_gsc([], {})):
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertEqual(snapshot['current_work']['id'], 'TASK-2')
        self.assertEqual([task['id'] for task in snapshot['drafts']], ['TASK-2'])
        self.assertEqual(snapshot['drafts'][0]['attachment_url'], '/api/attachment?task=TASK-2')
        self.assertEqual([task['id'] for task in snapshot['skill_lanes']['seo']['queue']], ['TASK-1'])
        self.assertEqual([task['id'] for task in snapshot['skill_lanes']['content']['completed']], ['TASK-3'])
        self.assertEqual(set(snapshot['skill_lanes']), {'seo', 'content', 'social', 'ads', 'ops'})

    def test_board_counts_combine_task_list_and_track_dynamic_columns(self):
        board_text = '''## Backlog\n\n### TASK-1 — Queued\n- ID: TASK-1\n- Owner: seo\n- Skill: seo\n- Status: Backlog\n\n## In Progress\n\n### TASK-2 — Active\n- ID: TASK-2\n- Owner: content\n- Skill: content\n- Status: In Progress\n\n## Research\n\n### TASK-3 — Dynamic column\n- ID: TASK-3\n- Owner: ops\n- Skill: ops\n- Status: Research\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'tasks.md'
            board.write_text(board_text, encoding='utf-8')
            with patch.object(dashboard_server, 'PROFILE_DIR', root), \
                 patch.object(dashboard_server, 'git_change_metadata', return_value={
                     'branch': '', 'commits': '', 'files_changed': '', 'commit_url': '',
                     'branch_url': '', 'evidence': 'no branch evidence'}), \
                 patch.object(dashboard_server, 'tmux_health', return_value={}), \
                 patch.object(dashboard_server, 'gsc_summary',
                              return_value=summarize_gsc([], {})):
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        counts = snapshot['board_counts']
        self.assertEqual(snapshot['board_columns'], ['Task List', 'Research'])
        self.assertEqual(counts['Task List'], 2)
        self.assertEqual(counts['Research'], 1)
        self.assertEqual(sorted(counts), sorted(snapshot['board_columns']))
        for column in snapshot['board_columns']:
            self.assertEqual(counts[column],
                             len([task for task in snapshot['tasks'] if task['board_column'] == column]))

    def test_board_counts_are_empty_without_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'tasks.md'
            board.write_text('## Backlog\n_No tasks._\n', encoding='utf-8')
            with patch.object(dashboard_server, 'PROFILE_DIR', root), \
                 patch.object(dashboard_server, 'tmux_health', return_value={}), \
                 patch.object(dashboard_server, 'gsc_summary',
                              return_value=summarize_gsc([], {})):
                snapshot = build_snapshot(board, tmux_bin='/bin/tmux')
        self.assertEqual(snapshot['board_counts'], {})
        self.assertEqual(snapshot['board_columns'], [])

    def test_effective_board_renderer_shows_snapshot_backed_column_counts(self):
        effective = dashboard_server.INDEX_HTML.rsplit('render=function(next)', 1)[1]
        self.assertIn("const countLabel=n=>`${n} ${n===1?'task':'tasks'}`;", dashboard_server.INDEX_HTML)
        self.assertIn('.column-count{', dashboard_server.INDEX_HTML)
        self.assertIn('const counts=next.board_counts||{};', effective)
        self.assertIn('<span class="column-count">${esc(countLabel(counts[column]||0))}</span>', effective)

    def test_task_attachment_is_resolved_from_parser_and_markdown_renders_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / 'artifacts' / 'TASK-9.md'
            artifact.parent.mkdir()
            artifact.write_text('# Draft\n\n<script>alert(1)</script>', encoding='utf-8')
            board = root / 'tasks.md'
            board.write_text('''## CMO Review\n\n### TASK-9 — Draft\n- ID: TASK-9\n- Owner: content\n- Skill: content\n- Status: CMO Review\n- Attachment: artifacts/TASK-9.md\n''', encoding='utf-8')
            content_type, body = load_task_attachment('TASK-9', board, root)
        rendered = body.decode('utf-8')
        self.assertEqual(content_type, 'text/html; charset=utf-8')
        self.assertIn('<h1>Draft</h1>', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_task_attachment_refuses_paths_outside_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'tasks.md'
            board.write_text('''## CMO Review\n\n### TASK-9 — Draft\n- ID: TASK-9\n- Owner: content\n- Status: CMO Review\n- Attachment: /etc/passwd\n''', encoding='utf-8')
            with self.assertRaises(PermissionError):
                load_task_attachment('TASK-9', board, root)

    def test_gsc_empty_rows_are_collecting_not_zero_or_declining(self):
        summary = summarize_gsc([], {'sitemap': []})
        self.assertEqual(summary['status'], 'collecting')
        self.assertIsNone(summary['impressions'])
        self.assertIsNone(summary['clicks'])
        self.assertIsNone(summary['average_position'])
        self.assertIsNone(summary['indexed_pages'])
        self.assertEqual(summary['collection_start'], '2026-08-04')

    def test_gsc_summary_uses_aggregate_row_and_sitemap_indexed_pages(self):
        summary = summarize_gsc(
            [{'clicks': 3, 'impressions': 20, 'position': 7.25}],
            {'sitemap': [{'contents': [{'type': 'WEB', 'submitted': '12', 'indexed': '9'}]}]},
        )
        self.assertEqual(summary['status'], 'ready')
        self.assertEqual(summary['clicks'], 3)
        self.assertEqual(summary['impressions'], 20)
        self.assertEqual(summary['average_position'], 7.25)
        self.assertEqual(summary['indexed_pages'], 9)


class AuthTests(unittest.TestCase):
    def test_basic_auth_uses_environment_credentials(self):
        token = base64.b64encode(b'alice:secret').decode()
        with patch.dict(os.environ, {'CMO_DASHBOARD_USERNAME': 'alice', 'CMO_DASHBOARD_PASSWORD': 'secret'}, clear=False):
            self.assertTrue(valid_basic_auth('Basic ' + token))
            self.assertFalse(valid_basic_auth('Basic ' + base64.b64encode(b'alice:wrong').decode()))


class ApprovalTests(unittest.TestCase):
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

    def test_website_approval_deploys_existing_commit_then_waits_for_human_merge(self):
        board = '''## Human Approval\n\n### TASK-7 — Website hero\n- ID: TASK-7\n- Title: Website hero\n- Owner: content\n- Status: Human Approval\n- Change type: website\n- Affected pages: /\n- Change commit: abc1234\n- Agent summary 1: Compare the hero headline.\n- Agent summary 2: Compare the primary CTA.\n- Agent summary 3: Check mobile spacing.\n- Decision summary:\n  - The branch implementation changes only the homepage hero.\n  - The CTA target remains unchanged.\n  - The commit is reversible before merge.\n- Last updated: old\n\n## In Progress\n_No tasks._\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board_path = root / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            metrics = root / 'website-metrics'
            metrics.mkdir()
            (metrics / 'TASK-7.baseline.json').write_text('{"status":"captured","pages":[]}', encoding='utf-8')
            with patch.object(dashboard_server, 'TASKS_FILE', board_path), \
                 patch.object(dashboard_server, 'BOARD_LOCK', root / 'tasks.lock'), \
                 patch.object(dashboard_server, 'APPROVAL_LOG', root / 'approvals.log'), \
                 patch.object(dashboard_server, 'ACTIVE_FILE', root / 'active.json'), \
                 patch.object(dashboard_server, 'METRICS_DIR', metrics), \
                 patch.object(dashboard_server, 'deploy_preview', return_value={'preview_url': 'https://preview.example'}) as deploy, \
                 patch.object(dashboard_server, 'evidence_message', return_value='preview evidence') as evidence, \
                 patch.object(dashboard_server, '_post_discord') as post, \
                 patch.object(dashboard_server, '_queue_approved_work') as queue:
                result = apply_approval('TASK-7', 'approve', 'preview it', 'alice')
            updated = board_path.read_text(encoding='utf-8')
            active = json.loads((root / 'active.json').read_text(encoding='utf-8'))
        deploy.assert_called_once_with('TASK-7', 'abc1234')
        evidence.assert_called_once()
        post.assert_called_once_with('preview evidence')
        queue.assert_not_called()
        self.assertEqual(result['preview_url'], 'https://preview.example')
        self.assertTrue(active['TASK-7']['awaiting_merge'])
        self.assertEqual(active['TASK-7']['commit'], 'abc1234')
        self.assertIn('- Preview URL: https://preview.example', updated)
        self.assertIn('- Change status: Preview ready; awaiting human merge to main.', updated)
        self.assertIn('- Status: In Progress', updated)

    def test_website_approval_refuses_missing_baseline_or_three_line_note(self):
        board = '''## Human Approval\n\n### TASK-8 — Website hero\n- ID: TASK-8\n- Owner: content\n- Status: Human Approval\n- Change type: website\n- Affected pages: /\n- Change commit: abc1234\n- Agent summary 1: One line only.\n- Decision summary:\n  - First concrete review point.\n  - Second concrete review point.\n  - Third concrete review point.\n\n## In Progress\n_No tasks._\n'''
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            board_path = root / 'tasks.md'
            board_path.write_text(board, encoding='utf-8')
            with patch.object(dashboard_server, 'TASKS_FILE', board_path), \
                 patch.object(dashboard_server, 'BOARD_LOCK', root / 'tasks.lock'), \
                 patch.object(dashboard_server, 'METRICS_DIR', root / 'website-metrics'):
                with self.assertRaises(RuntimeError):
                    apply_approval('TASK-8', 'approve', '', 'alice')
            self.assertEqual(board_path.read_text(encoding='utf-8'), board)


if __name__ == '__main__':
    unittest.main()
