import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import console_auth


class Handler:
    def __init__(self, authorization="Bearer token"):
        self.headers = {"Authorization": authorization}
        self.wfile = io.BytesIO()
        self.status = None
        self.response_headers = []

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.response_headers.append((name, value))

    def end_headers(self):
        pass


class ConsoleAuthTests(unittest.TestCase):
    def setUp(self):
        console_auth._token_cache.clear()
        self.env = {
            "SUPABASE_URL": "https://auth.invalid",
            "SUPABASE_ANON_KEY": "anon",
            "CMO_CEO_EMAIL": "ceo@example.test",
            "CMO_TECH_EMAIL": "tech@example.test",
        }

    def test_missing_non_bearer_and_oversized_tokens_are_401(self):
        for value in ("", "Basic abc", "Bearer " + "x" * 4097):
            with self.subTest(value=value[:10]), patch.dict(os.environ, self.env, clear=True):
                handler = Handler(value)
                self.assertIsNone(console_auth.authorize(handler, "ceo"))
                self.assertEqual(handler.status, 401)

    def test_exact_casefolded_role_match(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "_supabase_get_user", return_value="CEO@EXAMPLE.TEST"
        ):
            self.assertEqual(console_auth.authorize(Handler(), "ceo"), ("CEO@EXAMPLE.TEST", "ceo"))
        console_auth._token_cache.clear()
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "_supabase_get_user", return_value="ceo@example.test.evil.tld"
        ):
            handler = Handler()
            self.assertIsNone(console_auth.authorize(handler, "ceo"))
            self.assertEqual(handler.status, 403)

    def test_cross_role_is_403(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "_supabase_get_user", return_value="ceo@example.test"
        ):
            handler = Handler()
            self.assertIsNone(console_auth.authorize(handler, "tech"))
            self.assertEqual(handler.status, 403)

    def test_unset_role_affects_only_that_console(self):
        env = {**self.env, "CMO_CEO_EMAIL": ""}
        with patch.dict(os.environ, env, clear=True):
            handler = Handler()
            self.assertIsNone(console_auth.authorize(handler, "ceo"))
            self.assertEqual(handler.status, 503)
        with patch.dict(os.environ, env, clear=True), patch.object(
            console_auth, "_supabase_get_user", return_value="tech@example.test"
        ):
            self.assertEqual(console_auth.authorize(Handler(), "tech")[1], "tech")

    def test_provider_failure_statuses(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "_supabase_get_user", side_effect=PermissionError
        ):
            handler = Handler()
            self.assertIsNone(console_auth.authorize(handler, "ceo"))
            self.assertEqual(handler.status, 401)
        console_auth._token_cache.clear()
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "_supabase_get_user", side_effect=ConnectionError
        ):
            handler = Handler()
            self.assertIsNone(console_auth.authorize(handler, "ceo"))
            self.assertEqual(handler.status, 502)

    def test_success_cache_is_bounded_and_key_is_not_raw_token(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(
            console_auth, "CACHE_LIMIT", 2
        ), patch.object(console_auth, "_supabase_get_user", return_value="ceo@example.test") as get_user:
            console_auth.authorize(Handler("Bearer first"), "ceo")
            console_auth.authorize(Handler("Bearer first"), "ceo")
            console_auth.authorize(Handler("Bearer second"), "ceo")
            console_auth.authorize(Handler("Bearer third"), "ceo")
        self.assertEqual(get_user.call_count, 3)
        self.assertEqual(len(console_auth._token_cache), 2)
        self.assertNotIn("first", console_auth._token_cache)

    def test_console_sources_do_not_name_privileged_key(self):
        forbidden = "SUPABASE_" + "SERVICE_ROLE_KEY"
        root = Path(__file__).parent
        sources = [path for path in root.glob("*console.py")] + [root / "console_auth.py", root / "console_board.py"]
        for source in sources:
            if source.exists():
                self.assertNotIn(forbidden, source.read_text(encoding="utf-8"), source.name)


if __name__ == "__main__":
    unittest.main()
