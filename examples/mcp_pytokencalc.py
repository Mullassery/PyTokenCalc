"""Example: PyTokenCalc MCP 2.0 Integration"""

import asyncio
from pytokencalc import TokenCalculator

async def main():
    # Initialize with MCP 2.0 support
    calc = TokenCalculator()

    # Start MCP connector (requires the `statguardian` package for the real
    # DAB-backed connector; falls back to the bundled stub otherwise)
    mcp_url = calc.start_mcp_connector()
    print(f"✓ PyTokenCalc MCP 2.0 running at {mcp_url}")

    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        calc.stop_mcp_connector()
        print("✓ MCP server stopped")

if __name__ == "__main__":
    asyncio.run(main())
