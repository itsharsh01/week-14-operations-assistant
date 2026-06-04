# Week 14 Operations Assistant

Small electronics store operations assistant: FastMCP server + CrewAI crew for single-query workflows.

**Requires Python 3.12** (CrewAI/chromadb are not compatible with 3.14).

## Crew (single query)

Copy `.env.example` to `.env` and set `GROQ_API_KEY`.

```bash
python run_crew.py "Which products need reordering?"
```

Default query runs if you omit the argument. Full traces go to `traces/`; reports to `reports/`.

## Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Ask a question in the UI to see the answer, **proof** (which files/tools produced each fact), and a per-tool execution trace.

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
