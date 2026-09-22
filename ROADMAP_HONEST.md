# Honest Status & Roadmap

This replaces `docs/ROADMAP.md` and `docs/PRODUCT_VISION.md`, which were
deleted in this pass. Those two files described a fictional "MCP 2.0
Platform" (19 projects, 228 tools, a "Product Team" and "Platform Lead",
port assignments, SaaS/multi-tenancy phases) that has no relationship to
what actually exists in this repository: a single-maintainer, pure-Python
token-counting library. They were fabricated planning docs, not a
description of reality, and were deleted rather than "archived" because
nothing in them is true of this project.

Last verified: 2026-09 (Sonnet 5, doing an OSS-standardization pass).
Repo: `/Users/georgimullassery/PyTokenCalc`, package version 1.2.0.

## 1. What's shipped and verified working

- **`count_tokens()` / `estimate_cost()` top-level API** (`pytokencalc/api.py`,
  `pytokencalc/pricing.py`) — manually re-run in this pass:
  `count_tokens("Tell me a story about a robot", model="gpt-4o")` → `7`,
  `estimate_cost("gpt-4o", input_tokens=7)` → `1.75e-05`. Matches the
  README's own example. This has **no dedicated test file** (see gap below)
  but works as documented when exercised directly.
- **OpenAI/Azure tokenization via `tiktoken`** — works and is fast once
  tiktoken's encoding files are cached locally. See the critical bug below
  for what happens when they aren't.
- **CLI entry points** (`pytokencalc`, `pycount`) — real, registered in
  `pyproject.toml [project.scripts]`, present and importable.
- **REST server** (`pytokencalc/server.py`) — binds `127.0.0.1:8005` by
  default, no built-in auth; this matches what SECURITY.md and README both
  say. Not covered by any test.
- **Custom/BYOM provider registration, Ollama, local-inference counters**
  — real HTTP-based implementations with short (1-2s) timeouts on their
  local network calls, which is the correct pattern (contrast with the
  HuggingFace path below, which has none).
- **Streaming/incremental counting and tiktoken encoding-drift detection**
  — real logic exists (`tokenizers/streaming.py`,
  `tokenizers/encoding_fingerprint.py`) with dedicated tests
  (`tests/test_streaming.py`, `tests/test_encoding_drift.py`); could not be
  independently exercised in this pass because both depend on
  `TokenCounterRegistry()` construction, which hit the bug below in this
  sandbox.

## 2. Critical bug found in this pass — FIXED 2026-09-22

**A network hiccup loading tiktoken's OpenAI encodings takes down the
*entire* token-counter registry, including providers that have nothing to
do with OpenAI.**

> **Fixed** in a follow-up quick-fix pass (2026-09-22): every per-provider
> `try/except` in `TokenCounterRegistry._register_default_counters`
> (`pytokencalc/tokenizers/registry.py`) now catches `Exception` instead of
> just `ImportError`, so one provider's constructor blowing up (tiktoken
> network failure, or anything else) only skips that provider instead of
> crashing the whole registry. Regression tests in
> `tests/test_registry_resilience.py` simulate a failing constructor
> (`RuntimeError`, `OSError`) and confirm the registry still constructs and
> still serves the other providers. Full suite went from 53 passed/47
> failed (baseline, degraded network) to 156 passed/0 failed/26 skipped in
> this environment. The description below is kept as-written for the
> historical record of what was found.

- `pytokencalc/tokenizers/openai_counter.py:49-66`: `OpenAITokenCounter.__init__`
  eagerly calls `_load_default_encodings()`, which downloads both
  `cl100k_base` and `o200k_base` via `tiktoken.get_encoding(...)`. If that
  network call fails for any reason, line 66 raises `RuntimeError(f"Failed
  to load tiktoken encodings: {e}")`.
