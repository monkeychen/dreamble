#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

from validate_package import validate_package


class ValidatePackageTest(unittest.TestCase):
    def make_package(self, skill_text: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "references").mkdir()
        (root / "SKILL.md").write_text(skill_text, encoding="utf-8")
        return root

    def test_accepts_internal_link(self) -> None:
        root = self.make_package("[参考](references/guide.md)")
        (root / "references" / "guide.md").write_text("ok", encoding="utf-8")
        self.assertEqual(validate_package(root), [])

    def test_rejects_escaping_link(self) -> None:
        root = self.make_package("[外部](../prompt.md)")
        self.assertTrue(any("escapes package" in item for item in validate_package(root)))

    def test_rejects_missing_internal_link(self) -> None:
        root = self.make_package("[缺失](references/missing.md)")
        self.assertTrue(any("missing local link" in item for item in validate_package(root)))

    def test_rejects_generated_cache(self) -> None:
        root = self.make_package("ok")
        (root / "scripts" / "__pycache__").mkdir(parents=True)
        self.assertTrue(any("generated cache" in item for item in validate_package(root)))


if __name__ == "__main__":
    unittest.main()
