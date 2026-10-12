"""Example: PyTokenCalc MCP tool surface.

This shows the real MCP tool schemas and handlers. PyTokenCalc does not ship
an MCP server/transport (the old implementation tried to shell out to an
external ``dab`` binary that is not a dependency), so you drive the handler
from your own MCP host. Here we call it directly.
"""

import asyncio

from pytokencalc import TokenCalculator


async def main():
    calc = TokenCalculator()
    handler = calc.get_handler()

    tools = calc.get_tools()
    print(f"PyTokenCalc exposes {len(tools)} MCP tools: {', '.join(sorted(tools))}")

    # Real token count (requires the model's tokenizer dependency, e.g.
    # `pip install pytokencalc[tokenizers]` for OpenAI/tiktoken).
    counted = await handler.count_tokens("Tell me a short story", "gpt-4o")
    print("count_tokens:", counted)

    # Real cost estimate from the static pricing table.
    if counted.get("input_tokens"):
        cost = await handler.estimate_cost(
            counted["input_tokens"], output_tokens=200, model_name="gpt-4o"
        )
        print("estimate_cost:", cost)

    # Pricing is available with no tokenizer installed at all.
    print("get_model_pricing:", await handler.get_model_pricing("claude-3-5-sonnet"))


if __name__ == "__main__":
    asyncio.run(main())