- `pytokencalc/tokenizers/registry.py:36-40`: `TokenCounterRegistry.
  _register_default_counters` wraps the `OpenAITokenCounter()`
  construction in `try/except ImportError` — **not** `RuntimeError`. The
  `RuntimeError` from above is not caught. It propagates out of
  `TokenCounterRegistry.__init__`, so **the registry itself never gets
  constructed**, which means Anthropic/Google/Cohere/HuggingFace/Ollama/
  Azure/custom-provider counting all become unreachable too — not just
  OpenAI/tiktoken counting.
- **Reproduced live**: a `pytest tests/ -q` run in this sandbox (no cached
  tiktoken files, degraded network) hit exactly this — 47 of 100 tests
  failed, the overwhelming majority with the identical traceback rooted at
  `openai_counter.py:66`, cascading through `registry.py:37`, taking down
  unrelated test suites (`test_new_providers.py`'s Anthropic/Google/Cohere/
  Azure tests, `test_quick_cli.py`'s subprocess-based CLI tests,
  `test_streaming.py`, `test_encoding_drift.py`,
  `test_statguardian_integration.py`). Full run took 1h00m08s
  (3608.75s) because each affected `TokenCounterRegistry()` construction
  blocks for the OS-level TCP connect timeout (~60-75s observed here, not
  an instant failure) before raising.
- On a second, unrelated run minutes later on the same machine, the exact
  same `count_tokens()` call succeeded — consistent with an intermittent/
  throttled path to `openaipublic.blob.core.windows.net` rather than a
  hard network block. That intermittency is exactly the failure mode that
  will bite real users occasionally (flaky corporate proxy, first cold
  start in a `--network=none` Docker build stage, an airgapped CI runner)
  and be hard to reproduce/diagnose from a bug report, because it
  "usually works."
- **Fix shape** (not implemented here — needs a dedicated session):
  (a) catch `Exception` broadly (or specifically `RuntimeError` +
  `ImportError`) around each per-provider registration in `registry.py`,
  and/or (b) make `OpenAITokenCounter` lazy-load encodings on first
  `count()` call instead of eagerly in `__init__`, so a tiktoken network
  failure only breaks OpenAI/Azure counting, not the whole registry.

## 3. Test coverage gaps (concrete, by file)

- **No test file at all** for: `pytokencalc/api.py` (the `count_tokens`/
  `estimate_cost` top-level functions — the exact functions in the
  README's headline example), `pytokencalc/pricing.py` /
  `PRICING_TABLE` (the cost-estimation feature this library leads with),
  `pytokencalc/server.py` (REST server), `pytokencalc/cli.py` (the full
  `pytokencalc` CLI — only `quick_cli`/`pycount` has tests),
  `pytokencalc/okf_token_baselines.py`, `pytokencalc/_mcp_connector.py`,
  `pytokencalc/_mcp_tools.py`.
- `tests/test_accuracy_verification.py:1045` calls
  `AutoTokenizer.from_pretrained("tiiuae/falcon-7b")` with no timeout and
  no offline guard — a real network download of a 7B-parameter model's
  tokenizer files on every uncached run. This test is wrapped in a broad
  `except Exception: pytest.skip(...)`, so it doesn't fail outright, but
  it can block for the full connection-timeout duration first. Same
  pattern (no timeout on `AutoTokenizer.from_pretrained`) exists in
  production code, not just the test, at
  `pytokencalc/tokenizers/huggingface_counter.py:71` and
  `pytokencalc/tokenizers/opensource_counter.py:102` — any call to
  `count_tokens(text, model=<huggingface-or-fallback-model>)` for a model
  ID not already cached locally has no bound on how long it can block.
- `pytokencalc/statguardian_integration.py` and
  `pytokencalc/okf_token_baselines.py` implement real logic but are not
  called anywhere inside `count_tokens()`/`estimate_cost()` — they are
  separate, opt-in APIs most users of the headline API will never touch,
  and would not notice if they silently broke.

## 4. Dead / experimental code that should not be presented as shipped

- **MCP subsystem** (`pytokencalc/_mcp_connector.py`, `_mcp_tools.py`,
  exported at the top level as `pytokencalc.TokenCalculator`) — zero test
  coverage, zero mention in README.md or docs/API.md, and its real
  connector path shells out to an undocumented external `dab` binary that
  is not a declared dependency of this package. `examples/mcp_pytokencalc.py`
  exists and imports/calls it, but nobody has verified it works end-to-end
  outside whatever internal environment originally had `dab` installed.
  Recommendation: either write tests + docs for it, or remove it from the
  public `__all__` and stop shipping the example.
- **`docs/conf.py` + `docs/index.rst`** (removed in this pass) — a Sphinx
  scaffold whose `toctree` pointed at files that never existed
  (`user_guide/getting_started`, `api/core`, `providers/anthropic`, etc.),
  version pinned to a stale `0.8.0`, not wired into CI or Read the Docs.
  Running `sphinx-build` against it would have failed immediately. Deleted
  rather than fixed, since the project's real docs are the flat `.md`
  files in `docs/` and top-level, which is what README.md actually links
  to.
- **`docs/PRODUCT_VISION.md`, `docs/ROADMAP.md`** (removed in this pass) —
  see the note at the top of this file.
- **`docs/CONTRIBUTING.md`** (removed in this pass) — a second,
  contradictory CONTRIBUTING guide that duplicated the top-level
  `CONTRIBUTING.md` and actively conflicted with it: it listed "Cost
  calculation features" and "Financial/pricing data" as explicitly
  **out of scope** ("PyTokenCalc is PURELY a token counting library"),
  while the actual v1.1.0+ product's headline feature is
  `estimate_cost()` backed by a real pricing table. It also claimed "17
  tests, all passing" and "Zero External Dependencies: Only pydantic
  required" — both stale/false (there are 8 test files covering far more
  than 17 cases, most currently failing for the reason in section 2; see
  section 5 for the pydantic claim).

