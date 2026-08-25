from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_BENCHMARK = SKILL_ROOT / "references" / "stock-analyzer-01.md"


class SkillPackagingTest(unittest.TestCase):
    def test_historical_benchmark_is_bundled_inside_skill(self) -> None:
        content = BUNDLED_BENCHMARK.read_text(encoding="utf-8")
        self.assertGreater(len(content), 4_000)
        self.assertIn("三、信息核验要求", content)
        self.assertIn("四、个股分析必须覆盖的内容", content)
        self.assertIn("十一、个股深度研究闭环", content)
        self.assertIn("十二、特别提醒", content)

    def test_repo_prompt_copy_stays_in_sync_when_available(self) -> None:
        repo_root = SKILL_ROOT.parent.parent
        repo_prompt = repo_root / "prompts" / "stock-analyzer-01.md"
        if not repo_prompt.is_file():
            self.skipTest("standalone skill package has no repository prompt copy")
        self.assertEqual(repo_prompt.read_bytes(), BUNDLED_BENCHMARK.read_bytes())


if __name__ == "__main__":
    unittest.main()
