import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_spectre():
    module_name = "spectre_composite_under_test"
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


class CompositeCorrectnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spectre = load_spectre()

    def run_domain_profile(self, ip_result):
        ip_command = "dig example.test A +short | head -1"
        calls = []

        def fake_run(command, timeout=600):
            calls.append(command)
            return ip_result if command == ip_command else "placeholder"

        with patch.object(self.spectre, "run", side_effect=fake_run):
            report = self.spectre.full_domain_profile("example.test")
        return report, calls

    def test_full_person_profile_without_identifiers_returns_error(self):
        self.assertEqual(
            self.spectre.full_person_profile(),
            "[ERROR] Provide at least one of: name, email, username, phone",
        )

    def test_full_person_profile_name_path_no_longer_raises(self):
        with patch.object(self.spectre, "run", return_value="mocked"):
            report = self.spectre.full_person_profile(name="Jane Doe")
        self.assertIn("PERSON PROFILE COMPLETE", report)

    def test_full_person_profile_name_query_is_url_encoded(self):
        calls = []

        def fake_run(command, timeout=600):
            calls.append(command)
            return "mocked"

        with patch.object(self.spectre, "run", side_effect=fake_run):
            self.spectre.full_person_profile(name="Jane Doe")
        google_command = next(command for command in calls if "google.com/search" in command)
        self.assertIn("Jane%20Doe", google_command)

    def test_full_person_profile_name_path_uses_mocked_run(self):
        with patch.object(self.spectre, "run", return_value="mocked") as run:
            self.spectre.full_person_profile(name="Jane Doe")
        run.assert_called_once()

    def test_full_domain_profile_uses_valid_ipv4_for_ipinfo(self):
        _, calls = self.run_domain_profile("203.0.113.10")
        self.assertIn(
            "curl -s 'https://ipinfo.io/203.0.113.10/json' | python3 -m json.tool",
            calls,
        )

    def test_full_domain_profile_uses_valid_ipv4_for_internetdb(self):
        _, calls = self.run_domain_profile("203.0.113.10")
        self.assertIn(
            "curl -s 'https://internetdb.shodan.io/203.0.113.10' | python3 -m json.tool",
            calls,
        )

    def test_full_domain_profile_rejects_exit_marker(self):
        report, calls = self.run_domain_profile("[EXIT 1]")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_rejects_exit_marker_with_stderr(self):
        report, calls = self.run_domain_profile("[EXIT 1]\n[STDERR]\nfailed")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_rejects_no_output_marker(self):
        report, calls = self.run_domain_profile("(no output)")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_rejects_stderr_only_result(self):
        report, calls = self.run_domain_profile("[STDERR]\nfailed")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_rejects_malformed_ipv4(self):
        report, calls = self.run_domain_profile("999.999.999.999")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_rejects_ipv6_for_a_record(self):
        report, calls = self.run_domain_profile("2001:db8::10")
        self.assertIn("(could not resolve IP)", report)
        self.assertFalse(any("ipinfo.io" in command for command in calls))

    def test_full_domain_profile_reports_resolution_failure(self):
        report, _ = self.run_domain_profile("[EXIT 1]")
        self.assertIn("(could not resolve IP)", report)

    def test_full_domain_profile_skips_threat_intelligence_without_valid_ipv4(self):
        report, calls = self.run_domain_profile("[EXIT 1]")
        self.assertIn("(skipped — no valid IPv4)", report)
        self.assertFalse(any("internetdb.shodan.io" in command for command in calls))

    def test_mimikatz_unavailable_returns_existing_fallback(self):
        with patch.object(self.spectre, "_which", return_value=False):
            result = self.spectre.mimikatz_run()
        self.assertEqual(
            result,
            "[INFO] mimikatz not installed natively. Use msfconsole_run with: load kiwi; creds_all",
        )

    def test_mimikatz_unavailable_does_not_attempt_execution(self):
        with patch.object(self.spectre, "_which", return_value=False), patch.object(
            self.spectre, "run_argv"
        ) as run_argv:
            self.spectre.mimikatz_run()
        run_argv.assert_not_called()

    def test_mimikatz_available_invokes_existing_command(self):
        with patch.object(self.spectre, "_which", return_value=True), patch.object(
            self.spectre, "run_argv", return_value="ok"
        ) as run_argv:
            result = self.spectre.mimikatz_run()
        self.assertEqual(result, "ok")
        run_argv.assert_called_once_with(
            ["mimikatz", "sekurlsa::logonpasswords", "exit"],
            timeout=60,
        )

    def test_mimikatz_available_path_preserves_timeout(self):
        with patch.object(self.spectre, "_which", return_value=True), patch.object(
            self.spectre, "run_argv", return_value="ok"
        ) as run_argv:
            self.spectre.mimikatz_run()
        self.assertEqual(run_argv.call_args.kwargs["timeout"], 60)

    def test_mimikatz_command_preserves_sanitization(self):
        with patch.object(self.spectre, "_which", return_value=True), patch.object(
            self.spectre, "run_argv", return_value="ok"
        ) as run_argv:
            self.spectre.mimikatz_run("foo;bar")
        command = run_argv.call_args.args[0]
        self.assertNotIn(";", command[1])
        self.assertEqual(command[1], "foobar")


if __name__ == "__main__":
    unittest.main()
