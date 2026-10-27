import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('safe_blog', Path(__file__).resolve().parents[1] / 'scripts/youtube_to_post.py')
blog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blog)


class PublishSafetyTests(unittest.TestCase):
    def test_fixed_appendix_is_excluded_from_metadata_not_body(self):
        body = 'Telegram 登录排查，先检查已有设备上的官方验证码与当前账号的验证方式。'
        appendix = '\n## 短信及语音接码平台\nVPS Codex OpenAI 推荐\n' + '固定资源内容。' * 40
        self.assertEqual(blog.editorial_text(body + appendix), body)
        keywords = blog.generate_seo_keywords('Telegram 登录', body + appendix, ['Telegram'])
        self.assertNotIn('VPS', keywords)
        self.assertNotIn('Codex', keywords)
        self.assertEqual(blog.generate_seo_description('Telegram 登录', body + appendix),
                         blog.generate_seo_description('Telegram 登录', body))
        result = blog.generate_article_content_with_body(
            {'description': body + appendix, 'duration': 60, 'uploader': 'test'},
            'abcdefghijk', body)
        self.assertIn('短信及语音接码平台', result)
        self.assertIn(body, result)

    def test_editorial_code_is_not_metadata_and_real_vps_topic_survives(self):
        self.assertEqual(blog.editorial_text('正文\n```text\n## 关注与资源\n```\n结束'), '正文\n结束')
        self.assertIn('VPS', blog.generate_seo_keywords('VPS 配置', 'VPS 部署步骤。', ['VPS']))

    def test_existing_slug_is_not_duplicated_or_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'same.md'
            path.write_text('original')
            with self.assertRaises(FileExistsError):
                blog.save_post('new', 'same', directory, 'title', False)
            self.assertEqual(path.read_text(), 'original')
            self.assertEqual(len(list(Path(directory).glob('*.md'))), 1)

    def test_title_does_not_invent_specialized_coverage(self):
        summary = blog.generate_seo_description('Happy Claude Code', '')
        self.assertNotIn('自建中继', summary)

    def test_keywords_do_not_invent_product_features(self):
        happy = blog.extract_semantic_keywords('Happy Claude Code', '产品介绍。')
        self.assertNotIn('E2EE加密', happy)
        self.assertNotIn('远程开发', happy)
        mail = blog.extract_semantic_keywords('Cloudflare 邮箱', '邮箱设置介绍。')
        for keyword in ['D1数据库', 'KV缓存', '免费邮箱', 'Workers']:
            self.assertNotIn(keyword, mail)

    def test_publisher_requires_scoped_post(self):
        with self.assertRaises(ValueError):
            blog.deploy_to_git('/tmp')
