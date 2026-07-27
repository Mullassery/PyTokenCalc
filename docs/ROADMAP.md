# PyTokenCalc Roadmap

**Current Version:** v0.8.0

## Vision

PyTokenCalc provides unified token counting across 20+ LLM providers with intelligent routing, aggressive caching, and enterprise workflow integration.

## Completed Milestones

✅ **v0.1-0.7** — Core token counting engine
- Local tokenizers (tiktoken, HuggingFace)
- Multi-provider support (20+ cloud + open-source)
- Intelligent caching (70-80% API call reduction)
- Vision token counting

✅ **v0.8 (July 2026)** — Workflow Integration
- CLI interface: `pytokencalc count`, `count-vision`, `providers`, `models`, `cache-stats`
- REST API (Port 8005) for automation platforms
- n8n, Power Automate, Temporal, Airflow integration
- Bash/shell compatibility with JSON output
- Health check endpoints

## In Progress

⏳ **v0.9 (Aug 2026)** — Cost Intelligence
- Token cost estimation across all providers
- Budget tracking and alerts
- Cost comparison tools
- Enterprise billing integration

## Planned

📅 **v1.0 (Sep 2026)** — Production Hardening
- Distributed caching (Redis support)
- Multi-tenant isolation
- Advanced monitoring & logging
- Performance optimizations (sub-5ms latency)

📅 **v1.1 (Oct 2026)** — AI-Powered Optimization
- ML-based token prediction
- Automatic model selection optimization
- Prompt compression recommendations
- Context window optimization

📅 **v1.5 (Q4 2026)** — Enterprise Features
- On-premise deployment
- Custom provider support
- Advanced auditing & compliance
- SLA monitoring & reporting

## Integration Points

- **Workflow Tools:** n8n, Power Automate, Temporal, Airflow, UiPath
- **Frameworks:** LangChain, LlamaIndex, Semantic Kernel, CrewAI, PydanticAI
- **Deployment:** Docker, Kubernetes, serverless platforms

## Priority Features

1. **Cost Intelligence** (Q3 2026) — Budget tracking & optimization
2. **Distributed Caching** (Q3 2026) — Multi-instance deployment
3. **Custom Providers** (Q4 2026) — User-defined tokenizers
4. **Compliance & Audit** (Q4 2026) — Enterprise governance

## Known Limitations

- Vision token counting accuracy varies by provider
- Some proprietary models require API calls
- Caching TTL needs enterprise configuration

## Community Feedback

Contribute issues, feature requests, and PRs to:
https://github.com/Mullassery/PyTokenCalc/issues
