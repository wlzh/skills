import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('safe_blog', Path(__file__).resolve().parents[1] / 'scripts/youtube_to_post.py')
blog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blog)


class PublishSafetyTests(unittest.TestCase):
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

    def test_publisher_requires_scoped_post(self):
        with self.assertRaises(ValueError):
            blog.deploy_to_git('/tmp')
