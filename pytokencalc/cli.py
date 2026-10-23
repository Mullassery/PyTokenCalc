"""CLI for PyTokenCalc - multi-provider LLM token counter workflow integration."""

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .okf_token_baselines import (
    OKFTokenBaselines,
    build_baseline_from_samples,
)
from .tokenizers import TokenCounterCache, TokenCounterRegistry


class CLIInterface:
    """Command-line interface for PyTokenCalc workflow integration."""

    def __init__(self):
        self.cache = TokenCounterCache()
        self.registry = TokenCounterRegistry(cache=self.cache)
        self.sessions = {}

    def count_tokens(
        self,
        text: str,
        model: str,
        provider: Optional[str] = None,
    ) -> dict:
        """Count tokens for text input.

        Args:
            text: Input text to count
            model: Model identifier (e.g., 'gpt-4', 'claude-3-sonnet')
            provider: Provider name (optional, auto-detect if not given)

        Returns:
            JSON response with token counts
        """
        try:
            result = self.registry.count_tokens(model, text, provider)
            return {
                "status": "success",
                "model": model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "image_tokens": result.image_tokens,
                "system_tokens": result.system_tokens,
                "tool_tokens": result.tool_tokens,
                "total_tokens": result.total_tokens,
                "source": result.source,
                "cached": result.cached,
                "latency_ms": result.latency_ms,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "model": model,
            }

    def count_vision(
        self,
        text: str,
        model: str,
        image_count: int = 1,
        provider: Optional[str] = None,
    ) -> dict:
        """Count tokens for text + vision input.

        Args:
            text: Input text to count
            model: Model identifier (e.g., 'gpt-4-vision')
            image_count: Number of images (default: 1)
            provider: Provider name (optional)

        Returns:
            JSON response with token counts including vision tokens
        """
        try:
            result = self.registry.count_vision(
                model, text, num_images=image_count, provider=provider
            )
            return {
                "status": "success",
                "model": model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "image_tokens": result.image_tokens,
                "system_tokens": result.system_tokens,
                "tool_tokens": result.tool_tokens,
                "total_tokens": result.total_tokens,
                "source": result.source,
                "cached": result.cached,
                "latency_ms": result.latency_ms,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "model": model,
            }

    def list_providers(self) -> dict:
        """List all available providers.

        Returns:
            JSON response with provider list
        """
        providers = self.registry.list_providers()
        return {
            "status": "success",
            "providers": providers,
            "count": len(providers),
        }

    def list_models(self, provider: Optional[str] = None) -> dict:
        """List supported models.

        Args:
            provider: Filter by provider (optional)

        Returns:
            JSON response with model list
        """
        if provider:
            models = self.registry.list_models(provider)
            return {
                "status": "success",
                "provider": provider,
                "models": models,
                "count": len(models),
            }
        else:
            all_models = self.registry.list_models()
            return {
                "status": "success",
                "models": all_models,
                "count": len(all_models),
            }

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            JSON response with cache stats
        """
        stats = self.cache.get_stats()
        return {
            "status": "success",
            "cached_counts": stats.get("size", 0),
            "cache_hits": stats.get("hits", 0),
            "cache_misses": stats.get("misses", 0),
            "hit_rate": stats.get("hit_rate_percent", 0.0),
        }

    def clear_cache(self) -> dict:
        """Clear the token count cache.

        Returns:
            JSON response confirming cache clear
        """
        self.cache.clear()
        return {
            "status": "success",
            "message": "Cache cleared successfully",
        }


def _parse_cli_options(args, allowed):
    """Parse ``--key value`` / ``--key=value`` options plus positionals."""
    options = {}
    positional = []
    index = 0

    while index < len(args):
        arg = args[index]
        if arg.startswith("--"):
            name = arg[2:]
            if "=" in name:
                name, value = name.split("=", 1)
            else:
                if index + 1 >= len(args):
                    raise ValueError(f"--{name} requires a value")
                value = args[index + 1]
                index += 1

            key = name.replace("-", "_")
            if key not in allowed:
                raise ValueError(f"Unknown option: --{name}")
            options[key] = value
        elif arg.startswith("-"):
            raise ValueError(f"Unknown option: {arg}")
        else:
            positional.append(arg)

        index += 1

    return options, positional


def _required_option(options, key):
    value = options.get(key)
    if not value:
        raise ValueError(f"--{key.replace('_', '-')} is required")
    return value


def _parse_tags(value):
    tags = {}
    if not value:
        return tags
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("--tags entries must be key=value")
        key, tag_value = item.split("=", 1)
        if not key.strip():
            raise ValueError("--tags keys must be non-empty")
        tags[key.strip()] = tag_value.strip()
    return tags


def _load_json_object(path):
    """Load a JSON object (or array) from *path*."""
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"JSON file not found: {path}") from exc
    if not isinstance(raw, (dict, list)):
        raise ValueError("JSON file must contain an object or array")
    return raw


def _load_json_samples(path):
    """Load a JSON array, or an object with a ``samples`` array."""
    try:
        raw = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Samples file not found: {path}") from exc

    metadata = {}
    if isinstance(raw, list):
        samples = raw
    elif isinstance(raw, dict):
        metadata = {key: raw[key] for key in ("provider", "model", "task_type") if key in raw}
        if not isinstance(raw.get("samples"), list):
            raise ValueError('Samples JSON must be an array or an object with a "samples" array')
        samples = raw["samples"]
    else:
        raise ValueError('Samples JSON must be an array or an object with a "samples" array')

    return samples, metadata


def _load_jsonl_samples(path):
    """Load one sample object per non-blank line, reporting line numbers."""
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Samples file not found: {path}") from exc

    samples = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            sample = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(sample, dict):
            raise ValueError(f"{path}:{line_number}: each line must be a JSON object")
        samples.append(sample)

    return samples


def _save_samples_as_baseline(cli, options, samples, metadata):
    provider = options.get("provider") or metadata.get("provider")
    model = options.get("model") or metadata.get("model")
    task_type = options.get("task_type") or metadata.get("task_type")

    if not provider:
        raise ValueError("--provider is required")
    if not model:
        raise ValueError("--model is required")
    if not task_type:
        raise ValueError("--task-type is required")

    def count_prompt(prompt):
        return cli.registry.count_tokens(model, prompt, provider).input_tokens

    baseline = build_baseline_from_samples(
        provider,
        model,
        task_type,
        samples,
        input_counter=count_prompt,
    )

    baseline_dir = options.get("baseline_dir")
    store = OKFTokenBaselines(Path(baseline_dir) if baseline_dir else None)
    store.save_baseline(baseline)

    filename = f"{baseline.provider}_{baseline.model}_{baseline.task_type}.json"
    return {
        "status": "success",
        "baseline": asdict(baseline),
        "path": str(store.baseline_dir / filename),
    }


def _handle_baseline_command(cli, args):
    if not args:
        raise ValueError("baseline requires a subcommand: save, list, compare, from-jsonl")

    subcommand = args[0]
    rest = args[1:]
    common = {"provider", "model", "task_type", "baseline_dir"}

    if subcommand == "save":
        options, positional = _parse_cli_options(rest, common | {"samples"})
        source = options.get("samples") or (positional[0] if positional else None)
        if not source:
            raise ValueError("baseline save requires --samples PATH")
        if len(positional) > 1:
            raise ValueError("baseline save accepts a single samples file")

        samples, metadata = _load_json_samples(Path(source))
        return _save_samples_as_baseline(cli, options, samples, metadata)

    if subcommand == "from-jsonl":
        options, positional = _parse_cli_options(rest, common | {"samples"})
        source = options.get("samples") or (positional[0] if positional else None)
        if not source:
            raise ValueError("baseline from-jsonl requires a JSONL path")
        if len(positional) > 1:
            raise ValueError("baseline from-jsonl accepts a single JSONL file")

        samples = _load_jsonl_samples(Path(source))
        return _save_samples_as_baseline(cli, options, samples, {})

    if subcommand == "list":
        options, positional = _parse_cli_options(rest, common)
        if positional:
            raise ValueError("baseline list takes no positional arguments")

        baseline_dir = options.get("baseline_dir")
        store = OKFTokenBaselines(Path(baseline_dir) if baseline_dir else None)
        baselines = store.list_baselines(
            provider=options.get("provider"),
            task_type=options.get("task_type"),
        )
        return {
            "status": "success",
            "baseline_dir": str(store.baseline_dir),
            "baselines": [asdict(baseline) for baseline in baselines],
            "count": len(baselines),
        }

    if subcommand == "compare":
        options, positional = _parse_cli_options(rest, common)
        if positional:
            raise ValueError("baseline compare takes no positional arguments")

        provider = _required_option(options, "provider")
        task_type = _required_option(options, "task_type")
        baseline_dir = options.get("baseline_dir")
        store = OKFTokenBaselines(Path(baseline_dir) if baseline_dir else None)
        models = store.compare_models(provider, task_type)
        return {
            "status": "success",
            "provider": provider,
            "task_type": task_type,
            "models": models,
            "count": len(models),
        }

    raise ValueError(
        f"Unknown baseline subcommand: {subcommand}. Use save, list, compare, or from-jsonl"
    )


def main():
    """Main CLI entry point."""
    cli = CLIInterface()

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "count":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing text or model"}))
                sys.exit(1)

            text = sys.argv[2]
            model = sys.argv[3]
            provider = sys.argv[4] if len(sys.argv) > 4 else None

            result = cli.count_tokens(text, model, provider)
            print(json.dumps(result))

        elif command == "count-vision":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Missing text or model"}))
                sys.exit(1)

            text = sys.argv[2]
            model = sys.argv[3]
            image_count = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            provider = sys.argv[5] if len(sys.argv) > 5 else None

            result = cli.count_vision(text, model, image_count, provider)
            print(json.dumps(result))

        elif command == "providers":
            result = cli.list_providers()
            print(json.dumps(result))

        elif command == "models":
            provider = sys.argv[2] if len(sys.argv) > 2 else None
            result = cli.list_models(provider)
            print(json.dumps(result))

        elif command == "cache-stats":
            result = cli.get_cache_stats()
            print(json.dumps(result))

        elif command == "clear-cache":
            result = cli.clear_cache()
            print(json.dumps(result))

        elif command == "pricing":
            from .pricing import load_pricing_override, pricing_status

            status = pricing_status()
            if "--file" in sys.argv:
                index = sys.argv.index("--file")
                if index + 1 >= len(sys.argv):
                    print(json.dumps({"error": "--file requires a path"}))
                    sys.exit(1)
                status = load_pricing_override(sys.argv[index + 1])
            print(json.dumps(status))

        elif command == "catalog":
            if len(sys.argv) > 2 and sys.argv[2] == "import":
                from .openrouter import import_openrouter_catalog_file

                options, positional = _parse_cli_options(
                    sys.argv[3:], {"file", "include_variants"}
                )
                if positional:
                    raise ValueError(
                        "catalog import takes options, not positional arguments"
                    )
                source = _required_option(options, "file")
                include_variants = options.get("include_variants", "").lower() in {
                    "1",
                    "true",
                    "yes",
                }
                result = import_openrouter_catalog_file(
                    source, include_variants=include_variants
                )
                print(json.dumps(result.to_dict()))
            else:
                from .catalog import list_models

                provider = sys.argv[2] if len(sys.argv) > 2 else None
                specs = list_models(provider)
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "provider": provider,
                            "models": [spec.to_dict() for spec in specs],
                            "count": len(specs),
                        }
                    )
                )

        elif command == "model-info":
            from .catalog import get_model_spec

            if len(sys.argv) < 3:
                raise ValueError("model-info requires a model ID")
            spec = get_model_spec(sys.argv[2])
            if spec is None:
                raise ValueError(f"Unknown model: {sys.argv[2]}")
            print(json.dumps(spec.to_dict()))

        elif command == "preflight":
            from .preflight import preflight

            options, positional = _parse_cli_options(
                sys.argv[2:],
                {"file", "model", "max_output", "provider"},
            )
            if positional:
                raise ValueError("preflight takes options, not positional arguments")
            source = _required_option(options, "file")
            model = _required_option(options, "model")
            payload = _load_json_object(Path(source))
            if isinstance(payload, dict) and "messages" in payload:
                messages = payload["messages"]
                tools = payload.get("tools")
                default_max = payload.get("max_output_tokens")
            else:
                messages = payload
                tools = None
                default_max = None
            if "max_output" in options:
                max_output = int(options["max_output"])
            elif default_max is not None:
                max_output = int(default_max)
            else:
                max_output = None
            result = preflight(
                messages,
                model,
                tools=tools,
                max_output_tokens=max_output,
                provider=options.get("provider"),
            )
            print(json.dumps(result.to_dict()))

        elif command == "reconcile":
            from .reconcile import reconcile

            options, positional = _parse_cli_options(
                sys.argv[2:],
                {"file", "model", "provider", "expected_cost"},
            )
            if positional:
                raise ValueError("reconcile takes options, not positional arguments")
            source = _required_option(options, "file")
            model = _required_option(options, "model")
            expected = (
                float(options["expected_cost"]) if "expected_cost" in options else None
            )
            result = reconcile(
                model,
                _load_json_object(Path(source)),
                provider=options.get("provider"),
                expected_cost_usd=expected,
            )
            print(json.dumps(result.to_dict()))

        elif command == "usage":
            from .ledger import UsageLedger
            from .reconcile import reconcile

            subcommand = sys.argv[2] if len(sys.argv) > 2 else "report"
            if subcommand == "add":
                options, positional = _parse_cli_options(
                    sys.argv[3:],
                    {
                        "file",
                        "model",
                        "provider",
                        "expected_cost",
                        "ledger",
                        "tags",
                        "generation_id",
                    },
                )
                if positional:
                    raise ValueError("usage add takes options, not positional arguments")
                source = _required_option(options, "file")
                model = _required_option(options, "model")
                ledger = UsageLedger(options.get("ledger"))
                expected = (
                    float(options["expected_cost"])
                    if "expected_cost" in options
                    else None
                )
                reconciliation = reconcile(
                    model,
                    _load_json_object(Path(source)),
                    provider=options.get("provider"),
                    expected_cost_usd=expected,
                )
                record = ledger.record_reconciliation(
                    reconciliation,
                    tags=_parse_tags(options.get("tags")),
                    generation_id=options.get("generation_id"),
                )
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "ledger": str(ledger.path),
                            "record": record,
                        }
                    )
                )
            elif subcommand == "report":
                options, positional = _parse_cli_options(
                    sys.argv[3:], {"ledger", "since"}
                )
                if positional:
                    raise ValueError("usage report takes options, not positional arguments")
                ledger = UsageLedger(options.get("ledger"))
                print(
                    json.dumps(
                        {
                            "status": "success",
                            **ledger.summary(since=options.get("since")),
                        }
                    )
                )
            elif subcommand == "list":
                options, positional = _parse_cli_options(
                    sys.argv[3:], {"ledger", "since", "limit"}
                )
                if positional:
                    raise ValueError("usage list takes options, not positional arguments")
                ledger = UsageLedger(options.get("ledger"))
                limit = int(options["limit"]) if "limit" in options else None
                records = ledger.list_records(
                    since=options.get("since"), limit=limit
                )
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "ledger": str(ledger.path),
                            "count": len(records),
                            "records": records,
                        }
                    )
                )
            else:
                raise ValueError(f"Unknown usage subcommand: {subcommand}")

        elif command == "compare":
            from .pricing import Usage, compare_models

            options, positional = _parse_cli_options(
                sys.argv[2:],
                {
                    "models",
                    "input_tokens",
                    "output_tokens",
                    "cached_input_tokens",
                    "cache_write_tokens",
                    "requests",
                },
            )
            if positional:
                raise ValueError("compare takes options, not positional arguments")
            models = [
                model.strip()
                for model in _required_option(options, "models").split(",")
                if model.strip()
            ]
            if not models:
                raise ValueError("--models must contain at least one model")
            usage = Usage(
                input_tokens=int(_required_option(options, "input_tokens")),
                output_tokens=int(options.get("output_tokens", 0)),
                cached_input_tokens=int(options.get("cached_input_tokens", 0)),
                cache_write_tokens=int(options.get("cache_write_tokens", 0)),
                request_count=int(options.get("requests", 1)),
            )
            comparisons = compare_models(models, usage)
            print(
                json.dumps(
                    {
                        "status": "success",
                        "comparisons": [item.to_dict() for item in comparisons],
                        "cheapest_model": next(
                            (
                                item.model
                                for item in comparisons
                                if item.cost is not None
                            ),
                            None,
                        ),
                    }
                )
            )

        elif command == "endpoints":
            from .catalog import get_model_spec
            from .endpoints import compare_endpoints
            from .openrouter import import_openrouter_endpoints_file
            from .pricing import Usage

            subcommand = sys.argv[2] if len(sys.argv) > 2 else "list"
            if subcommand == "import":
                options, positional = _parse_cli_options(
                    sys.argv[3:], {"file", "model"}
                )
                if positional:
                    raise ValueError(
                        "endpoints import takes options, not positional arguments"
                    )
                source = _required_option(options, "file")
                result = import_openrouter_endpoints_file(
                    source, model_id=options.get("model")
                )
                print(json.dumps(result.to_dict()))
            elif subcommand == "list":
                options, positional = _parse_cli_options(
                    sys.argv[3:], {"model"}
                )
                if positional:
                    raise ValueError(
                        "endpoints list takes options, not positional arguments"
                    )
                model = _required_option(options, "model")
                spec = get_model_spec(model)
                if spec is None:
                    raise ValueError(f"Unknown model: {model}")
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "model": spec.id,
                            "count": len(spec.endpoints),
                            "endpoints": [
                                endpoint.to_dict() for endpoint in spec.endpoints
                            ],
                        }
                    )
                )
            elif subcommand == "compare":
                options, positional = _parse_cli_options(
                    sys.argv[3:],
                    {
                        "model",
                        "input_tokens",
                        "output_tokens",
                        "cached_input_tokens",
                        "cache_write_tokens",
                        "provider",
                        "requests",
                    },
                )
                if positional:
                    raise ValueError(
                        "endpoints compare takes options, not positional arguments"
                    )
                model = _required_option(options, "model")
                usage = Usage(
                    input_tokens=int(_required_option(options, "input_tokens")),
                    output_tokens=int(options.get("output_tokens", 0)),
                    cached_input_tokens=int(
                        options.get("cached_input_tokens", 0)
                    ),
                    cache_write_tokens=int(
                        options.get("cache_write_tokens", 0)
                    ),
                    request_count=int(options.get("requests", 1)),
                )
                comparisons = compare_endpoints(
                    model, usage, provider=options.get("provider")
                )
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "model": model,
                            "comparisons": [
                                item.to_dict() for item in comparisons
                            ],
                            "cheapest_provider": next(
                                (
                                    item.endpoint.provider
                                    for item in comparisons
                                    if item.cost is not None
                                ),
                                None,
                            ),
                        }
                    )
                )
            else:
                raise ValueError(f"Unknown endpoints subcommand: {subcommand}")

        elif command == "benchmark":
            from .benchmark import benchmark_counts, load_samples

            options, positional = _parse_cli_options(
                sys.argv[2:], {"file", "model", "provider"}
            )
            if positional:
                raise ValueError("benchmark takes options, not positional arguments")
            source = _required_option(options, "file")
            summary = benchmark_counts(
                load_samples(source),
                model=options.get("model"),
                provider=options.get("provider"),
            )
            print(json.dumps({"status": "success", **summary.to_dict()}))

        elif command == "baseline":
            result = _handle_baseline_command(cli, sys.argv[2:])
            print(json.dumps(result))

        elif command == "help":
            print_help()

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e), "status": "error"}))
        sys.exit(1)


def print_help():
    """Print help message."""
    help_text = """
