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
        self.registry = TokenCounterRegistry()
        self.cache = TokenCounterCache()
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
            "cached_counts": stats.get("cached_counts", 0),
            "cache_hits": stats.get("cache_hits", 0),
            "cache_misses": stats.get("cache_misses", 0),
            "hit_rate": stats.get("hit_rate", 0.0),
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
        Show pricing-snapshot age/staleness; optionally load a local JSON
        override with {"last_updated": "YYYY-MM-DD", "models": {...}}

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