## 5. Other technical debt (concrete, by file:line)

- ~~**`pyproject.toml`**: `dependencies = ["pydantic>=2.0"]`~~ **Fixed
  2026-09-22**: confirmed zero usages anywhere in `pytokencalc/`, removed
  from `pyproject.toml` (`dependencies = []`) and
  `requirements-lock.txt`. Verified `pytokencalc` still imports and
  `count_tokens()`/`estimate_cost()` still work with pydantic absent.
- ~~**`pytokencalc/pricing.py:22`**: `PRICING_LAST_UPDATED = "2025-06"`~~
  **Partially addressed 2026-09-22**: spot-checked the table's existing
  entries (gpt-4o, claude-3-5-sonnet, etc.) against current OpenAI/
  Anthropic pricing pages -- still accurate for those specific model IDs
  (both providers kept legacy models at original pricing) -- and bumped
  the marker to `"2026-09"` with a note clarifying it verifies the
  *existing* rows, not full coverage. The table is still missing
  current-generation model families that launched since 2025-06 (GPT-4.1/
  GPT-5-era, Claude 4-era, etc.) -- adding those is real data-entry work,
  left for a follow-up.
- **Lint is not enforced anywhere.** `.github/workflows/ci.yml` only runs
  `pytest`; it never runs `ruff`, `black --check`, or `mypy`, despite all
  three being configured in `.pre-commit-config.yaml` and `pyproject.toml`.
  Running `ruff check pytokencalc/` in this pass surfaced **291 findings**
  (44 auto-fixable) against ruff's current default rule set — this
  project's `[tool.ruff]` config only sets `line-length`/`target-version`
  and has never curated a rule selection, so it's accumulated ruff's
  growing default rules unchecked. Not fixed here (291 findings is a real
  cleanup task, not a typo fix) — flagged for a dedicated lint-debt
  session, including deciding on an intentional `select =` in
  `[tool.ruff]` instead of the implicit default. **Update 2026-09-22**:
  now 299 findings after the registry crash fix (section 2) — the +8 are
  `BLE001` ("do not catch blind exception") on the 8 new
  `except Exception` clauses in `registry.py`, which is the intentional,
  correct tradeoff for provider-registration isolation. Still not fixed
  as part of this quick-fix pass; still needs the dedicated lint-debt
  session.
