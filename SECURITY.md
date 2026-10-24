# Security Policy

## Reporting a vulnerability

This is a solo-maintained open-source project. There is no dedicated
security team, no bug bounty, and no SLA on response time.

To report a security issue, email **mullassery@gmail.com** with a
description and, if possible, a minimal reproduction. Please do not open a
public GitHub issue for anything that could be actively exploited before a
fix ships (e.g. a way to leak an API key, execute arbitrary code, or bypass
the network-bind guard described below).

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
- **The MCP server has no authentication layer.** The FastMCP transport
  binds to `127.0.0.1` by default. HTTP/SSE binds to a non-loopback host
  are refused unless `PYTOKENCALC_MCP_ALLOW_UNAUTHENTICATED=1` is set;
  only set that variable behind your own auth/network controls.
  `pytokencalc.toml` is documentation only and is not currently loaded by
  the server. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detail.
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
  [docs/internal/ROADMAP_HONEST.md](docs/internal/ROADMAP_HONEST.md)). Dependabot is configured
  ([.github/dependabot.yml](.github/dependabot.yml)) for dependency
  version bumps, but there is no `pip-audit`/`safety` job verifying those
  bumps address real CVEs, and no SBOM is generated.
