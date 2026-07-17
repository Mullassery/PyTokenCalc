# Changelog

All notable changes to PyTokenCalc are documented in this file.

## [0.9.0] - 2026-07-18

### Added (Major Features)
- **Custom Provider Registration**: Register ANY provider with an API endpoint
- **Local Inference Engine Support**: Auto-detect LM Studio, LocalAI, Llama.cpp, GPT4All, Text Generation WebUI, Jan, Vllm
- **Ollama Integration**: Full support for Ollama with dynamic model discovery
- **Model Discovery System**: Pattern-based provider suggestion, model lookup, setup instructions
- **BYOM Support**: Bring your own model - fine-tuned, proprietary, or custom models
- **Platform-Aware Tracking**: Metadata for platform, source, and temporal tracking
- **Temporal Variation Monitoring**: Timestamp and session_id tracking for infrastructure changes
- **Forward-Compatible Patterns**: Pattern-based validation (claude-*, gemini-*, command-*) instead of hardcoded lists

### Added (Testing & Verification)
- 40 accuracy verification tests (OpenAI, Azure, Anthropic, Google, Cohere, HuggingFace)
- 23 model discovery tests (pattern matching, lookup, reporting)
- 7 custom provider tests (registration, integration, examples)
- 6 temporal variation tests (timestamp, session tracking, latency monitoring)
- 3 local inference tests (auto-detection, model discovery)
- Platform difference documentation and tests

### Added (Documentation)
- CUSTOM_PROVIDERS.md (200+ lines with 10+ provider examples)
- Model discovery documentation
- Platform awareness guidance (prevent confusion with multi-platform results)
- Temporal variation best practices
- BYOM (Bring Your Own Model) examples

### Changed
- TokenCountResult now includes `timestamp` and `session_id` fields
- Anthropic provider: Changed from hardcoded model list to claude-* pattern
- Google provider: Changed from hardcoded model list to gemini-* pattern
- Cohere provider: Changed from hardcoded model list to command-* pattern
- OpenSource provider: Removed hardcoded MODEL_ALIASES, now accepts ANY HuggingFace model

### Fixed
- Forward compatibility: New Anthropic models (like fable) now work without code changes
- Forward compatibility: New Google Gemini models work automatically
- Forward compatibility: New Cohere Command variants work automatically
- Forward compatibility: Any HuggingFace model now works (no hardcoded list)
- Forward compatibility: Ollama models update daily without requiring PyTokenCalc updates

### Technical Improvements
- Added model discovery module for pattern-based provider lookup
- Registry integration with custom providers
- Graceful fallback for unavailable local inference engines
- Improved error messages for unknown models/providers
- Multi-provider model support (same model on different providers)

### Performance
- No performance regression
- Custom providers add <5ms overhead
- Model discovery is instant (pattern-based)
- Cache continues to provide 70-80% API call reduction

### Breaking Changes
- None - fully backward compatible

### Migration Guide
No changes required. Existing code works exactly as before. New features are available immediately:

```python
# Existing code - still works
result = registry.count_tokens("gpt-4o", text)

# New features available
from pytokencalc.model_discovery import ModelDiscovery
from pytokencalc.tokenizers.custom_provider_counter import CustomProviderCounter

# Discover providers
providers = ModelDiscovery.suggest_provider("llama-2-7b")

# Register custom provider
my_provider = CustomProviderCounter(provider_name="custom", base_url="http://localhost:8000")
```

### Testing
- Total: 104 tests passing, 25 tests skipped (expected - API keys, offline services)
- All tests pass on Python 3.9+
- No regressions from v0.8.0

### Deprecations
- None

### Dependencies
- No new dependencies added
- Optional: requests (for custom providers, already optional)

---

## [0.8.0] - 2026-06-15

### Initial Release
- Token counting for 8 cloud providers
- Support for 30+ LLM models
- Intelligent caching (70-80% API reduction)
- CLI and REST API integration
- Multi-provider auto-detection

---

## Versioning

PyTokenCalc follows [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible new features  
- PATCH version for backwards-compatible bug fixes

## Release Notes

See https://github.com/Mullassery/PyTokenCalc/releases for detailed release notes and upgrade instructions.
