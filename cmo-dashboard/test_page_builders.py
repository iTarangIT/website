import importlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import page_builders


class PageBuilderEnumerationTests(unittest.TestCase):
    def test_every_page_builder_assembles_and_its_inline_javascript_parses(self):
        discovered = []
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://auth.invalid", "SUPABASE_ANON_KEY": "test-anon-key"},
            clear=False,
        ):
            for name, builder in page_builders.iter_page_builders():
                discovered.append(name)
                page = builder().decode("utf-8")
                scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", page, re.S | re.I)
                self.assertTrue(scripts, f"{name} must contain an inline script")
                for index, script in enumerate(scripts):
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".js", encoding="utf-8", delete=False
                    ) as handle:
                        handle.write(script)
                        script_path = Path(handle.name)
                    try:
                        result = subprocess.run(
                            ["node", "--check", str(script_path)],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                    finally:
                        script_path.unlink(missing_ok=True)
                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{name} inline script {index} failed Node parsing:\n{result.stderr}",
                    )
        expected = sorted(path.stem for path in Path(__file__).parent.glob("*_page.py"))
        self.assertEqual(discovered, expected)


if __name__ == "__main__":
    unittest.main()
