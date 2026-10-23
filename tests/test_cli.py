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


    def test_catalog_prints_models(self, monkeypatch, capsys):
        self._run(monkeypatch, ["pytokencalc", "catalog", "openai"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["count"] > 0
        assert all(model["provider"] == "openai" for model in payload["models"])

    def test_catalog_import_command(self, monkeypatch, capsys, tmp_path):
        source = tmp_path / "models.json"
        source.write_text(
            '{"data": [{"id": "testvendor/cli-model",'
            ' "pricing": {"prompt": "0.000001", "completion": "0.000002"}}]}',
            encoding="utf-8",
        )
        self._run(
            monkeypatch,
            ["pytokencalc", "catalog", "import", "--file", str(source)],
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["imported"] == 1
        assert payload["pricing_imported"] == 1

    def test_model_info_prints_metadata(self, monkeypatch, capsys):
        self._run(monkeypatch, ["pytokencalc", "model-info", "gpt-4o"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["id"] == "gpt-4o"
        assert payload["context_length"] == 128_000

    def test_preflight_command(self, monkeypatch, capsys, tmp_path):
        request = tmp_path / "request.json"
        request.write_text(
            '{"messages": [{"role": "user", "content": "Hello world"}]}',
            encoding="utf-8",
        )
        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "preflight",
                "--file",
                str(request),
                "--model",
                "gpt-4o",
                "--max-output",
                "100",
            ],
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["input_tokens"] > 0
        assert payload["fits"] is True

    def test_endpoints_import_list_and_compare(self, monkeypatch, capsys, tmp_path):
        source = tmp_path / "endpoints.json"
        source.write_text(
            json.dumps(
                {
                    "data": {
                        "id": "testvendor/cli-endpoint-model",
                        "endpoints": [
                            {
                                "provider_name": "provider-a",
                                "pricing": {
                                    "prompt": "0.000001",
                                    "completion": "0.000002",
                                },
                            },
                            {
                                "provider_name": "provider-b",
                                "pricing": {
                                    "prompt": "0.000003",
                                    "completion": "0.000006",
                                },
                            },
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        self._run(
            monkeypatch,
            ["pytokencalc", "endpoints", "import", "--file", str(source)],
        )
        imported = json.loads(capsys.readouterr().out)
        assert imported["imported"] == 2

        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "endpoints",
                "list",
                "--model",
                "testvendor/cli-endpoint-model",
            ],
        )
        listed = json.loads(capsys.readouterr().out)
        assert listed["count"] == 2

        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "endpoints",
                "compare",
                "--model",
                "testvendor/cli-endpoint-model",
                "--input-tokens",
                "1000",
                "--output-tokens",
                "500",
            ],
        )
        compared = json.loads(capsys.readouterr().out)
        assert compared["cheapest_provider"] == "provider-a"

    def test_compare_command(self, monkeypatch, capsys):
        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "compare",
                "--models",
                "gpt-4o,gpt-4o-mini",
                "--input-tokens",
                "1000",
                "--output-tokens",
                "500",
            ],
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["cheapest_model"] == "gpt-4o-mini"
        assert payload["comparisons"][0]["model"] == "gpt-4o-mini"

    def test_usage_add_and_report_commands(self, monkeypatch, capsys, tmp_path):
        response = tmp_path / "response.json"
        response.write_text(
            '{"usage": {"prompt_tokens": 100, "completion_tokens": 20}}',
            encoding="utf-8",
        )
        ledger = tmp_path / "usage.jsonl"
        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "usage",
                "add",
                "--file",
                str(response),
                "--model",
                "gpt-4o",
                "--ledger",
                str(ledger),
                "--tags",
                "env=test",
                "--generation-id",
                "gen-1",
            ],
        )
        added = json.loads(capsys.readouterr().out)
        assert added["record"]["generation_id"] == "gen-1"
        assert added["record"]["tags"] == {"env": "test"}

        self._run(
            monkeypatch,
            ["pytokencalc", "usage", "report", "--ledger", str(ledger)],
        )
        report = json.loads(capsys.readouterr().out)
        assert report["totals"]["records"] == 1
        assert report["totals"]["input_tokens"] == 100

    def test_reconcile_command(self, monkeypatch, capsys, tmp_path):
        response = tmp_path / "response.json"
        response.write_text(
            '{"usage": {"prompt_tokens": 100, "completion_tokens": 20}}',
            encoding="utf-8",
        )
        self._run(
            monkeypatch,
            [
                "pytokencalc",
                "reconcile",
                "--file",
                str(response),
                "--model",
                "gpt-4o",
                "--expected-cost",
                "0.001",
            ],
        )
        payload = json.loads(capsys.readouterr().out)
        assert payload["usage"]["input_tokens"] == 100
        assert payload["delta_usd"] is not None


def test_print_help_contains_commands(capsys):
    print_help()
    out = capsys.readouterr().out
    for command in (
        "count",
        "count-vision",
        "providers",
        "models",
        "catalog",
        "model-info",
        "preflight",
        "reconcile",
        "help",
    ):
        assert command in out
