import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_spectre():
    module_name = "spectre_execution_under_test"
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
                spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def completed(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class ExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spectre = load_spectre()

    def invoke_run(self, result, command="safe-command", timeout=17):
        with patch.object(self.spectre.subprocess, "run", return_value=result) as process:
            output = self.spectre.run(command, timeout=timeout)
        return output, process

    def invoke_run_argv(self, result, command=None, timeout=17):
        command = command or ["safe-command", "--flag"]
        with patch.object(self.spectre.subprocess, "run", return_value=result) as process:
            output = self.spectre.run_argv(command, timeout=timeout)
        return output, process

    def test_run_exit_zero_stdout_only(self):
        output, process = self.invoke_run(completed(stdout="out"))
        self.assertEqual(output, "out")
        process.assert_called_once_with(
            "safe-command",
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            timeout=17,
        )

    def test_run_exit_zero_stderr_only(self):
        output, _ = self.invoke_run(completed(stderr="err"))
        self.assertEqual(output, "[STDERR]\nerr")

    def test_run_exit_zero_stdout_and_stderr(self):
        output, _ = self.invoke_run(completed(stdout="out", stderr="err"))
        self.assertEqual(output, "out\n[STDERR]\nerr")

    def test_run_exit_zero_without_output(self):
        output, _ = self.invoke_run(completed())
        self.assertEqual(output, "(no output)")

    def test_run_exit_one_with_stdout(self):
        output, _ = self.invoke_run(completed(returncode=1, stdout="out"))
        self.assertEqual(output, "[EXIT 1]\nout")

    def test_run_exit_one_without_output(self):
        output, _ = self.invoke_run(completed(returncode=1))
        self.assertEqual(output, "[EXIT 1]")

    def test_run_arbitrary_nonzero_with_stderr(self):
        output, _ = self.invoke_run(completed(returncode=7, stderr="err"))
        self.assertEqual(output, "[EXIT 7]\n[STDERR]\nerr")

    def test_run_arbitrary_nonzero_with_stdout_and_stderr(self):
        output, _ = self.invoke_run(completed(returncode=7, stdout="out", stderr="err"))
        self.assertEqual(output, "[EXIT 7]\nout\n[STDERR]\nerr")

    def test_run_argv_exit_zero_and_preserved_mechanics(self):
        command = ["safe-command", "--flag"]
        output, process = self.invoke_run_argv(completed(stdout="out"), command)
        self.assertEqual(output, "out")
        process.assert_called_once_with(
            command,
            capture_output=True,
            text=True,
            timeout=17,
        )

    def test_run_argv_exit_one_is_visible(self):
        output, _ = self.invoke_run_argv(completed(returncode=1))
        self.assertEqual(output, "[EXIT 1]")

    def test_run_argv_exit_above_one_is_visible(self):
        output, _ = self.invoke_run_argv(completed(returncode=2))
        self.assertEqual(output, "[EXIT 2]")

    def test_run_argv_nonzero_stdout_is_retained(self):
        output, _ = self.invoke_run_argv(completed(returncode=3, stdout="out"))
        self.assertEqual(output, "[EXIT 3]\nout")

    def test_run_argv_nonzero_stderr_is_labeled(self):
        output, _ = self.invoke_run_argv(completed(returncode=4, stderr="err"))
        self.assertEqual(output, "[EXIT 4]\n[STDERR]\nerr")

    def test_run_argv_nonzero_without_output_is_not_no_output(self):
        output, _ = self.invoke_run_argv(completed(returncode=5))
        self.assertEqual(output, "[EXIT 5]")
        self.assertNotIn("(no output)", output)

    def test_run_timeout_marker_is_preserved(self):
        with patch.object(
            self.spectre.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("safe-command", 9),
        ):
            output = self.spectre.run("safe-command", timeout=9)
        self.assertEqual(output, "[TIMEOUT] 9s exceeded")

    def test_run_argv_missing_tool_marker_is_preserved(self):
        missing = FileNotFoundError(2, "No such file or directory", "missing-tool")
        with patch.object(self.spectre.subprocess, "run", side_effect=missing):
            output = self.spectre.run_argv(["missing-tool"])
        self.assertTrue(output.startswith("[ERROR] Tool not found: "))
        self.assertIn("missing-tool", output)

    def test_generic_execution_exception_marker_is_preserved(self):
        with patch.object(
            self.spectre.subprocess,
            "run",
            side_effect=RuntimeError("boom"),
        ):
            output = self.spectre.run("safe-command")
        self.assertEqual(output, "[ERROR] boom")

    def test_command_logging_masks_secret_shaped_values(self):
        with patch.object(
            self.spectre.subprocess,
            "run",
            return_value=completed(),
        ), patch.object(self.spectre.log, "info") as log_info:
            self.spectre.run("tool --api_key=supersecret123")
        logged_command = log_info.call_args.args[1]
        self.assertIn("supe***", logged_command)
        self.assertNotIn("supersecret123", logged_command)


if __name__ == "__main__":
    unittest.main()
