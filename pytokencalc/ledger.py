"""Optional JSONL usage ledger.

This is the local equivalent of OpenRouter's generation/usage audit trail:
append a reconciliation record after each request, then summarize spend and
token usage by model/provider. PyTokenCalc does not write anything unless you
construct a ledger and call ``record_*``.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional

from .reconcile import Reconciliation

DEFAULT_LEDGER_PATH = Path.home() / ".pytokencalc" / "usage.jsonl"


class UsageLedger:
    """Append-only JSONL ledger for reconciled usage/cost records."""

    def __init__(self, path: Optional[str] = None):
        self.path = Path(path).expanduser() if path else DEFAULT_LEDGER_PATH
        self._lock = threading.Lock()

    def _ensure_parent(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping")
        payload = dict(record)
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self._ensure_parent()
        line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return payload

    def record_reconciliation(
        self,
        reconciliation: Reconciliation,
        *,
        tags: Optional[Mapping[str, str]] = None,
        generation_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "model": reconciliation.model,
            "provider": reconciliation.provider,
            "generation_id": generation_id,
            "tags": dict(tags or {}),
            "usage": reconciliation.usage.to_dict(),
            "cost_usd": reconciliation.cost.total_usd,
            "provider_reported_cost_usd": reconciliation.provider_reported_cost_usd,
            "expected_cost_usd": reconciliation.expected_cost_usd,
            "delta_usd": reconciliation.delta_usd,
            "delta_percent": reconciliation.delta_percent,
        }
        return self.append(record)

    def records(self) -> Iterator[Dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{self.path}:{line_number}: invalid JSON: {exc.msg}"
                    ) from exc
                if not isinstance(record, dict):
                    raise ValueError(
                        f"{self.path}:{line_number}: record must be a JSON object"
                    )
                yield record

    def list_records(
        self,
        *,
        since: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        records = self._filtered_records(since)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            records = records[-limit:] if limit else []
        return records

    def _filtered_records(self, since: Optional[str]) -> List[Dict[str, Any]]:
        records = list(self.records())
        if since:
            cutoff = _parse_timestamp(since)
            filtered = []
            for record in records:
                timestamp = record.get("timestamp")
                if not isinstance(timestamp, str):
                    continue
                try:
                    if _parse_timestamp(timestamp) >= cutoff:
                        filtered.append(record)
                except ValueError:
                    continue
            return filtered
        return records

    def summary(self, *, since: Optional[str] = None) -> Dict[str, Any]:
        by_model: Dict[str, Dict[str, float]] = {}
        by_provider: Dict[str, Dict[str, float]] = {}
        totals = _empty_totals()

        for record in self._filtered_records(since):
            usage = record.get("usage")
            if not isinstance(usage, Mapping):
                continue
            cost = _float(record.get("cost_usd"))
            _add_usage(totals, usage, cost)

            model = str(record.get("model") or "unknown")
            provider = str(record.get("provider") or "unknown")
            _add_usage(by_model.setdefault(model, _empty_totals()), usage, cost)
            _add_usage(
                by_provider.setdefault(provider, _empty_totals()), usage, cost
            )

        return {
            "ledger": str(self.path),
            "since": since,
            "totals": totals,
            "by_model": by_model,
            "by_provider": by_provider,
        }

    def clear(self) -> None:
        self._ensure_parent()
        with self._lock:
            self.path.write_text("", encoding="utf-8")


def _parse_timestamp(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _empty_totals() -> Dict[str, float]:
    return {
        "records": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.0,
    }


def _add_usage(totals: Dict[str, float], usage: Mapping[str, Any], cost: float) -> None:
    totals["records"] += 1
    for key in (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
    ):
        value = usage.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        totals[key] += value
    totals["cost_usd"] += cost
