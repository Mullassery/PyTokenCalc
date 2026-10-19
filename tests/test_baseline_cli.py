"""CLI tests for the OKF baseline save/list/compare/from-jsonl commands."""

import json

import pytest

from pytokencalc.cli import main


def _run(monkeypatch, args):
    monkeypatch.setattr("sys.argv", ["pytokencalc", *args])
    main()


def _payload(capsys):
    return json.loads(capsys.readouterr().out)


def _write_json(path, payload):
    path.write_text(json.dumps(payload))


def _write_jsonl(path, samples):
    path.write_text("\n".join(json.dumps(sample) for sample in samples) + "\n")


def _samples():
    return [
        {"input_tokens": 100, "output_tokens": 50},
        {"input_tokens": 120, "output_tokens": 60},
        {"input_tokens": 140, "output_tokens": 80},
    ]


def test_baseline_save_from_json_array(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    _write_json(source, _samples())

    _run(
        monkeypatch,
        [
            "baseline",
            "save",
            "--samples",
            str(source),
            "--provider",
            "openai",
            "--model",
            "gpt-4o",
            "--task-type",
            "chat",
            "--baseline-dir",
            str(tmp_path),
        ],
    )

    payload = _payload(capsys)
    assert payload["status"] == "success"
    assert payload["baseline"] == {
        "provider": "openai",
        "model": "gpt-4o",
        "task_type": "chat",
        "avg_input_tokens": 120,
        "avg_output_tokens": 63,
        "samples": 3,
        "percentile_95_input": 140,
        "percentile_95_output": 80,
    }
    assert (tmp_path / "openai_gpt-4o_chat.json").exists()


def test_baseline_save_reads_metadata_from_object(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    _write_json(
        source,
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "task_type": "completion",
            "samples": _samples(),
        },
    )

    _run(
        monkeypatch,
        ["baseline", "save", str(source), "--baseline-dir", str(tmp_path)],
    )

    assert _payload(capsys)["baseline"]["model"] == "gpt-4o-mini"


def test_baseline_list_and_compare(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    _write_json(source, _samples())
    for model in ("gpt-4o", "gpt-4o-mini"):
        _run(
            monkeypatch,
            [
                "baseline",
                "save",
                str(source),
                "--provider",
                "openai",
                "--model",
                model,
                "--task-type",
                "chat",
                "--baseline-dir",
                str(tmp_path),
            ],
        )
    capsys.readouterr()

    _run(
        monkeypatch,
        ["baseline", "list", "--provider", "openai", "--baseline-dir", str(tmp_path)],
    )
    listing = _payload(capsys)
    assert listing["status"] == "success"
    assert listing["count"] == 2
    assert {item["model"] for item in listing["baselines"]} == {
        "gpt-4o",
        "gpt-4o-mini",
    }

    _run(
        monkeypatch,
        [
            "baseline",
            "compare",
            "--provider",
            "openai",
            "--task-type",
            "chat",
            "--baseline-dir",
            str(tmp_path),
        ],
    )
    comparison = _payload(capsys)
    assert comparison["count"] == 2
    assert comparison["models"]["gpt-4o"]["p95_output_tokens"] == 80
    assert comparison["models"]["gpt-4o"]["p95_total_tokens"] == 220


def test_baseline_list_empty_dir(monkeypatch, capsys, tmp_path):
    _run(
        monkeypatch,
        ["baseline", "list", "--baseline-dir", str(tmp_path / "missing")],
    )

    payload = _payload(capsys)
    assert payload["status"] == "success"
    assert payload["count"] == 0
    assert payload["baselines"] == []


def test_baseline_from_jsonl_counts_prompts(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.jsonl"
    _write_jsonl(
        source,
        [
            {"prompt": "hello world", "output_tokens": 5},
            {"prompt": "hello there, world", "output_tokens": 7},
        ],
    )

    _run(
        monkeypatch,
        [
            "baseline",
            "from-jsonl",
            str(source),
            "--provider",
            "openai",
            "--model",
            "gpt-4o",
            "--task-type",
            "chat",
            "--baseline-dir",
            str(tmp_path),
        ],
    )

    payload = _payload(capsys)
    assert payload["status"] == "success"
    assert payload["baseline"]["samples"] == 2
    assert payload["baseline"]["avg_input_tokens"] > 0
    assert payload["baseline"]["percentile_95_output"] == 7


def test_baseline_from_jsonl_skips_blank_lines(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.jsonl"
    source.write_text(
        '\n{"input_tokens": 10, "output_tokens": 3}\n\n{"input_tokens": 20, "output_tokens": 4}\n\n'
    )

    _run(
        monkeypatch,
        [
            "baseline",
            "from-jsonl",
            str(source),
            "--provider",
            "openai",
            "--model",
            "gpt-4o",
            "--task-type",
            "chat",
            "--baseline-dir",
            str(tmp_path),
        ],
    )

    assert _payload(capsys)["baseline"]["samples"] == 2


def test_baseline_from_jsonl_empty_file_exits(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.jsonl"
    source.write_text("\n\n")

    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            [
                "baseline",
                "from-jsonl",
                str(source),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--task-type",
                "chat",
                "--baseline-dir",
                str(tmp_path),
            ],
        )

    assert excinfo.value.code == 1
    assert "at least one sample" in _payload(capsys)["error"]


def test_baseline_from_jsonl_malformed_line_exits(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.jsonl"
    source.write_text('{"input_tokens": 10, "output_tokens": 3}\n{not json}\n')

    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            [
                "baseline",
                "from-jsonl",
                str(source),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--task-type",
                "chat",
                "--baseline-dir",
                str(tmp_path),
            ],
        )

    assert excinfo.value.code == 1
    error = _payload(capsys)["error"]
    assert ":2:" in error
    assert "invalid JSON" in error


def test_baseline_save_malformed_json_exits(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    source.write_text("{not json")

    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            [
                "baseline",
                "save",
                str(source),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--task-type",
                "chat",
                "--baseline-dir",
                str(tmp_path),
            ],
        )

    assert excinfo.value.code == 1
    assert _payload(capsys)["error"]


def test_baseline_missing_samples_file_exits(monkeypatch, capsys, tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            [
                "baseline",
                "from-jsonl",
                str(tmp_path / "nope.jsonl"),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--task-type",
                "chat",
            ],
        )

    assert excinfo.value.code == 1
    assert "not found" in _payload(capsys)["error"]


def test_baseline_missing_required_option_exits(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    _write_json(source, _samples())

    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            ["baseline", "save", str(source), "--provider", "openai"],
        )

    assert excinfo.value.code == 1
    assert "--model is required" in _payload(capsys)["error"]


def test_baseline_unknown_subcommand_exits(monkeypatch, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _run(monkeypatch, ["baseline", "bogus"])

    assert excinfo.value.code == 1
    assert "Unknown baseline subcommand" in _payload(capsys)["error"]


def test_baseline_list_malformed_store_exits(monkeypatch, capsys, tmp_path):
    (tmp_path / "openai_gpt-4o_chat.json").write_text("{not json")

    with pytest.raises(SystemExit) as excinfo:
        _run(monkeypatch, ["baseline", "list", "--baseline-dir", str(tmp_path)])

    assert excinfo.value.code == 1
    assert _payload(capsys)["error"]


def test_baseline_save_empty_samples_exits(monkeypatch, capsys, tmp_path):
    source = tmp_path / "samples.json"
    _write_json(source, [])

    with pytest.raises(SystemExit) as excinfo:
        _run(
            monkeypatch,
            [
                "baseline",
                "save",
                str(source),
                "--provider",
                "openai",
                "--model",
                "gpt-4o",
                "--task-type",
                "chat",
                "--baseline-dir",
                str(tmp_path),
            ],
        )

    assert excinfo.value.code == 1
    assert "at least one sample" in _payload(capsys)["error"]
