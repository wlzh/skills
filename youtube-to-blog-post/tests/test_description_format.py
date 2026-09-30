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
    def test_video_upload_date_normalizes_yt_dlp_compact_date(self):
        self.assertEqual(
            blog.normalize_video_upload_date("20250726"),
            "2025-07-26T00:00:00Z",
        )

    def test_video_upload_date_rejects_missing_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            blog.normalize_video_upload_date("2025-07-26T12:30:00")

    def test_video_upload_date_rejects_invalid_time(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            blog.normalize_video_upload_date("2025-02-24T23:302:51Z")

    def test_seo_description_meets_shared_length_contract(self):
        description = blog.generate_seo_description("测试工具教程", "这是一句很短的介绍。")
        self.assertGreaterEqual(len(description), 45)
        self.assertLessEqual(len(description), 160)
        self.assertFalse(description.startswith("#"))

    def test_seo_description_preserves_decimal_numbers(self):
        description = blog.generate_seo_description(
            "菲律宾 DITO eSIM 低成本保号教程",
            "菲律宾 DITO eSIM 全流程教程，每年只需 0.6 元人民币即可低成本保号，涵盖开卡、充值和大陆漫游。",
        )
        self.assertIn("0.6", description)
        self.assertIn("低成本保号", description)

    def test_seo_description_rejects_source_code_candidates(self):
        description = blog.generate_seo_description(
            "ChatGPT Plus Gopay 开通教程",
            'console.log("ChatGPT Plus Gopay plan"); console.error("debug"). '
            "本教程介绍使用 Gopay 开通 ChatGPT Plus 的准备条件、接码步骤、付款流程和结果验证。",
        )
        self.assertNotIn("console", description)
        self.assertIn("Gopay", description)

    def test_baipiao_alias_becomes_canonical_heading(self):
        self.assertEqual(
            blog.description_heading_for_line("纯净住宅IP白嫖流量"),
            "## 白嫖流量",
        )
        self.assertTrue(blog.should_skip_heading_source_line("纯净住宅IP白嫖流量"))

    def test_resource_markers_become_headings_without_losing_following_urls(self):
        formatted = blog.format_description_as_markdown(
            "更多资料获取及讨论群\n"
            "1. 微信讨论群：https://qr.869hr.uk/aitech\n"
            "短信及语音接码平台\n"
            "https://hero-sms.com/?ref=357885"
        )
        self.assertIn("## 关注与资源", formatted)
        self.assertIn("## 短信及语音接码平台", formatted)
        self.assertIn("https://hero-sms.com/?ref=357885", formatted)

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

    def test_body_md_preserves_fenced_code_for_hexo_copy_button(self):
        body_md = """## 安装命令

```bash
npm install example-package
echo "安装完成"
```
"""
        content = blog.generate_post_content(
            {
                "id": "abc123XYZ",
                "title": "命令行工具安装教程",
                "description": "介绍命令行工具的安装、配置、验证方法与常见问题。",
                "uploader": "频道",
                "upload_date": "2026-07-26T12:00:00+08:00",
                "duration": 120,
                "thumbnail": "",
            },
            {"author": "M.", "local_thumbnail": "/images/test.jpg"},
            "技术",
            ["教程"],
            body_md=body_md,
        )
        humanized = blog.humanize_article(content, "命令行工具安装教程")
        self.assertIn(
            '```bash\nnpm install example-package\necho "安装完成"\n```',
            humanized,
        )

    def test_redundant_browser_copy_notice_is_removed_from_all_inputs(self):
        description = (
            "适用场景\n"
            "这是完整描述。" * 40
            + "\n注意⚠️链接需复制到浏览器中才能打开！！！"
        )
        content = blog.generate_post_content(
            {
                "id": "abc123XYZ",
                "title": "测试教程",
                "description": description,
                "uploader": "频道",
                "upload_date": "2026-07-23T12:00:00+08:00",
                "duration": 120,
                "thumbnail": "",
            },
            {"author": "M.", "local_thumbnail": "/images/test.jpg"},
            "技术",
            ["教程"],
            body_md="## 原始正文\n\n部分链接需要复制到浏览器中才能打开。\n\n正文保留。",
        )
        self.assertNotIn("复制到浏览器中才能打开", content)
        self.assertIn("正文保留。", content)

    def test_video_front_matter_and_tag_limit(self):
        content = blog.generate_post_content(
            {
                "id": "abc123XYZ",
                "title": "Oracle Cloud 免费 VPS 完整教程",
                "description": "介绍 Oracle Cloud 免费 VPS 的注册、配置、验证方法与常见问题。",
                "uploader": "频道",
                "upload_date": "2026-07-22T12:00:00+08:00",
                "duration": 252,
                "thumbnail": "",
            },
            {"author": "M.", "local_thumbnail": "/images/test.jpg"},
            "网络与 VPS",
            ["VPS", "Oracle", "云服务器", "教程", "免费资源", "多余标签"],
        )
        self.assertIn("video_id: abc123XYZ", content)
        self.assertIn("video_duration: 252", content)
        self.assertIn('video_upload_date: "2026-07-22T12:00:00+08:00"', content)
        self.assertIn("excerpt:", content)
        front_matter = content.split("---", 2)[1]
        tag_block = front_matter.split("tags:\n", 1)[1].split("\nkeywords:", 1)[0]
        self.assertEqual(tag_block.count("  - "), 5)
        self.assertNotIn("[相关推荐](https://869hr.uk)", content)


if __name__ == "__main__":
    unittest.main()
