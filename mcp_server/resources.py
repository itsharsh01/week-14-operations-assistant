"""Data paths and file access helpers for the operations assistant."""

import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INVENTORY_PATH = DATA_DIR / "inventory.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"


def list_document_filenames() -> list[str]:
    if not DOCUMENTS_DIR.is_dir():
        return []
    return sorted(p.name for p in DOCUMENTS_DIR.glob("*.txt"))


def read_document_text(filename: str) -> str:
    path = _safe_document_path(filename)
    return path.read_text(encoding="utf-8")


def _safe_document_path(filename: str) -> Path:
    name = Path(filename).name
    if not name.endswith(".txt"):
        raise ValueError("Only .txt documents in data/documents are supported.")
    path = DOCUMENTS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {name}")
    return path


def search_documents(query: str, limit: int) -> list[tuple[str, str, int]]:
    """Return (filename, snippet, score) sorted by score descending."""
    terms = [t.lower() for t in re.split(r"\W+", query.strip()) if t]
    if not terms:
        return []

    results: list[tuple[str, str, int]] = []
    for filename in list_document_filenames():
        content = read_document_text(filename)
        lower_name = filename.lower()
        lower_content = content.lower()
        score = 0
        for term in terms:
            if term in lower_name:
                score += 3
            score += lower_content.count(term)

        if score > 0:
            snippet = _build_snippet(content, terms)
            results.append((filename, snippet, score))

    results.sort(key=lambda r: r[2], reverse=True)
    return results[:limit]


def _build_snippet(content: str, terms: list[str], max_len: int = 200) -> str:
    lower = content.lower()
    for term in terms:
        idx = lower.find(term)
        if idx >= 0:
            start = max(0, idx - 60)
            end = min(len(content), idx + max_len - 60)
            snippet = content[start:end].replace("\n", " ").strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            return snippet
    return content.replace("\n", " ").strip()[:max_len]


def load_inventory() -> list[dict[str, str]]:
    if not INVENTORY_PATH.is_file():
        raise FileNotFoundError(f"Inventory file not found: {INVENTORY_PATH}")
    with INVENTORY_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_report_file(title: str, content: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", title.strip().lower()).strip("_") or "report"
    existing = {p.stem for p in REPORTS_DIR.glob("*.md")}
    base = slug
    n = 1
    while base in existing:
        base = f"{slug}_{n}"
        n += 1
    path = REPORTS_DIR / f"{base}.md"
    path.write_text(content, encoding="utf-8")
    return path
