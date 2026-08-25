from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).with_name("prepare_site_post.py")


class PrepareSitePostTest(unittest.TestCase):
    def test_builds_site_frontmatter_and_copies_images(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "run"
            source_dir.mkdir()
            (source_dir / "article.md").write_text(
                "---\ntitle: 旧标题\ncoverImage: ./imgs/cover.png\n---\n\n## 正文\n\n内容。\n",
                encoding="utf-8",
            )
            (source_dir / "imgs").mkdir()
            (source_dir / "imgs" / "cover.png").write_bytes(b"png")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source_dir / "article.md"),
                    "--output-root",
                    str(root / "output"),
                    "--date",
                    "2026-08-24",
                    "--slug",
                    "sample-stock",
                    "--title",
                    "新标题",
                    "--summary",
                    "摘要",
                    "--tag",
                    "A股",
                    "--source-wechat",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            destination = root / "output" / "2026-08-24-sample-stock"
            output = (destination / "index.md").read_text(encoding="utf-8")
            self.assertIn('title: "新标题"', output)
            self.assertIn('summary: "摘要"', output)
            self.assertIn('tags: ["A股"]', output)
            self.assertIn("source: wechat", output)
            self.assertNotIn("coverImage:", output)
            self.assertIn("## 正文", output)
            self.assertTrue((destination / "imgs" / "cover.png").is_file())

    def test_allows_draft_wechat_source_combination(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "article.md"
            source.write_text("正文", encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output-root",
                    str(root / "output"),
                    "--date",
                    "2026-08-24",
                    "--slug",
                    "sample-stock",
                    "--title",
                    "标题",
                    "--source-wechat",
                    "--draft",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            output = (
                root / "output" / "2026-08-24-sample-stock" / "index.md"
            ).read_text(encoding="utf-8")
            self.assertIn("source: wechat", output)
            self.assertIn("draft: true", output)

    def test_rejects_unclosed_frontmatter_without_partial_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "article.md"
            source.write_text("---\ntitle: 标题\n正文", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output-root",
                    str(root / "output"),
                    "--date",
                    "2026-08-24",
                    "--slug",
                    "sample-stock",
                    "--title",
                    "标题",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no closing delimiter", result.stderr)
            self.assertFalse((root / "output" / "2026-08-24-sample-stock").exists())


if __name__ == "__main__":
    unittest.main()
