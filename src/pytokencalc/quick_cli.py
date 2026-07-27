"""Quick CLI for PyTokenCalc - one-liner token counting from the terminal."""

import sys
import json
from typing import Optional

from .tokenizers import TokenCounterRegistry


class QuickCLI:
    """Simple, fast token counter for terminal use."""

    def __init__(self):
        self.registry = TokenCounterRegistry()

    def count(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        json_output: bool = False,
    ) -> None:
        """Count tokens and print result."""
        if not text.strip():
            print("Error: No text provided", file=sys.stderr)
            sys.exit(1)

        # Default to gpt-4 if no model specified
        if not model:
            model = "gpt-4"

        try:
            result = self.registry.count_tokens(model, text, provider)

            if json_output:
                output = {
                    "model": model,
                    "tokens": result.total_tokens,
                    "input": result.input_tokens,
                    "output": result.output_tokens,
                    "source": result.source,
                    "cached": result.cached,
                    "latency_ms": result.latency_ms,
                }
                print(json.dumps(output))
            else:
                # Human-readable output
                print(f"{result.total_tokens} tokens", end="")
                if result.input_tokens:
                    print(f" (input: {result.input_tokens}", end="")
                    if result.output_tokens:
                        print(f", output: {result.output_tokens}", end="")
                    print(")", end="")
                print()

        except Exception as e:
            if json_output:
                print(json.dumps({"error": str(e), "model": model}))
            else:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """Main entry point for pycount command."""
    cli = QuickCLI()

    # Parse arguments
    model = None
    provider = None
    json_output = False
    text = None

    # Simple argument parsing
    args = sys.argv[1:]

    while args:
        arg = args.pop(0)

        if arg in ["-h", "--help"]:
            print_help()
            sys.exit(0)
        elif arg in ["-m", "--model"]:
            if not args:
                print("Error: --model requires an argument", file=sys.stderr)
                sys.exit(1)
            model = args.pop(0)
        elif arg in ["-p", "--provider"]:
            if not args:
                print("Error: --provider requires an argument", file=sys.stderr)
                sys.exit(1)
            provider = args.pop(0)
        elif arg in ["-j", "--json"]:
            json_output = True
        elif arg.startswith("-"):
            print(f"Error: Unknown option {arg}", file=sys.stderr)
            sys.exit(1)
        else:
            # First non-option argument is the text
            text = arg
            # Remaining args are appended to text (if user didn't quote)
            if args:
                text += " " + " ".join(args)
            break

    # Handle stdin if no text provided
    if not text:
        if not sys.stdin.isatty():
            # Reading from pipe
            text = sys.stdin.read()
        else:
            # No text and no pipe
            print_help()
            sys.exit(1)

    cli.count(text, model, provider, json_output)


def print_help():
    """Print help message."""
    help_text = """
pycount - Quick terminal token counter

USAGE:
    pycount [OPTIONS] [TEXT]
    echo "text" | pycount [OPTIONS]

ARGUMENTS:
    TEXT                Text to count tokens for (optional if piping from stdin)

OPTIONS:
    -m, --model MODEL       Model to use (default: gpt-4)
                           Examples: gpt-4, claude-3-sonnet, llama-70b

    -p, --provider PROV     Provider name (optional, auto-detect if not given)
                           Examples: openai, anthropic, mistral

    -j, --json              Output as JSON instead of human-readable

    -h, --help              Show this help message

EXAMPLES:
    # Quick count (uses gpt-4 by default)
    pycount "Hello world"

    # Count for specific model
    pycount -m claude-3-sonnet "Hello world"

    # Pipe from stdin
    echo "Hello world" | pycount

    # From a file
    cat myfile.txt | pycount -m gpt-4

    # JSON output for scripting
    pycount -j "Hello world"

    # Specify provider
    pycount -m claude-3-sonnet -p anthropic "Hello world"

DEFAULTS:
    - Model: gpt-4 (if not specified)
    - Provider: auto-detected based on model name
    - Output: human-readable token count

SUPPORTED MODELS:
    Run: pytokencalc models
"""
    print(help_text)


if __name__ == "__main__":
    main()
