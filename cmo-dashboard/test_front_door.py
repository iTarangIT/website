import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import front_door


class FrontDoorLoginTests(unittest.TestCase):
    def assembled_script(self) -> str:
        env = {
            "SUPABASE_URL": "https://project.example.test/",
            "SUPABASE_ANON_KEY": "public-anon-key",
        }
        with patch.dict(os.environ, env, clear=True):
            page = front_door._page().decode("utf-8")
        match = re.search(r"<script>(.*?)</script>", page, re.DOTALL)
        self.assertIsNotNone(match, "assembled login page must contain an inline script")
        return match.group(1)

    def test_assembled_page_contains_complete_supabase_password_request(self):
        script = self.assembled_script()
        expected_request = """const auth=await fetch(config.url.replace(/\\/$/,'')+'/auth/v1/token?grant_type=password',{
   method:'POST',
   headers:{apikey:config.anon_key,'Content-Type':'application/json'},
   body:JSON.stringify({email:fields.get('email'),password:fields.get('password')})
  });"""
        self.assertIn('const config={"url":"https://project.example.test/","anon_key":"public-anon-key"};', script)
        self.assertIn(expected_request, script)

    def test_assembled_page_javascript_parses_with_node(self):
        script = self.assembled_script()
        with tempfile.TemporaryDirectory() as directory:
            script_path = Path(directory) / "front-door.js"
            script_path.write_text(script, encoding="utf-8")
            result = subprocess.run(
                ["node", "--check", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
