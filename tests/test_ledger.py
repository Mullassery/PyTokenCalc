"""Tests for the optional JSONL usage ledger."""

import json

import pytest

from pytokencalc.ledger import UsageLedger
from pytokencalc.reconcile import reconcile


def test_record_reconciliation_and_summarize(tmp_path):
    ledger = UsageLedger(str(tmp_path / "usage.jsonl"))
    result = reconcile(
        "gpt-4o",
        {"usage": {"prompt_tokens": 1_000, "completion_tokens": 500}},
        expected_cost_usd=0.001,
    )
    record = ledger.record_reconciliation(
        result,
        tags={"env": "test"},
        generation_id="gen-1",
        timestamp="2026-10-24T00:00:00+00:00",
    )
    assert record["generation_id"] == "gen-1"
    assert record["tags"] == {"env": "test"}

    summary = ledger.summary()
    assert summary["totals"]["records"] == 1
    assert summary["totals"]["input_tokens"] == 1_000
    assert summary["totals"]["output_tokens"] == 500
    assert summary["totals"]["cost_usd"] == pytest.approx(0.0075)
    assert summary["by_model"]["gpt-4o"]["cost_usd"] == pytest.approx(0.0075)
    assert summary["by_provider"]["unknown"]["records"] == 1


def test_list_records_limit_and_since(tmp_path):
    ledger = UsageLedger(str(tmp_path / "usage.jsonl"))
    ledger.append(
        {
            "timestamp": "2026-10-23T00:00:00+00:00",
            "model": "old",
            "usage": {"input_tokens": 1},
        }
    )
    ledger.append(
        {
            "timestamp": "2026-10-24T00:00:00+00:00",
            "model": "new",
            "usage": {"input_tokens": 2},
        }
    )
    assert len(ledger.list_records()) == 2
    assert len(ledger.list_records(limit=1)) == 1
    assert ledger.list_records(limit=1)[0]["model"] == "new"
    assert len(ledger.list_records(since="2026-10-24T00:00:00Z")) == 1
    assert ledger.summary(since="2026-10-24T00:00:00Z")["totals"]["input_tokens"] == 2


def test_clear(tmp_path):
    ledger = UsageLedger(str(tmp_path / "usage.jsonl"))
    ledger.append({"model": "x", "usage": {"input_tokens": 1}})
    ledger.clear()
    assert list(ledger.records()) == []


def test_malformed_record_reports_line(tmp_path):
    path = tmp_path / "usage.jsonl"
    path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")
    ledger = UsageLedger(str(path))
    with pytest.raises(ValueError, match=":2: invalid JSON"):
        list(ledger.records())


def test_ledger_file_is_jsonl(tmp_path):
    path = tmp_path / "usage.jsonl"
    ledger = UsageLedger(str(path))
    ledger.append({"model": "a", "usage": {"input_tokens": 1}})
    ledger.append({"model": "b", "usage": {"input_tokens": 2}})
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["model"] for line in lines] == ["a", "b"]
