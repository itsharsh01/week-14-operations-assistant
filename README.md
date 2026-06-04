# Week 14 Operations Assistant

## MCP server (FastMCP)

Install dependencies:

```bash
uv pip install -r requirements.txt
```

Run (stdio, default for MCP clients):

```bash
fastmcp run mcp_server/server.py
```

Run (HTTP, for local testing):

```bash
fastmcp run mcp_server/server.py --transport http --port 8765
```

Inspect tools / call dummy `ping` tool:

```bash
fastmcp inspect mcp_server/server.py:mcp
fastmcp call --server-spec http://127.0.0.1:8765/mcp --target ping
```
