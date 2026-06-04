"""Shared paths and MCP server configuration for the crew."""

import os
import sys
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INVENTORY_PATH = DATA_DIR / "inventory.csv"
MCP_SERVER_SCRIPT = PROJECT_ROOT / "mcp_server" / "server.py"
TRACES_DIR = PROJECT_ROOT / "traces"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_QUERY = "Which products need reordering and which suppliers should be contacted?"
DEFAULT_GROQ_MODEL = "groq/llama-3.3-70b-versatile"


@lru_cache(maxsize=1)
def get_groq_llm():
    """Build CrewAI LLM backed by Groq (reads GROQ_API_KEY from environment)."""
    from crewai import LLM

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file before running the crew."
        )

    return LLM(
        model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        api_key=api_key,
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.2")),
    )


def python_executable() -> str:
    return os.environ.get("CREW_PYTHON", sys.executable)


def mcp_stdio_server(tool_filter=None):
    """Stdio MCP config for the local operations inventory server."""
    from crewai.mcp import MCPServerStdio

    kwargs = {
        "command": python_executable(),
        "args": [str(MCP_SERVER_SCRIPT)],
        "env": {**os.environ},
        "cwd": str(PROJECT_ROOT),
        "cache_tools_list": True,
    }
    if tool_filter is not None:
        kwargs["tool_filter"] = tool_filter
    return MCPServerStdio(**kwargs)
