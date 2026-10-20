import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "release", Path(__file__).with_name("verify_pages_release.py")
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_token_is_passed_over_stdin_not_command_arguments(self):
        with patch.object(release.subprocess, "run", return_value=SimpleNamespace(
            returncode=0, stdout=b"ok"
        )) as run:
            self.assertEqual(release.fetch("https://api.cloudflare.com/test", "private"), b"ok")
            self.assertNotIn("private", " ".join(run.call_args.args[0]))
            self.assertIn(b"Bearer private", run.call_args.kwargs["input"])

    def test_http_error_fails_closed(self):
        with patch.object(release.subprocess, "run", return_value=SimpleNamespace(
            returncode=22, stdout=b""
        )):
            with self.assertRaises(RuntimeError):
                release.fetch("https://doc.869hr.uk/test")

    def test_wrong_account_fails_before_network(self):
        with patch.dict(os.environ, {"CLOUDFLARE_ACCOUNT_ID": "old"}):
            with patch.object(release, "fetch") as fetch:
                with self.assertRaises(RuntimeError):
                    release.project()
                fetch.assert_not_called()

    def test_preflight_uses_actual_subdomain(self):
        info = {"name": "doc869hr", "subdomain": "doc869hr-6r4.pages.dev"}
        with patch.dict(os.environ, {
            "CLOUDFLARE_ACCOUNT_ID": release.ACCOUNT,
            "CLOUDFLARE_API_TOKEN": "test-only",
            "CF_PAGES_PROJECT": "doc869hr",
        }):
            with patch.object(release, "fetch", return_value=json.dumps({
                "success": True, "result": info,
            }).encode()):
                self.assertEqual(release.project(), info)

    def test_stamp_is_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.argv", ["verify", "--stamp", directory]):
                release.main()
                first = (Path(directory) / release.MARKER).read_bytes()
                release.main()
                self.assertNotEqual(first, (Path(directory) / release.MARKER).read_bytes())

    def test_wrong_live_release_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / release.MARKER).write_text('{"release":"expected"}')
            with patch("sys.argv", ["verify", "--verify", directory]), \
                    patch.object(release, "project", return_value={
                        "name": "doc869hr", "subdomain": "new.pages.dev",
                        "domains": [release.DOMAIN],
                    }), \
                    patch.object(release, "fetch", return_value=b"old"), \
                    patch.object(release.time, "sleep"):
                with self.assertRaises(RuntimeError):
                    release.main()

    def test_verified_release_checks_both_hosts_and_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            expected = b'{"release":"expected"}'
            (Path(directory) / release.MARKER).write_bytes(expected)
            with patch("sys.argv", ["verify", "--verify", directory]), \
                    patch.object(release, "project", return_value={
                        "name": "doc869hr", "subdomain": "new.pages.dev",
                        "domains": [release.DOMAIN],
                    }), \
                    patch.object(release, "fetch", return_value=expected) as fetch:
                release.main()
                self.assertEqual(fetch.call_count, 6)
                self.assertIn("new.pages.dev", fetch.call_args_list[0].args[0])
                self.assertIn(release.DOMAIN, fetch.call_args_list[1].args[0])

    def test_missing_domain_fails_before_public_probes(self):
        with patch("sys.argv", ["verify", "--verify", "/unused"]), \
                patch.object(release, "project", return_value={
                    "name": "doc869hr", "subdomain": "new.pages.dev", "domains": [],
                }), \
                patch.object(release, "fetch") as fetch:
            with self.assertRaises(RuntimeError):
                release.main()
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
