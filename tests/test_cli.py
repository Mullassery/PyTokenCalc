"""Tests for `pytokencalc/cli.py`.

Previously had no dedicated test file (only `quick_cli`/`pycount` was
tested) -- ROADMAP_HONEST.md section 3. These cover both the `CLIInterface`
methods in-process and the `main()` argv dispatch (via a patched sys.argv
and captured stdout).
"""

import json

import pytest

from pytokencalc.cli import CLIInterface, main, print_help


@pytest.fixture
def cli():
    return CLIInterface()


class TestCLIInterface:
    def test_count_tokens_success(self, cli):
        result = cli.count_tokens("Tell me a story about a robot", "gpt-4o")
        assert result["status"] == "success"
        assert result["model"] == "gpt-4o"
        assert result["input_tokens"] > 0
        assert result["total_tokens"] >= result["input_tokens"]

    def test_count_tokens_error_returns_error_dict(self, cli):
        result = cli.count_tokens("hello", "definitely-not-a-model-xyz")
        assert result["status"] == "error"
        assert "message" in result
        assert result["model"] == "definitely-not-a-model-xyz"

    def test_list_providers(self, cli):
        result = cli.list_providers()
        assert result["status"] == "success"
        assert result["count"] == len(result["providers"])

    def test_list_models_all(self, cli):
        result = cli.list_models()
        assert result["status"] == "success"
        assert result["count"] == len(result["models"])

    def test_list_models_for_provider(self, cli):
        result = cli.list_models("openai")
        assert result["status"] == "success"
        assert result["provider"] == "openai"

    def test_cache_stats(self, cli):
        result = cli.get_cache_stats()
        assert result["status"] == "success"
        assert result["cached_counts"] == 0
        assert result["cache_hits"] == 0

    def test_clear_cache(self, cli):
        result = cli.clear_cache()
        assert result["status"] == "success"


class TestMainDispatch:
    def _run(self, monkeypatch, args):
        monkeypatch.setattr("sys.argv", args)
        main()

    def test_count_prints_success_json(self, monkeypatch, capsys):
        self._run(monkeypatch, ["pytokencalc", "count", "hello world", "gpt-4o"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "success"
        assert payload["input_tokens"] > 0

    def test_count_missing_args_exits(self, monkeypatch, capsys):
        with pytest.raises(SystemExit) as excinfo:
            self._run(monkeypatch, ["pytokencalc", "count", "hello"])
        assert excinfo.value.code == 1
        assert json.loads(capsys.readouterr().out)["error"]

    def test_no_args_prints_help_and_exits(self, monkeypatch, capsys):
        with pytest.raises(SystemExit) as excinfo:
            self._run(monkeypatch, ["pytokencalc"])
        assert excinfo.value.code == 1
        assert "USAGE" in capsys.readouterr().out

    def test_providers_prints_json(self, monkeypatch, capsys):
        self._run(monkeypatch, ["pytokencalc", "providers"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "success"

    def test_unknown_command_exits(self, monkeypatch, capsys):
        with pytest.raises(SystemExit) as excinfo:
            self._run(monkeypatch, ["pytokencalc", "bogus-command"])
        assert excinfo.value.code == 1
        assert json.loads(capsys.readouterr().out)["error"]

    def test_help_command(self, monkeypatch, capsys):
        # "help" prints usage and does not exit non-zero.
        self._run(monkeypatch, ["pytokencalc", "help"])
        assert "USAGE" in capsys.readouterr().out

    def test_models_with_provider(self, monkeypatch, capsys):
        self._run(monkeypatch, ["pytokencalc", "models", "openai"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "success"
        assert payload["provider"] == "openai"


def test_print_help_contains_commands(capsys):
    print_help()
    out = capsys.readouterr().out
    for command in ("count", "count-vision", "providers", "models", "help"):
        assert command in out
