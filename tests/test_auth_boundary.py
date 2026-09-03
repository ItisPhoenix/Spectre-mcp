import importlib.util
import inspect
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_spectre():
    source = ROOT / "spectre.py"
    spec = importlib.util.spec_from_file_location("spectre_under_test", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    real_makedirs = os.makedirs

    def ignore_output_dir(path, *args, **kwargs):
        if path == "/tmp/spectre":
            return None
        return real_makedirs(path, *args, **kwargs)

    try:
        with patch.object(os, "makedirs", side_effect=ignore_output_dir):
            with patch.dict(os.environ, {"SPECTRE_API_KEY": ""}):
                spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


class AuthBoundaryTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.spectre = load_spectre()

    async def invoke(self, api_key, headers=(), scope_type="http", path="/mcp"):
        downstream_scopes = []
        sent = []

        async def downstream(scope, receive, send):
            downstream_scopes.append(scope["type"])
            if scope["type"] == "lifespan":
                await send({"type": "lifespan.startup.complete"})
                return
            await send({
                "type": "http.response.start",
                "status": 204,
                "headers": [],
            })
            await send({"type": "http.response.body", "body": b""})

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        scope = {"type": scope_type}
        if scope_type == "http":
            scope.update({"path": path, "headers": list(headers)})
        app = self.spectre._ASGIBearerAuth(downstream, api_key)
        await app(scope, receive, send)
        return sent, downstream_scopes

    async def test_key_unset_passes_through(self):
        sent, downstream = await self.invoke("")
        self.assertEqual(downstream, ["http"])
        self.assertEqual(sent[0]["status"], 204)

    async def test_missing_key_is_rejected(self):
        sent, downstream = await self.invoke("test-secret-123")
        self.assertEqual(downstream, [])
        self.assertEqual(sent[0]["status"], 401)
        self.assertNotIn(b"test-secret-123", sent[1]["body"])

    async def test_wrong_bearer_is_rejected(self):
        sent, downstream = await self.invoke(
            "test-secret-123",
            [(b"authorization", b"Bearer wrong-secret")],
        )
        self.assertEqual(downstream, [])
        self.assertEqual(sent[0]["status"], 401)

    async def test_correct_bearer_passes(self):
        sent, downstream = await self.invoke(
            "test-secret-123",
            [(b"authorization", b"Bearer test-secret-123")],
        )
        self.assertEqual(downstream, ["http"])
        self.assertEqual(sent[0]["status"], 204)

    async def test_correct_x_api_key_passes(self):
        sent, downstream = await self.invoke(
            "test-secret-123",
            [(b"x-api-key", b"test-secret-123")],
        )
        self.assertEqual(downstream, ["http"])
        self.assertEqual(sent[0]["status"], 204)

    async def test_lifespan_scope_passes_through(self):
        sent, downstream = await self.invoke("test-secret-123", scope_type="lifespan")
        self.assertEqual(downstream, ["lifespan"])
        self.assertEqual(sent[0]["type"], "lifespan.startup.complete")

    def test_auth_uses_constant_time_comparison(self):
        source = inspect.getsource(self.spectre._ASGIBearerAuth)
        self.assertIn("hmac.compare_digest", source)
        self.assertNotIn("auth !=", source)
        self.assertNotIn("xkey !=", source)


if __name__ == "__main__":
    unittest.main()
