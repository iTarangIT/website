import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'scripts' / 'hourly-cycle.py'
spec = importlib.util.spec_from_file_location('hourly_cycle', SCRIPT)
hourly = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(hourly)


class HourlyCycleContractTests(unittest.TestCase):
    def test_parse_website_implementation_requires_commit_and_three_lines(self):
        result = hourly.parse_implementation_result(
            '{"commit":"abcdef1","look":["Check hero","Check mobile","Check CTA"]}'
        )
        self.assertEqual('abcdef1', result['commit'])
        self.assertEqual(3, len(result['look']))
        self.assertEqual('', result['reply'])
        with self.assertRaises(ValueError):
            hourly.parse_implementation_result('{"commit":"abcdef1","look":["Only one"]}')

    def test_rejection_reply_is_detected_and_thread_is_mirrored(self):
        task = {'fields': {
            'Approval thread 1 rejection': 'alice: fix contrast',
            'Approval thread 1 reply': 'content: fixed contrast',
            'Approval thread 2 rejection': 'alice: check mobile',
        }}
        self.assertEqual('2', hourly.outstanding_rejection(task)['round'])
        self.assertIn('Round 1 reply: content: fixed contrast', hourly.thread_message(task))

    def test_website_task_is_explicit_not_guessed_from_free_text(self):
        task = {'fields': {'Change type': 'website'}}
        self.assertTrue(hourly.is_website_change(task))
        self.assertFalse(hourly.is_website_change({'fields': {'Objective': 'website audit only'}}))

    def test_metrics_summary_is_single_line_for_markdown_card(self):
        rows = [{'metric': 'performance score', 'before': 80, 'after': 90, 'delta': 10}]
        self.assertEqual('performance score: 80 → 90 (+10)', hourly.metric_summary(rows))


if __name__ == '__main__':
    unittest.main()
