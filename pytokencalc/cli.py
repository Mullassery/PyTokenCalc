"""CLI for PyTokenCalc - multi-provider LLM token counter workflow integration."""

import json
import sys
from typing import Optional

from .tokenizers import TokenCounterRegistry, TokenCounterCache


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
            result = self.registry.count(text, model, provider)
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
                text, model, num_images=image_count, provider=provider
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
            all_models = self.registry.list_all_models()
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

    help
        Show this help message

OUTPUT FORMAT:
    All commands return JSON output
"""
    print(help_text)


if __name__ == "__main__":
    main()
