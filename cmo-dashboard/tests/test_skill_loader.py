from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cmo_runtime.skill_loader import DisabledSkillError, SkillLoader


class SkillLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.skill_dir = Path(self.temp_dir.name)
        for name in ("seo", "content", "social", "ads"):
            (self.skill_dir / f"{name}.skill").write_text(
                f"SKILL:       {name}\nOBJECTIVE:   enabled objective\nKPIS:\nTOOLS:       none\n",
                encoding="utf-8",
            )
        (self.skill_dir / "ops.skill").write_text(
            "SKILL:       ops\n"
            "OBJECTIVE:   not defined — skill disabled\n"
            "KPIS:\n"
            "TOOLS:       none — skill disabled\n"
            "OUTPUT:      none — skill disabled until the human supplies a one-line objective and approves a KPI set\n",
            encoding="utf-8",
        )

    def test_load_reads_only_the_requested_skill_file(self) -> None:
        reads: list[Path] = []

        def reader(path: Path) -> str:
            reads.append(path)
            return path.read_text(encoding="utf-8")

        loaded = SkillLoader(self.skill_dir, reader=reader).load("seo")

        self.assertEqual(loaded.name, "seo")
        self.assertEqual(reads, [self.skill_dir / "seo.skill"])

    def test_disabled_ops_refuses_with_reason(self) -> None:
        with self.assertRaisesRegex(
            DisabledSkillError,
            "ops is disabled: the human must supply a one-line objective and approve a KPI set",
        ):
            SkillLoader(self.skill_dir).load("ops")


if __name__ == "__main__":
    unittest.main()
