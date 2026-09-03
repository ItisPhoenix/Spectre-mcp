import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_spectre(transport=None):
    module_name = "spectre_transport_under_test"
    sys.modules.pop(module_name, None)
    source = ROOT / "spectre.py"
    spec = importlib.util.spec_from_file_location(module_name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    real_makedirs = os.makedirs

    def ignore_output_dir(path, *args, **kwargs):
        if path == "/tmp/spectre":
            return None
        return real_makedirs(path, *args, **kwargs)

    try:
        with patch.object(os, "makedirs", side_effect=ignore_output_dir):
            with patch.dict(os.environ, {"SPECTRE_API_KEY": ""}, clear=False):
                for name in ("MCP_TRANSPORT", "MCP_HOST", "MCP_PORT"):
                    os.environ.pop(name, None)
                if transport is not None:
                    os.environ["MCP_TRANSPORT"] = transport
                spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


class TransportEnvironmentTests(unittest.TestCase):
    def test_unset_transport_defaults_to_streamable_http(self):
        self.assertEqual(load_spectre().TRANSPORT, "streamable-http")

    def test_explicit_streamable_http_is_preserved(self):
        self.assertEqual(load_spectre("streamable-http").TRANSPORT, "streamable-http")

    def test_explicit_sse_is_preserved(self):
        self.assertEqual(load_spectre("sse").TRANSPORT, "sse")

    def test_s1_localhost_host_default_is_preserved(self):
        module = load_spectre()
        self.assertEqual(module.HOST, "127.0.0.1")
        self.assertEqual(module.PORT, 8001)


class BundledConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "mcp-config.json").read_text(encoding="utf-8"))
        cls.server = cls.config["mcpServers"]["spectre"]

    def test_mcp_config_is_valid_json(self):
        self.assertIsInstance(self.config, dict)

    def test_mcp_config_uses_http_mcp_endpoint(self):
        self.assertEqual(self.server["type"], "http")
        self.assertEqual(self.server["url"], "http://localhost:8001/mcp")
        self.assertNotIn("/sse", self.server["url"])
        self.assertNotEqual(self.server["type"], "sse")
        self.assertNotEqual(self.server["type"], "streamable-http")

    def test_entrypoint_default_banner_matches_runtime_default(self):
        entrypoint = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn(
            'Transport : ${MCP_TRANSPORT:-streamable-http}',
            entrypoint,
        )


if __name__ == "__main__":
    unittest.main()
