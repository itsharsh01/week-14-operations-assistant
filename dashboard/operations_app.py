"""Operations Inventory Assistant — Streamlit UI (Week 14 project)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

TRACES_DIR = PROJECT_ROOT / "traces"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_trace_files() -> list[Path]:
    if not TRACES_DIR.is_dir():
        return []
    return sorted(TRACES_DIR.glob("crew_run_*.json"), reverse=True)


def load_trace(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_crew(query: str) -> dict:
    from crew.crew import run_query

    return run_query(query)


def render_proof(proof: list[dict]) -> None:
    if not proof:
        st.info("No source proof captured for this run.")
        return
    for i, item in enumerate(proof, start=1):
        with st.expander(f"{i}. {item.get('source_type', 'source')} — `{item.get('path', '')}`"):
            st.markdown(f"**Tool:** `{item.get('tool', '')}`")
            st.caption(item.get("detail", ""))


def render_tool_traces(tool_calls: list[dict]) -> None:
    if not tool_calls:
        st.info("No MCP tool calls recorded.")
        return
    for i, call in enumerate(tool_calls, start=1):
        status = call.get("status", "unknown")
        tool = call.get("tool", call.get("raw_tool_name", "tool"))
        icon = "✅" if status == "completed" else "❌"
        with st.expander(f"{icon} Step {i}: `{tool}` ({status})", expanded=i == 1):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Arguments**")
                st.json(call.get("args", {}))
            with col2:
                st.markdown("**Agent**")
                st.write(call.get("agent_role") or "—")
                if call.get("duration_ms"):
                    st.write(f"Duration: {call['duration_ms']:.0f} ms")
                if call.get("from_cache"):
                    st.caption("Result served from cache")

            st.markdown("**Result**")
            st.json(call.get("result", call.get("error", {})))

            sources = call.get("sources", [])
            if sources:
                st.markdown("**Proof sources from this tool**")
                for src in sources:
                    st.markdown(f"- `{src.get('path')}` — {src.get('detail', '')[:120]}")


def render_tasks(tasks: list[dict]) -> None:
    if not tasks:
        return
    st.subheader("Agent tasks")
    for i, task in enumerate(tasks, start=1):
        with st.expander(f"Task {i}: {task.get('agent_role', 'Agent')}"):
            st.markdown(f"**Name:** {task.get('task_name', '')}")
            st.markdown(task.get("output", ""))


def render_timeline(events: list[dict]) -> None:
    if not events:
        return
    st.subheader("Event timeline")
    for event in events:
        st.caption(
            f"`{event.get('timestamp', '')}` — **{event.get('kind', '')}** "
            f"{json.dumps({k: v for k, v in event.items() if k not in ('timestamp', 'kind')}, default=str)[:200]}"
        )


def main() -> None:
    st.set_page_config(
        page_title="Week 14 — Operations Assistant",
        page_icon="📦",
        layout="wide",
    )
    st.title("Operations Inventory Assistant")
    st.caption(
        f"Project: `{PROJECT_ROOT.name}` · MCP crew + proof traces · Port **8502**"
    )

    tab_ask, tab_history = st.tabs(["Ask", "History"])

    with tab_ask:
        query = st.text_area(
            "Your question",
            value="Which products need reordering and which suppliers should be contacted?",
            height=100,
        )
        run_btn = st.button("Run crew", type="primary")

        if run_btn and query.strip():
            with st.spinner("Running crew (MCP tools + agents)..."):
                try:
                    payload = run_crew(query.strip())
                    st.session_state["last_run"] = payload
                except Exception as exc:
                    st.error(str(exc))
                    st.stop()

        payload = st.session_state.get("last_run")
        if payload:
            st.success("Run completed")
            st.markdown("### Answer")
            st.markdown(payload.get("answer", ""))

            if payload.get("report_path"):
                report_file = PROJECT_ROOT / payload["report_path"]
                if report_file.is_file():
                    with st.expander("Saved report file"):
                        st.markdown(report_file.read_text(encoding="utf-8"))

            st.markdown("### Proof — where this came from")
            render_proof(payload.get("proof", []))

            st.markdown("### Tool execution trace")
            render_tool_traces(payload.get("tool_calls", []))

            with st.expander("Task outputs"):
                render_tasks(payload.get("tasks", []))

            with st.expander("Full event timeline"):
                render_timeline(payload.get("events", []))

            st.download_button(
                "Download trace JSON",
                data=json.dumps(payload, indent=2, default=str),
                file_name=f"crew_run_{payload.get('trace_id', 'trace')}.json",
                mime="application/json",
            )

    with tab_history:
        files = load_trace_files()
        if not files:
            st.info("No past runs yet.")
        else:
            labels = [f.name for f in files]
            choice = st.selectbox("Past run", labels)
            if choice:
                payload = load_trace(TRACES_DIR / choice)
                st.markdown("### Answer")
                st.markdown(payload.get("answer", ""))
                st.markdown("### Proof")
                render_proof(payload.get("proof", []))
                st.markdown("### Tool trace")
                render_tool_traces(payload.get("tool_calls", []))


if __name__ == "__main__":
    main()
