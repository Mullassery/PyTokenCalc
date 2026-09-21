# Security Policy

## Reporting a vulnerability

This is a solo-maintained open-source project. There is no dedicated
security team, no bug bounty, and no SLA on response time.

To report a security issue, email **mullassery@gmail.com** with a
description and, if possible, a minimal reproduction. Please do not open a
public GitHub issue for anything that could be actively exploited before a
fix ships (e.g. a way to leak an API key, execute arbitrary code, or bypass
the auth defaults described below).

There is currently no GPG key for encrypted reports and no published CVE
process. If a report turns into a real fix, it will be credited in
[CHANGELOG.md](CHANGELOG.md) unless you ask not to be.

## Supported versions

Only the latest release on PyPI is supported. There are no LTS branches
and no backported security fixes to older versions.

## Known security-relevant behavior (as of this writing)

This section is deliberately specific instead of generic reassurance:

- **REST server (`pytokencalc/server.py` / `pytokencalc.server.run_server`)**
  binds to `127.0.0.1` by default and implements **no authentication**.
  Passing `host="0.0.0.0"` exposes token-counting/cost endpoints to the
  network with zero access control; only do this behind your own
  auth/network layer. This is documented, not hidden, but it is real
  attack surface if misconfigured.
- **API keys** for Anthropic/Google/Cohere counters are read from the
  environment (e.g. `ANTHROPIC_API_KEY`) by the underlying provider SDKs,
  not by PyTokenCalc itself. PyTokenCalc does not log, cache, or persist
  these keys, but it also does not scrub them from tracebacks raised by
  the underlying SDKs.
- **The MCP connector** (`pytokencalc._mcp_connector.TokenCalculator`,
  exported at the top level) has a `require_auth = true` default in
  `pytokencalc.toml` and a security comment in `_mcp_connector.py`
  disclaiming wildcard CORS/RBAC by default. This code path is
  **untested** (no test file covers it) and depends on an external `dab`
  binary not bundled or pinned by this project. Do not treat its security
  defaults as verified; treat the entire MCP subsystem as experimental.
  See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detail.
- **Local-inference / custom-provider / Ollama counters**
  (`tokenizers/ollama_counter.py`, `tokenizers/local_inference_counter.py`,
  `tokenizers/custom_provider_counter.py`) make outbound HTTP requests to
  URLs you configure (default `http://localhost:11434` for Ollama). If you
  point a custom provider at an untrusted URL, PyTokenCalc will send your
  request text to it verbatim with no sanitization — this is by design
  (BYOM support) but is worth knowing.
- **HuggingFace/open-source tokenizer loading**
  (`tokenizers/huggingface_counter.py`, `tokenizers/opensource_counter.py`)
  calls `transformers.AutoTokenizer.from_pretrained(model_id)`, which will
  download and execute tokenizer config/code from the HuggingFace Hub for
  whatever `model_id` you pass in. As with any use of `from_pretrained`,
  only pass model IDs you trust — this is standard `transformers` behavior,
  not something PyTokenCalc adds a sandbox around.
- No dependency/vulnerability scanning currently runs in CI (see
  [ROADMAP_HONEST.md](ROADMAP_HONEST.md)). Dependabot is configured
  ([.github/dependabot.yml](.github/dependabot.yml)) for dependency
  version bumps, but there is no `pip-audit`/`safety` job verifying those
  bumps address real CVEs, and no SBOM is generated.
