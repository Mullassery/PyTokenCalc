# Quick CLI Guide: `pycount`

The fastest way to count tokens from your terminal.

## Installation

```bash
pip install pytokencalc
```

## Quick Examples

### Count tokens (one-liner)
```bash
pycount "Hello world"
# Output: 2 tokens (input: 2)
```

### Specify a model
```bash
pycount -m claude-3-sonnet "Your text here"
pycount --model gpt-4 "Your text here"
```

### Pipe from stdin
```bash
echo "Hello world" | pycount

# From a file
cat myfile.txt | pycount

# From another command
curl https://example.com/api/data | pycount -m gpt-4
```

### JSON output (for scripting)
```bash
pycount -j "Hello world"
# Output: {"model": "gpt-4", "tokens": 2, "input": 2, "output": 0, ...}

# Useful for automation
token_count=$(pycount -j "test" | jq .tokens)
echo "Used $token_count tokens"
```

### Specify provider (if needed)
```bash
pycount -p anthropic "text"
pycount -p openai "text"
```

## Usage Patterns

### Batch process multiple files
```bash
for file in *.txt; do
    echo -n "$file: "
    cat "$file" | pycount
done
```

### Check token count while writing
```bash
# Monitor as you compose
cat draft.txt | pycount

# Check with specific model
cat draft.txt | pycount -m claude-3-sonnet
```

### Integration with scripts
```bash
#!/bin/bash
text="$1"
tokens=$(pycount -j "$text" | jq .tokens)

if [ $tokens -gt 1000 ]; then
    echo "Warning: Text exceeds 1000 tokens ($tokens tokens)"
fi
```

### Cost estimation (manual)
```bash
# Count tokens, then calculate cost
tokens=$(echo "your text" | pycount -j | jq .tokens)
cost=$(echo "scale=4; $tokens * 0.00003" | bc)  # Example: $0.03 per 1M tokens
echo "Estimated cost: \$$cost"
```

## Default Behavior

| Aspect | Default |
|--------|---------|
| Model | `gpt-4` |
| Provider | Auto-detected (from model name) |
| Output | Human-readable token count |
| Input | Argument or stdin |

## All Options

```
pycount [OPTIONS] [TEXT]

OPTIONS:
  -m, --model MODEL       Model ID (default: gpt-4)
  -p, --provider PROV     Provider name (optional, auto-detected)
  -j, --json              Output as JSON (for scripting)
  -h, --help              Show help message
```

## Supported Models

GPT family:
- `gpt-4`, `gpt-4-turbo`, `gpt-4o`, `gpt-3.5-turbo`

Claude family:
- `claude-3-sonnet`, `claude-3-opus`, `claude-3-haiku`

Open source:
- `llama-70b`, `llama2-70b`, `mistral-7b`, `deepseek-67b`

And 20+ more. Run `pytokencalc models` to see the full list.

## Full CLI Reference

For the complete CLI with all features, use:

```bash
pytokencalc --help
```

The `pytokencalc` command has additional options for:
- Vision token counting
- Batch operations
- Provider/model discovery
- Cache statistics

But for quick terminal work, `pycount` is faster and simpler.

## Troubleshooting

### "No text provided"
Make sure you're either passing text as an argument or piping from stdin:
```bash
pycount "text"        # ✅ Works
echo "text" | pycount # ✅ Works
pycount               # ❌ Fails (no text)
```

### Model not found
Check supported models:
```bash
pytokencalc models
pytokencalc models openai
```

### Authentication errors
Some providers (Anthropic, Google) require API keys. Set them as environment variables or use models that work without auth (GPT models with tiktoken, open source models).

---

**Want the full-featured CLI?** See [README.md](README.md) for `pytokencalc` documentation.