PyTokenCalc CLI - Multi-Provider LLM Token Counter Workflow Integration

USAGE:
    pytokencalc <command> [options]

COMMANDS:
    count <text> <model> [provider]
        Count tokens for text input
        - text: Text to tokenize (required)
        - model: Model ID (required) - e.g., gpt-4, claude-3-sonnet, llama-70b
        - provider: Provider name (optional) - auto-detect if not given

        Example:
            pytokencalc count "Hello world" gpt-4
            pytokencalc count "Hello world" claude-3-sonnet anthropic

    count-vision <text> <model> [image_count] [provider]
        Count tokens for text + vision input
        - text: Text to tokenize (required)
        - model: Model ID (required) - e.g., gpt-4-vision
        - image_count: Number of images (default: 1)
        - provider: Provider name (optional)

        Example:
            pytokencalc count-vision "Describe this" gpt-4-vision 3

    pricing [--file PATH]
        Show pricing-snapshot age/staleness; optionally merge a local JSON
        override with {"last_updated": "YYYY-MM-DD", "models": {...}}

    catalog [provider]
        List model metadata: context window, modalities, tokenizer, pricing

    catalog import --file FILE [--include-variants true]
        Import a downloaded OpenRouter /api/v1/models JSON snapshot

    model-info <model>
        Show metadata and pricing for one model

    preflight --file REQUEST.json --model MODEL [--max-output N] [--provider P]
        Count a chat request before sending it and check context/cost fit.
        REQUEST.json can be an array of messages or {"messages": [...], "tools": [...]}

    reconcile --file RESPONSE.json --model MODEL [--provider P] [--expected-cost USD]
        Compare provider-reported usage/cost with a prior estimate

    usage add --file RESPONSE.json --model MODEL [--provider P] [--expected-cost USD]
        Append a reconciled usage record to a JSONL ledger

    usage report [--ledger PATH] [--since ISO_TIMESTAMP]
        Summarize recorded usage and spend

    usage list [--ledger PATH] [--since ISO_TIMESTAMP] [--limit N]
        Show individual ledger records

    compare --models MODEL1,MODEL2 --input-tokens N [--output-tokens N]
        Compare one usage profile across models, cheapest first

    endpoints import --file FILE [--model MODEL]
        Import a downloaded OpenRouter model-endpoints JSON snapshot

    endpoints list --model MODEL
        Show endpoint-level pricing/metadata for a model

    endpoints compare --model MODEL --input-tokens N [--output-tokens N]
        Compare providers/endpoints for one model, cheapest first

    benchmark --file SAMPLES.jsonl [--model MODEL] [--provider P]
        Compare local token counts against provider-reported usage

    providers
        List all available token counter providers

        Example:
            pytokencalc providers

    models [provider]
        List supported models
        - provider: Filter by provider (optional)

        Example:
            pytokencalc models
            pytokencalc models openai

    cache-stats
        Get token count cache statistics

        Example:
            pytokencalc cache-stats

    clear-cache
        Clear the token count cache

        Example:
            pytokencalc clear-cache

    baseline save --samples PATH --provider P --model M --task-type T [--baseline-dir DIR]
        Build and save a historical baseline from a JSON array of real
        {"prompt": ..., "output_tokens": ...} samples (or input_tokens instead
        of prompt). The object form {"provider": ..., "model": ...,
        "task_type": ..., "samples": [...]} may supply the metadata too.

    baseline from-jsonl PATH --provider P --model M --task-type T [--baseline-dir DIR]
        Same as save, but reads one JSON sample object per non-blank line.
        Prompts are counted with the exact tokenizer for the given model.

    baseline list [--provider P] [--task-type T] [--baseline-dir DIR]
        List stored baselines, including sample counts and p95 token data.

    baseline compare --provider P --task-type T [--baseline-dir DIR]
        Compare stored models, including average and p95 token counts.

        Examples:
            pytokencalc baseline save --samples samples.json --provider openai
                --model gpt-4o --task-type chat
            pytokencalc baseline from-jsonl samples.jsonl --provider openai
                --model gpt-4o --task-type chat
            pytokencalc baseline list --provider openai
            pytokencalc baseline compare --provider openai --task-type chat

    help
        Show this help message

OUTPUT FORMAT:
    All commands return JSON output
"""
    print(help_text)


if __name__ == "__main__":
    main()