- **`.pre-commit-config.yaml`'s bandit hook referenced a `.bandit` config
  file that did not exist** (`args: ["-c", ".bandit"]`), which meant the
  bandit hook would fail outright for anyone running `pre-commit run
  --all-files` or committing with hooks enabled. Fixed in this pass by
  adding a minimal `.bandit` at the repo root.
- **`Makefile` was copy-pasted from an unrelated Rust/maturin project**
  ("ClaudeBeacon") — `make build`/`make test`/`make lint` invoked `cargo`,
  `maturin`, and a `python/` directory that don't exist in this pure-Python
  repo. Every target was non-functional. Rewritten in this pass to match
  the actual pytest/black/ruff/mypy tooling this repo uses.
- **`.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`
  referenced "OpenAnchor"** (a different project) instead of PyTokenCalc.
  Fixed in this pass.
- **Top-level `CONTRIBUTING.md` said "License: MIT"** while the repo has
  been Apache-2.0 since commit `9768699` ("Relicense under Apache License
  2.0"). Fixed in this pass.
- **CI (`.github/workflows/ci.yml`) uses `actions/checkout@v4`,
  `actions/setup-python@v4`, `actions/upload-artifact@v4`.** `actionlint`
  flags `setup-python@v4` as an outdated runner. Dependabot already has
  open (unmerged) PRs against this exact repo bumping all three
  (`dependabot/github_actions/actions/checkout-7`,
  `.../setup-python-7`, `.../upload-artifact-7`) — the fix exists, it just
  hasn't been merged. Not duplicated by hand in this pass to avoid
  conflicting with those PRs; merge them.
- **No dependency/vulnerability-audit CI job existed.** Added a
  `dependency-audit` job to `.github/workflows/ci.yml` running `pip-audit`
  in this pass. **Unverified**: this sandbox has no network access to
  PyPI, so `pip-audit` could not actually be run here to confirm it
  produces clean/expected output on this dependency set. Confirm it runs
  and passes (or triages any findings) on the next real GitHub Actions run.
- **`docs/PRODUCT_VISION.md` / `docs/ROADMAP.md` referenced a package
  version "2.0.0"** that has never existed in `pyproject.toml` or
  `pytokencalc/_version.py` (both say `1.2.0`) — one more reason those
  files were fabricated rather than merely stale, and were deleted rather
  than corrected.

## 6. Not built / explicitly out of scope

- No async API. `count_tokens`/`estimate_cost` and every `TokenCounter`
  are synchronous; API-backed providers (Anthropic/Google/Cohere) block
  the calling thread for the network round trip.
- No CI matrix beyond `ubuntu-latest` — Windows/macOS are not tested in CI
  (probably fine for a pure-Python package with no OS-specific code paths,
  but unverified).
- No published SBOM, no signed releases, no reproducible-build
  verification.
- No live pricing feed — by design (see `pricing.py` docstring); don't
  build one without also solving the "who verifies it" problem.

## 7. Process notes for whoever picks this up next

Priority order if you have one dedicated session: ~~(1) the registry
exception-handling bug in section 2~~ **done 2026-09-22, see section 2**;
(2) add tests for `api.py`/`pricing.py` since that's the feature the
README leads with and it currently has zero coverage; (3) decide whether
the MCP subsystem gets real tests + docs or gets removed; (4) curate a
real `ruff` rule selection and turn lint on in CI once the (now 299,
see section 5) findings are triaged; (5) expand `pricing.py`'s
`PRICING_TABLE` to cover current-generation model families (see section
5 — existing rows were spot-checked and are accurate, but coverage is
incomplete); (6) add a bounded timeout around
`AutoTokenizer.from_pretrained()` in `huggingface_counter.py:71` /
`opensource_counter.py:102` — assessed in the 2026-09-22 pass as real
feature work (needs a thread/signal-based timeout wrapper since
`from_pretrained` has no native timeout param), not a quick fix, so still
open.
