"""Pydantic schemas for MCP tool inputs and outputs."""

from pydantic import BaseModel, Field


class DocumentMatch(BaseModel):
    """A document matched by search."""

    filename: str = Field(description="Document filename (e.g. reorder_policy.txt)")
    snippet: str = Field(description="Short excerpt showing why the document matched")
    score: int = Field(description="Relevance score (higher is more relevant)")


class SearchDocumentsInput(BaseModel):
    """Input for search_documents."""

    query: str = Field(description="Keywords to find relevant documents")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of results")


class SearchDocumentsOutput(BaseModel):
    """Output from search_documents."""

    query: str
    matches: list[DocumentMatch]


class ReadDocumentInput(BaseModel):
    """Input for read_documents."""

    filename: str = Field(
        description="Document filename in data/documents (e.g. reorder_policy.txt)"
    )


class ReadDocumentOutput(BaseModel):
    """Output from read_documents."""

    filename: str
    content: str


class InventoryItem(BaseModel):
    """One row from inventory.csv."""

    product_name: str
    current_stock: int
    reorder_level: int
    supplier: str


class ReadInventoryInput(BaseModel):
    """Input for read_inventory."""

    low_stock_only: bool = Field(
        default=False,
        description="If true, return only products at or below reorder level",
    )


class ReadInventoryOutput(BaseModel):
    """Output from read_inventory."""

    items: list[InventoryItem]
    low_stock_count: int = Field(
        description="Number of products at or below reorder level"
    )


class SaveReportInput(BaseModel):
    """Input for save_report."""

    title: str = Field(description="Short title used in the saved filename")
    content: str = Field(description="Full report text to save")


class SaveReportOutput(BaseModel):
    """Output from save_report."""

    filename: str
    path: str
    message: str
