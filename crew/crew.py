"""Run the operations crew for a single query via the local MCP server."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from crew.config import DEFAULT_QUERY, PROJECT_ROOT, TRACES_DIR, get_groq_llm
from crew.tasks import create_tasks
from crew.tracing import (
    DashboardTraceListener,
    TraceCollector,
    extract_answer_from_tasks,
    find_report_path,
)

load_dotenv(PROJECT_ROOT / ".env")

# Enable CrewAI tracing for this project
os.environ.setdefault("CREWAI_TRACING_ENABLED", "true")


def build_crew(query: str, collector: TraceCollector):
    from crewai import Crew, Process
    from crewai.events.listeners.tracing.utils import set_suppress_tracing_messages

    set_suppress_tracing_messages(True)
    DashboardTraceListener(collector)

    research_task, analysis_task, report_task = create_tasks(query)

    return Crew(
        agents=[
            research_task.agent,
            analysis_task.agent,
            report_task.agent,
        ],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        llm=get_groq_llm(),
        verbose=True,
        memory=False,
        tracing=True,
    )


def run_query(query: str) -> dict:
    """Run the crew and return answer plus full execution trace."""
    if not query.strip():
        raise ValueError("Query must not be empty.")

    trace_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mcp_log = TRACES_DIR / f"mcp_tools_{trace_id}.jsonl"
    collector = TraceCollector(query=query, trace_id=trace_id)
    collector.set_mcp_log_path(mcp_log)

    os.environ["OPS_TRACE_PATH"] = str(mcp_log)

    try:
        crew = build_crew(query, collector)
        result = crew.kickoff(inputs={"query": query})
    finally:
        os.environ.pop("OPS_TRACE_PATH", None)

    raw_result = str(result)
    answer = extract_answer_from_tasks(collector.tasks) or raw_result
    report_path = find_report_path(collector)

    payload = collector.to_dict(
        answer=answer,
        raw_result=raw_result,
        report_path=report_path,
    )
    _save_trace(payload)
    return payload


def _save_trace(payload: dict) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"crew_run_{payload['trace_id']}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run operations crew for one question using the local MCP server."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=DEFAULT_QUERY,
        help="Operations question to answer",
    )
    args = parser.parse_args(argv)

    try:
        payload = run_query(args.query)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\n--- Crew result ---\n")
    print(payload.get("answer") or payload.get("raw_result"))
    if payload.get("report_path"):
        print(f"\nReport: {payload['report_path']}")
    print(f"\nTrace: traces/crew_run_{payload['trace_id']}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
