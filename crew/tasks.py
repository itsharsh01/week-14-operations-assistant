"""CrewAI tasks for a single operations query."""

from crewai import Task

from crew.agents import (
    create_analyst_agent,
    create_reporter_agent,
    create_research_agent,
)


def create_tasks(query: str) -> tuple[Task, Task, Task]:
    researcher = create_research_agent()
    analyst = create_analyst_agent()
    reporter = create_reporter_agent()

    research_task = Task(
        name="research",
        description=(
            "Investigate this operations question: {query}\n\n"
            "Use MCP tools to:\n"
            "1. Call read_inventory for current stock levels\n"
            "2. Call search_documents with keywords from the question\n"
            "3. Call read_documents for the most relevant files\n\n"
            "Return structured notes: inventory rows, document excerpts, and file names."
        ),
        expected_output=(
            "Research notes with inventory table (product, stock, reorder level, supplier), "
            "relevant document filenames, and key quotes."
        ),
        agent=researcher,
    )

    analysis_task = Task(
        name="analysis",
        description=(
            "Using the research notes, answer this question: {query}\n\n"
            "Include which products need reordering, which suppliers to contact, "
            "applicable policies, and any risks mentioned in tickets or notes."
        ),
        expected_output=(
            "Clear answer with bullet points, cited document names, and actionable recommendations."
        ),
        agent=analyst,
        context=[research_task],
    )

    report_task = Task(
        name="report",
        description=(
            "Save a markdown report that answers: {query}\n\n"
            "Use save_report with a short title and full markdown content summarizing "
            "research and the final answer from prior tasks."
        ),
        expected_output=(
            "Confirmation of saved report including filename and path from save_report."
        ),
        agent=reporter,
        context=[research_task, analysis_task],
    )

    return research_task, analysis_task, report_task
