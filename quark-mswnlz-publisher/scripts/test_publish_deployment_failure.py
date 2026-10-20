import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "publisher", Path(__file__).with_name("mswnlz_publish.py")
)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class DeploymentFailureTests(unittest.TestCase):
    def test_deployment_failure_is_not_swallowed(self):
        with patch.object(publisher.subprocess, "run", return_value=SimpleNamespace(
            returncode=1, stderr="production release mismatch", stdout=""
        )):
            with self.assertRaises(RuntimeError):
                publisher.trigger_site_rebuild()

    def test_timeout_is_not_swallowed(self):
        with patch.object(publisher.subprocess, "run", side_effect=TimeoutError("test")):
            with self.assertRaises(RuntimeError):
                publisher.trigger_site_rebuild()


if __name__ == "__main__":
    unittest.main()
