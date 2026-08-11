from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SKILL_NAMES = ("seo", "content", "social", "ads", "ops")
SKILL_DECLARATION = re.compile(r"^SKILL:\s+(\w+)\s*$")


class SkillLoaderError(ValueError):
    pass


class DisabledSkillError(SkillLoaderError):
    pass


@dataclass(frozen=True)
class LoadedSkill:
    name: str
    path: Path
    content: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SkillLoader:
    def __init__(
        self,
        skill_dir: str | Path,
        *,
        reader: Callable[[Path], str] | None = None,
    ) -> None:
        self.skill_dir = Path(skill_dir)
        self.reader = reader or _read_text

    def load(self, name: str) -> LoadedSkill:
        if name not in SKILL_NAMES:
            raise SkillLoaderError(f"unknown skill: {name}")
        path = self.skill_dir / f"{name}.skill"
        try:
            content = self.reader(path)
        except OSError as error:
            raise SkillLoaderError(f"cannot read skill {name}: {error}") from error

        first_line = content.splitlines()[0] if content else ""
        declaration = SKILL_DECLARATION.fullmatch(first_line)
        if declaration is None or declaration.group(1) != name:
            raise SkillLoaderError(f"{path} does not declare SKILL: {name}")
        if "skill disabled" in content.lower():
            if name == "ops":
                raise DisabledSkillError(
                    "ops is disabled: the human must supply a one-line objective and approve a KPI set"
                )
            raise DisabledSkillError(f"{name} is disabled by {path.name}")
        return LoadedSkill(name=name, path=path, content=content)


class SkillFileAudit:
    """Record actual Python open events for the five CMO skill files."""

    def __init__(self, skill_dir: str | Path) -> None:
        self.skill_dir = Path(skill_dir).resolve()
        self.reads: list[Path] = []

    def hook(self, event: str, args: tuple[object, ...]) -> None:
        if event != "open" or len(args) < 2:
            return
        raw_path, raw_mode = args[0], args[1]
        if not isinstance(raw_path, (str, bytes)):
            return
        if not isinstance(raw_mode, str) or "r" not in raw_mode:
            return
        path = Path(raw_path).resolve()
        if path.parent == self.skill_dir and path.name in {
            f"{name}.skill" for name in SKILL_NAMES
        }:
            self.reads.append(path)

    def evidence(self) -> dict[str, object]:
        counts = {
            name: self.reads.count(self.skill_dir / f"{name}.skill")
            for name in SKILL_NAMES
        }
        return {
            "source": "Python sys.addaudithook open events",
            "read_counts": counts,
            "read_event_paths": [str(path) for path in self.reads],
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load exactly one iTarang CMO skill")
    parser.add_argument("name", choices=SKILL_NAMES)
    parser.add_argument("--dir", default="cmo_skills", dest="skill_dir")
    parser.add_argument("--evidence", action="store_true")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    audit = SkillFileAudit(args.skill_dir) if args.evidence else None
    if audit is not None:
        sys.addaudithook(audit.hook)
    try:
        loaded = SkillLoader(args.skill_dir).load(args.name)
    except SkillLoaderError as error:
        print(f"ERROR: {error}")
        if audit is not None:
            print(json.dumps(audit.evidence(), indent=2))
        return 2

    print(loaded.content, end="" if loaded.content.endswith("\n") else "\n")
    if audit is not None:
        print(json.dumps(audit.evidence(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
