"""MCP tools for the operations inventory assistant."""

from pathlib import Path

from fastmcp import FastMCP

if __package__:
    from . import resources
    from .schemas import (
        DocumentMatch,
        InventoryItem,
        ReadDocumentInput,
        ReadDocumentOutput,
        ReadInventoryOutput,
        SaveReportInput,
        SaveReportOutput,
        SearchDocumentsInput,
        SearchDocumentsOutput,
    )
else:
    import resources
    from schemas import (
        DocumentMatch,
        InventoryItem,
        ReadDocumentInput,
        ReadDocumentOutput,
        ReadInventoryOutput,
        SaveReportInput,
        SaveReportOutput,
        SearchDocumentsInput,
        SearchDocumentsOutput,
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all tools on the given FastMCP server instance."""

    @mcp.tool
    def ping() -> str:
        """Health check. Returns a short confirmation that the MCP server is running."""
        return "Operations Inventory MCP server is running."

    @mcp.tool
    def search_documents(query: str, limit: int = 5) -> SearchDocumentsOutput:
        """Find relevant policy, product, and support documents by keyword query."""
        params = SearchDocumentsInput(query=query, limit=limit)
        rows = resources.search_documents(params.query, params.limit)
        return SearchDocumentsOutput(
            query=params.query,
            matches=[
                DocumentMatch(filename=name, snippet=snippet, score=score)
                for name, snippet, score in rows
            ],
        )

    @mcp.tool
    def read_documents(filename: str) -> ReadDocumentOutput:
        """Read the full text of a document from data/documents."""
        params = ReadDocumentInput(filename=filename)
        try:
            content = resources.read_document_text(params.filename)
        except FileNotFoundError as e:
            raise ValueError(str(e)) from e
        except ValueError as e:
            raise ValueError(str(e)) from e
        return ReadDocumentOutput(
            filename=Path(params.filename).name,
            content=content,
        )

    @mcp.tool
    def read_inventory() -> ReadInventoryOutput:
        """Get structured inventory data from data/inventory.csv."""
        rows = resources.load_inventory()
        items = [
            InventoryItem(
                product_name=row["product_name"],
                current_stock=int(row["current_stock"]),
                reorder_level=int(row["reorder_level"]),
                supplier=row["supplier"],
            )
            for row in rows
        ]
        low_stock = sum(
            1 for item in items if item.current_stock <= item.reorder_level
        )
        return ReadInventoryOutput(items=items, low_stock_count=low_stock)

    @mcp.tool
    def save_report(title: str, content: str) -> SaveReportOutput:
        """Save an operations report to the reports/ directory as markdown."""
        params = SaveReportInput(title=title, content=content)
        path = resources.save_report_file(params.title, params.content)
        return SaveReportOutput(
            filename=path.name,
            path=str(path),
            message=f"Report saved to {path.name}",
        )
