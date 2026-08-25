from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest

from prepare_article import prepare_article_text


SCRIPT = Path(__file__).with_name("prepare_article.py")


class PrepareArticleTest(unittest.TestCase):
    def test_adds_publish_metadata_without_rewriting_research_body(self) -> None:
        body = "# 核心结论\n\n数字、表格和判断必须原样保留。\n"
        source = f'---\ntitle: "研究报告"\nsummary: "研究摘要"\n---\n{body}'
        article, research_body = prepare_article_text(source)

        self.assertEqual(research_body, body)
        self.assertTrue(article.endswith(body))
        self.assertIn('coverImage: "./imgs/cover.png"', article)
        self.assertIn("![文章封面](./imgs/cover.png)", article)
        self.assertEqual(article.count("数字、表格和判断必须原样保留。"), 1)

    def test_does_not_duplicate_existing_inline_cover(self) -> None:
        source = (
            '---\ntitle: "研究报告"\nsummary: "研究摘要"\n---\n'
            "![已有封面](./imgs/cover.png)\n\n正文。\n"
        )
        article, _ = prepare_article_text(source)
        self.assertEqual(article.count("./imgs/cover.png)"), 1)

    def test_rejects_missing_required_frontmatter_without_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "analyst-report.md"
            destination = root / "article.md"
            source.write_text("---\ntitle: 报告\n---\n正文", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), str(destination)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires non-empty summary", result.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
