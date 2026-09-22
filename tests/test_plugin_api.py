import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "dashboard" / "plugin_api.py"
spec = importlib.util.spec_from_file_location("ai_usage_tracker_plugin_api", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OpenCodeUsageTests(unittest.TestCase):
    def test_local_auth_key_is_read_for_requested_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = Path(directory) / "auth.json"
            auth_path.write_text(json.dumps({
                "opencode-go": {"type": "api", "key": "go-secret"},
                "opencode": {"type": "api", "key": "zen-secret"},
            }))

            self.assertEqual(module._opencode_local_auth_key("opencode-go", auth_path), "go-secret")
            self.assertEqual(module._opencode_local_auth_key("opencode-zen", auth_path), "zen-secret")

    def test_local_auth_key_does_not_cross_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            auth_path = Path(directory) / "auth.json"
            auth_path.write_text(json.dumps({"opencode": {"type": "api", "key": "zen-secret"}}))

            self.assertIsNone(module._opencode_local_auth_key("opencode-go", auth_path))

    def test_opencode_usage_probe_sends_browser_like_user_agent(self):
        captured = {}

        def fake_get_json(url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return {"usage": {"rolling": {"percent": 1}}}

        with patch.object(module, "_runtime_key", return_value="go-secret"), \
             patch.object(module, "_get_json", side_effect=fake_get_json):
            result = module._probe_opencode_go()

        self.assertTrue(result["available"])
        self.assertEqual(captured["url"], "https://opencode.ai/zen/go/v1/usage")
        self.assertTrue(captured["headers"]["User-Agent"])


if __name__ == "__main__":
    unittest.main()
