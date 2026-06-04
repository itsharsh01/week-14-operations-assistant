"""FastMCP server entry point for the operations inventory assistant."""

from fastmcp import FastMCP

if __package__:
    from .tools import register_tools
else:
    from tools import register_tools

mcp = FastMCP("Operations Inventory Assistant")

register_tools(mcp)

if __name__ == "__main__":
    mcp.run()
