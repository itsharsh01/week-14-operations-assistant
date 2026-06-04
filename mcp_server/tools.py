"""MCP tools for the operations inventory assistant."""

from fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Register all tools on the given FastMCP server instance."""

    @mcp.tool
    def ping() -> str:
        """Health check. Returns a short confirmation that the MCP server is running."""
        return "Operations Inventory MCP server is running."
