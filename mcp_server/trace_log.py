"""Append-only MCP tool trace log (used when OPS_TRACE_PATH is set)."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def log_tool_call(tool_name: str, args: dict[str, Any], result: Any) -> None:
    path = os.getenv("OPS_TRACE_PATH")
    if not path:
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "args": args,
        "result": _serialize(result),
        "source": "mcp_server",
    }
    trace_path = Path(path)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return str(value)
