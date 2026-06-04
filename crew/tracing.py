"""Execution tracing and proof extraction for the operations crew."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crewai.events.base_event_listener import BaseEventListener
from crewai.events.event_bus import CrewAIEventsBus
from crewai.events.types.crew_events import (
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
)
from crewai.events.types.mcp_events import (
    MCPToolExecutionCompletedEvent,
    MCPToolExecutionFailedEvent,
    MCPToolExecutionStartedEvent,
)
from crewai.events.types.task_events import TaskCompletedEvent, TaskStartedEvent
from crewai.events.types.tool_usage_events import (
    ToolUsageErrorEvent,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)

from crew.config import DOCUMENTS_DIR, INVENTORY_PATH, PROJECT_ROOT

INVENTORY_SOURCE = str(INVENTORY_PATH.relative_to(PROJECT_ROOT))
DOCUMENTS_SOURCE = str(DOCUMENTS_DIR.relative_to(PROJECT_ROOT)) + "/"


def infer_tool_name(tool_name: str, tool_args: dict[str, Any] | None) -> str:
    """Map CrewAI/MCP adapter names to our canonical tool names."""
    args = tool_args or {}
    lower = tool_name.lower()
    if "search" in lower or "query" in args:
        return "search_documents"
    if "read" in lower and "filename" in args:
        return "read_documents"
    if "filename" in args:
        return "read_documents"
    if "low_stock" in args or "inventory" in lower:
        return "read_inventory"
    if "title" in args and "content" in args:
        return "save_report"
    if "check" in args and len(args) <= 1:
        return "ping"
    return tool_name


def extract_sources(tool: str, args: dict[str, Any], result: Any) -> list[dict[str, str]]:
    """Build proof sources from a tool call."""
    sources: list[dict[str, str]] = []
    parsed = _parse_result(result)

    if tool == "read_inventory":
        sources.append(
            {
                "type": "inventory_csv",
                "path": INVENTORY_SOURCE,
                "detail": f"Loaded {len(parsed.get('items', []))} product row(s)",
            }
        )
    elif tool == "search_documents":
        query = args.get("query", parsed.get("query", ""))
        sources.append(
            {
                "type": "document_search",
                "path": DOCUMENTS_SOURCE,
                "detail": f"Keyword search: {query}",
            }
        )
        for match in parsed.get("matches", []):
            fname = match.get("filename", "")
            if fname:
                sources.append(
                    {
                        "type": "document_match",
                        "path": f"{DOCUMENTS_SOURCE}{fname}",
                        "detail": match.get("snippet", "")[:200],
                    }
                )
    elif tool == "read_documents":
        fname = args.get("filename") or parsed.get("filename", "")
        path = f"{DOCUMENTS_SOURCE}{Path(str(fname)).name}"
        sources.append(
            {
                "type": "document_full",
                "path": path,
                "detail": (parsed.get("content", "") or "")[:300],
            }
        )
    elif tool == "save_report":
        path = parsed.get("path") or parsed.get("filename", "")
        if path:
            rel = _relative_path(str(path))
            sources.append(
                {
                    "type": "report_file",
                    "path": rel,
                    "detail": parsed.get("message", "Report saved"),
                }
            )
    return sources


def _parse_result(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        text = result.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        if "result" in text and "{" in text:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
    return {"raw": str(result)[:2000]}


def _relative_path(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return path


class TraceCollector:
    """Collects crew and MCP events for dashboard display."""

    def __init__(self, query: str, trace_id: str) -> None:
        self.query = query
        self.trace_id = trace_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.events: list[dict[str, Any]] = []
        self.tool_calls: list[dict[str, Any]] = []
        self.tasks: list[dict[str, Any]] = []
        self._pending_tools: dict[str, dict[str, Any]] = {}
        self.mcp_log_path: Path | None = None

    def set_mcp_log_path(self, path: Path) -> None:
        self.mcp_log_path = path

    def add_event(self, kind: str, payload: dict[str, Any]) -> None:
        self.events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "kind": kind,
                **payload,
            }
        )

    def merge_mcp_log(self) -> None:
        if not self.mcp_log_path or not self.mcp_log_path.is_file():
            return
        for line in self.mcp_log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            tool = entry["tool"]
            args = entry.get("args", {})
            result = entry.get("result", {})
            call = {
                "tool": tool,
                "args": args,
                "result": result,
                "status": "completed",
                "agent_role": None,
                "duration_ms": None,
                "sources": extract_sources(tool, args, result),
                "logged_at": entry.get("timestamp"),
                "source_channel": "mcp_server",
            }
            if not any(
                c["tool"] == tool
                and c.get("args") == args
                and c.get("result") == result
                for c in self.tool_calls
            ):
                self.tool_calls.append(call)

    def build_proof(self) -> list[dict[str, Any]]:
        proof: list[dict[str, Any]] = []
        for call in self.tool_calls:
            for src in call.get("sources", []):
                proof.append(
                    {
                        "tool": call["tool"],
                        "source_type": src["type"],
                        "path": src["path"],
                        "detail": src.get("detail", ""),
                    }
                )
        return proof

    def dedupe_tool_calls(self) -> list[dict[str, Any]]:
        """Keep one entry per tool+args (prefer mcp_server log over crew events)."""
        order = {"mcp_server": 0, "crewai_mcp_event": 1, "crewai_tool_usage": 2}
        seen: dict[tuple[str, str], dict[str, Any]] = {}
        for call in self.tool_calls:
            key = (call["tool"], json.dumps(call.get("args", {}), sort_keys=True))
            existing = seen.get(key)
            if existing is None:
                seen[key] = call
                continue
            prev_rank = order.get(existing.get("source_channel", ""), 99)
            new_rank = order.get(call.get("source_channel", ""), 99)
            if new_rank < prev_rank:
                seen[key] = call
        return list(seen.values())

    def to_dict(
        self,
        answer: str,
        raw_result: str,
        report_path: str | None = None,
    ) -> dict[str, Any]:
        self.merge_mcp_log()
        self.tool_calls = self.dedupe_tool_calls()
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "answer": answer,
            "raw_result": raw_result,
            "report_path": report_path,
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "tasks": self.tasks,
            "tool_calls": self.tool_calls,
            "events": self.events,
            "proof": self.build_proof(),
        }


class DashboardTraceListener(BaseEventListener):
    """CrewAI event listener that feeds TraceCollector."""

    def __init__(self, collector: TraceCollector) -> None:
        self.collector = collector
        super().__init__()

    def setup_listeners(self, bus: CrewAIEventsBus) -> None:
        c = self.collector

        @bus.on(CrewKickoffStartedEvent)
        def _crew_start(_: Any, event: CrewKickoffStartedEvent) -> None:
            c.add_event("crew_started", {"crew_name": getattr(event, "crew_name", "crew")})

        @bus.on(CrewKickoffCompletedEvent)
        def _crew_done(_: Any, event: CrewKickoffCompletedEvent) -> None:
            c.add_event("crew_completed", {"output": str(getattr(event, "output", ""))[:500]})

        @bus.on(CrewKickoffFailedEvent)
        def _crew_fail(_: Any, event: CrewKickoffFailedEvent) -> None:
            c.add_event("crew_failed", {"error": str(getattr(event, "error", ""))})

        @bus.on(TaskStartedEvent)
        def _task_start(_: Any, event: TaskStartedEvent) -> None:
            c.add_event(
                "task_started",
                {
                    "task_name": event.task_name,
                    "agent_role": event.agent_role,
                },
            )

        @bus.on(TaskCompletedEvent)
        def _task_done(_: Any, event: TaskCompletedEvent) -> None:
            output = str(event.output.raw) if event.output else ""
            entry = {
                "task_name": event.task_name,
                "agent_role": event.agent_role,
                "output": output,
            }
            c.tasks.append(entry)
            c.add_event("task_completed", {"task_name": event.task_name, "agent_role": event.agent_role})

        @bus.on(MCPToolExecutionStartedEvent)
        def _mcp_start(_: Any, event: MCPToolExecutionStartedEvent) -> None:
            tool = infer_tool_name(event.tool_name, event.tool_args)
            key = f"{tool}:{json.dumps(event.tool_args or {}, sort_keys=True)}"
            c._pending_tools[key] = {
                "tool": tool,
                "raw_tool_name": event.tool_name,
                "args": event.tool_args or {},
                "agent_role": event.agent_role,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            c.add_event(
                "tool_started",
                {"tool": tool, "args": event.tool_args, "agent_role": event.agent_role},
            )

        @bus.on(MCPToolExecutionCompletedEvent)
        def _mcp_done(_: Any, event: MCPToolExecutionCompletedEvent) -> None:
            tool = infer_tool_name(event.tool_name, event.tool_args)
            key = f"{tool}:{json.dumps(event.tool_args or {}, sort_keys=True)}"
            pending = c._pending_tools.pop(key, {})
            result = event.result
            call = {
                "tool": tool,
                "raw_tool_name": event.tool_name,
                "args": event.tool_args or {},
                "result": _parse_result(result),
                "status": "completed",
                "agent_role": event.agent_role or pending.get("agent_role"),
                "duration_ms": event.execution_duration_ms,
                "sources": extract_sources(tool, event.tool_args or {}, result),
                "source_channel": "crewai_mcp_event",
            }
            c.tool_calls.append(call)
            c.add_event("tool_completed", {"tool": tool, "status": "completed"})

        @bus.on(MCPToolExecutionFailedEvent)
        def _mcp_fail(_: Any, event: MCPToolExecutionFailedEvent) -> None:
            tool = infer_tool_name(event.tool_name, event.tool_args)
            c.tool_calls.append(
                {
                    "tool": tool,
                    "args": event.tool_args or {},
                    "status": "failed",
                    "error": event.error,
                    "agent_role": event.agent_role,
                }
            )
            c.add_event("tool_failed", {"tool": tool, "error": event.error})

        @bus.on(ToolUsageStartedEvent)
        def _tool_start(_: Any, event: ToolUsageStartedEvent) -> None:
            tool = infer_tool_name(event.tool_name, _args_dict(event.tool_args))
            c.add_event(
                "tool_usage_started",
                {"tool": tool, "args": event.tool_args, "agent_role": event.agent_role},
            )

        @bus.on(ToolUsageFinishedEvent)
        def _tool_done(_: Any, event: ToolUsageFinishedEvent) -> None:
            args = _args_dict(event.tool_args)
            tool = infer_tool_name(event.tool_name, args)
            if any(
                tc["tool"] == tool
                and tc.get("args") == args
                and tc.get("status") == "completed"
                for tc in c.tool_calls
            ):
                return
            call = {
                "tool": tool,
                "raw_tool_name": event.tool_name,
                "args": args,
                "result": _parse_result(event.output),
                "status": "completed",
                "agent_role": event.agent_role,
                "from_cache": event.from_cache,
                "sources": extract_sources(tool, args, event.output),
                "source_channel": "crewai_tool_usage",
            }
            c.tool_calls.append(call)

        @bus.on(ToolUsageErrorEvent)
        def _tool_err(_: Any, event: ToolUsageErrorEvent) -> None:
            tool = infer_tool_name(event.tool_name, _args_dict(event.tool_args))
            c.add_event("tool_error", {"tool": tool, "error": str(event.error)})


def _args_dict(tool_args: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(tool_args, dict):
        return tool_args
    if isinstance(tool_args, str):
        try:
            return json.loads(tool_args)
        except json.JSONDecodeError:
            return {"raw": tool_args}
    return {}


def extract_answer_from_tasks(tasks: list[dict[str, Any]]) -> str:
    """Prefer analysis task output; fall back to last non-report task."""
    for task in tasks:
        name = (task.get("task_name") or "").lower()
        if name == "analysis" or "analyst" in name:
            return task.get("output", "")
    for task in reversed(tasks):
        name = (task.get("task_name") or "").lower()
        if name != "report" and task.get("output"):
            return task.get("output", "")
    return tasks[-1].get("output", "") if tasks else ""


def find_report_path(collector: TraceCollector) -> str | None:
    for call in reversed(collector.tool_calls):
        if call.get("tool") == "save_report":
            parsed = call.get("result") or {}
            path = parsed.get("path") or parsed.get("filename")
            if path:
                return _relative_path(str(path))
    return None
