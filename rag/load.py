"""Load local markdown/text documents for indexing."""
from __future__ import annotations

from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
SUPPORTED = {".md", ".txt"}


def load_documents(data_dir: Path | str | None = None) -> list[tuple[str, str]]:
    """Return list of (source_name, text)."""
    root = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    if not root.is_dir():
        raise FileNotFoundError(f"Sample data directory not found: {root}")
    docs: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                docs.append((path.name, text))
    if not docs:
        raise FileNotFoundError(f"No .md/.txt files under {root}")
    return docs
