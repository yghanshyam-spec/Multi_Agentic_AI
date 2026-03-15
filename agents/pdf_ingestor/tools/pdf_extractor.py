"""agents/pdf_ingestor/tools/pdf_extractor.py — mock PDF extractor."""
from shared import new_id

class PDFExtractor:
    def extract(self, path: str) -> dict:
        return {"pages": [{"page": i+1, "text": f"Page {i+1} content from {path}."} for i in range(3)],
                "page_count": 3, "is_scanned": False}

class VectorStoreWriter:
    def __init__(self, config=None): self.config = config or {}
    def upsert(self, chunks: list) -> dict:
        return {"upserted": len(chunks), "skipped": 0, "errors": []}
