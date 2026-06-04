"""CrewAI agents wired to the operations inventory MCP server."""

from crewai import Agent
from crewai.mcp.filters import create_static_tool_filter

from crew.config import get_groq_llm, mcp_stdio_server

RESEARCH_TOOLS = create_static_tool_filter(
    allowed_tool_names=["search_documents", "read_documents", "read_inventory"]
)
REPORT_TOOLS = create_static_tool_filter(allowed_tool_names=["save_report"])


def create_research_agent() -> Agent:
    return Agent(
        llm=get_groq_llm(),
        role="Inventory Research Specialist",
        goal="Gather inventory figures and relevant store documents for operations questions",
        backstory=(
            "You work at a small electronics store. You use MCP tools to read "
            "inventory.csv and search/read policy, product, and support documents. "
            "You collect facts only—no final recommendations yet."
        ),
        mcps=[mcp_stdio_server(tool_filter=RESEARCH_TOOLS)],
        verbose=True,
        allow_delegation=False,
    )


def create_analyst_agent() -> Agent:
    return Agent(
        llm=get_groq_llm(),
        role="Operations Analyst",
        goal="Answer operations questions clearly using research from the team",
        backstory=(
            "You interpret inventory and policy data for store managers. "
            "You cite document names and stock numbers in your answers."
        ),
        verbose=True,
        allow_delegation=False,
    )


def create_reporter_agent() -> Agent:
    return Agent(
        llm=get_groq_llm(),
        role="Report Writer",
        goal="Save a concise markdown report for the operations team",
        backstory=(
            "You turn finalized answers into markdown reports using the save_report MCP tool."
        ),
        mcps=[mcp_stdio_server(tool_filter=REPORT_TOOLS)],
        verbose=True,
        allow_delegation=False,
    )
