from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "youtube_to_post.py"
SPEC = importlib.util.spec_from_file_location("youtube_to_post", SCRIPT)
assert SPEC and SPEC.loader
blog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blog)


class DescriptionFormatTests(unittest.TestCase):
    def test_baipiao_alias_becomes_canonical_heading(self):
        self.assertEqual(
            blog.description_heading_for_line("纯净住宅IP白嫖流量"),
            "## 白嫖流量",
        )
        self.assertTrue(blog.should_skip_heading_source_line("纯净住宅IP白嫖流量"))

    def test_body_md_keeps_body_and_appends_full_description(self):
        description = "适用场景\n" + "这是完整描述。" * 40
        content = blog.generate_article_content_with_body(
            {
                "uploader": "频道",
                "description": description,
                "duration": 120,
            },
            "video-id",
            "## 原始正文\n\n正文必须保留。",
        )
        self.assertIn("## 原始正文", content)
        self.assertIn("正文必须保留。", content)
        self.assertIn("适用场景", content)
        self.assertIn("这是完整描述。", content)


if __name__ == "__main__":
    unittest.main()
