# CLAUDE.md — Cost Guardian

This file provides guidance to Claude Code when working with this repository.

## What We're Building

**Cost Guardian** — Real-time cost optimizer for Claude Code. Answers: "Why does Claude cost so much, and what can I do about it?"

**Core insight:** Users can't optimize what they can't measure. We measure, then recommend optimizations.

---

## Architecture Overview

### Layer 1: Rust Core (`crates/beacon-core/`)
**High-performance cost tracking**

- `cost_tracker.rs` — Track every operation + calculate cost in real-time
- `pricing.rs` — Model pricing database (keeps Claude 3.5, Haiku, etc. prices)
- `analyzer.rs` — Cost trends, anomaly detection, pattern analysis
- `recommender.rs` — Model selector (use Haiku vs Sonnet), batch suggestions
- `caching.rs` — Detect repeated prompts (enable cache for 90% savings)
- `storage.rs` — SQLite backend (local, no cloud)

**Why Rust:**
- ✅ Performance-critical (every operation tracked = high volume)
- ✅ Memory-efficient (streaming ops, not buffering)
- ✅ Safe concurrency (handle multiple sessions)

### Layer 2: Python Wrapper (`python/src/`)
**Easy-to-use API**

- `__init__.py` — Main `CostGuardian` class
- `api.py` — REST API for dashboards/reports
- `cli.py` — Command-line interface
- `alerts.py` — Slack/webhook notifications

**Why Python:**
- ✅ Natural data science stack (pandas, matplotlib)
- ✅ Easy CLI (Click framework)
- ✅ Ecosystem integration (SQLAlchemy, FastAPI)

### Communication Flow

```
Claude Code operation
    ↓
CostGuardian tracks (Python API)
    ↓
Rust Core calculates cost (PyO3 FFI)
    ↓
SQLite stores operation + cost
    ↓
Python returns: breakdown, trends, recommendations
```

---

## Build & Development

### Install
```bash
make install      # Install deps + pre-commit hooks
```

### Build
```bash
make build        # Full Rust + Python build
make dev          # Dev install with hot reload (maturin)
```

### Test
```bash
make test         # All tests (Rust + Python)
make test-rust    # Rust only
make test-python  # Python only
```

### Format & Lint
```bash
make fmt          # Format code
make lint         # Lint Rust + Python
```

---

## Key Implementation Details

### Cost Tracking Pipeline

1. **Operation entry:** Every tool call (file_read, ai_call, git_op) is tracked
2. **Token counting:** Input + output tokens recorded
3. **Model lookup:** Get model pricing from database
4. **Cost calculation:** `(input_tokens * input_rate + output_tokens * output_rate) / 1M`
5. **Storage:** Save operation + cost to SQLite
6. **Aggregation:** Group by operation type, time period, model

### Real-time Attribution

Users get: "File reads = 60% of your tokens ($32.40 today)"

Instead of: "You spent $47 total" (not helpful)

### Model Pricing Database

Kept updated with:
- Claude 3.5 Sonnet: $3.00/$15.00 per 1M tokens
- Claude 3.5 Haiku: $0.80/$4.00 per 1M tokens  
- Claude 3 Opus: $15.00/$75.00 per 1M tokens

---

## Development Workflow

### Add a new operation type
1. Add to `beacon-core/src/cost_tracker.rs` → `OperationType` enum
2. Update `recommender.rs` with optimization hints
3. Update Python API in `python/src/__init__.py`
4. Test: `make test`

### Update pricing
1. Edit `crates/beacon-core/src/pricing.rs`
2. Run: `cargo build`
3. Pricing auto-reloaded next session

### Add recommendation
1. Implement in `crates/beacon-core/src/recommender.rs`
2. Expose in Python via `python/src/api.py`
3. Test with `pytest tests/`

---

## Common Tasks

**Track new operation:**
```rust
// In Rust:
let cost = tracker.track_operation(OperationCost {
    operation: OperationType::FileRead,
    tokens_input: 450,
    tokens_output: 120,
    model: "claude-3-5-sonnet",
    cost_usd: 0.0145,
    timestamp: now(),
})?;
```

**Get daily breakdown:**
```python
# In Python:
breakdown = guardian.get_cost_breakdown(period="today")
# Returns: {"file_read": 32.40, "ai_call": 15.20, ...}
```

**Detect caching opportunities:**
```python
# In Python:
opps = guardian.detect_caching_opportunities()
# Returns: [{"prompt": "...", "occurrences": 12, "savings": 2.10}]
```

---

## Testing Strategy

**Unit tests:**
```bash
cargo test -p beacon-core          # Rust tests
pytest tests/ -v                   # Python tests
```

**Integration tests:**
```bash
pytest tests/integration/          # End-to-end
```

**Manual testing:**
```bash
# 1. Start tracking
cost-guardian serve

# 2. Perform operations
# 3. Check breakdown
cost-guardian breakdown --period today
```

---

## Performance Targets

- Cost calculation: <1ms per operation
- Daily breakdown query: <5ms
- Trend analysis: <10ms
- Model selector decision: <50ms

All critical for real-time feedback.

---

## Important Constraints

1. **Pricing accuracy:** Must stay in sync with Anthropic pricing
2. **Real-time performance:** Cost calc must not block user
3. **Privacy:** All data stays local (SQLite, no cloud)
4. **Accuracy:** Token counting MUST match Claude's actual usage

---

## Future Phases

- Phase 2: Model selector + prompt caching detector
- Phase 3: Auto-optimization + Slack alerts
- Phase 4: Team dashboards + compliance reporting

---

## References

- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [Claude Code Integration Guide](https://docs.anthropic.com/en/docs/about-claude/tool-use)
- [MCP Protocol](https://modelcontextprotocol.io/)
