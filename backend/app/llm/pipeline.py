
"""
Ingestion pipeline orchestrator.

Wires together: parse → chunk → embed → store.

The chunking step delegates to ingestion/chunking.py
"""

import logging
from pathlib import Path

from app.db.db_client import ChunkStore
from app.llm.chunking import chunk_document
from app.llm.embedder import embed_documents
from app.llm.parser import parse_pdf, parse_txt

logger = logging.getLogger(__name__)


def ingest_document(*, file_path: str, document_id: str) -> dict:
    """
    Run the full ingestion pipeline for a single document.

    Steps:
      1. Parse  — extract text from each page (pdfplumber + OCR fallback)
      2. Chunk  — split into retrievable pieces
      3. Embed  — encode chunks with Voyage AI
      4. Store  — bulk-insert into Supabase chunks table

    Args:
        file_path:   Absolute path to the document on disk.
        document_id: Stable identifier for this document (used in citations).

    Returns:
        {"chunks_processed": int}

    Raises:
        NotImplementedError if chunk_document() is not yet implemented.
        FileNotFoundError   if the file does not exist.
    """
    path = Path(file_path)
    logger.info("Ingesting document %s (id=%s)", path.name, document_id)

    # ── Parse ─────────────────────────────────────────────────────────
    if ".txt" in file_path:
        pages = parse_txt(file_path)
    else:
        pages = parse_pdf(file_path)
    logger.info("Parsed %d pages", len(pages))

    # ── Chunk  ─────────────────────────────────
    chunks = chunk_document(
        pages=pages,
        document_id=document_id,
        source_path=str(path),
    )
    logger.info("Produced %d chunks", len(chunks))

    if not chunks:
        logger.warning("No chunks produced for document %s — nothing stored", document_id)
        return {"chunks_processed": 0}

    # ── Embed ─────────────────────────────────────────────────────────
    texts = [c["content"] for c in chunks]
    embeddings = embed_documents(texts)

    if len(chunks) != len(embeddings):
        raise RuntimeError(
            f"Embedding count mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings"
        )

    logger.info("Embedded %d chunks", len(embeddings))

    # ── Store ─────────────────────────────────────────────────────────
    store = ChunkStore()

    # Delete any previous version of this document before re-ingesting
    store.delete_document(document_id)

    rows = [
        {
            "document_id": chunk["document_id"],
            "content": chunk["content"],
            "embedding": embedding,
            "source_path": chunk["source_path"],
            "page": chunk.get("page"),
            "section": chunk.get("section"),
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]
    store.insert_chunk_batch(rows)
    logger.info("Stored %d chunks for document %s", len(rows), document_id)

    return {"chunks_processed": len(rows)}

