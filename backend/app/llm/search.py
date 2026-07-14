"""
Retrieval — embed a query and fetch the most similar chunks from Supabase.
"""

import logging

from app.core.config import settings
from app.db.db_client import ChunkStore
from app.llm.embedder import embed_query as _embed_query

logger = logging.getLogger(__name__)


def retrieve_chunks(
    *,
    query: str,
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """
    Embed a user query and retrieve the top-k most similar chunks.

    Args:
        query:     The user's question (plain text).
        top_k:     Max chunks to return. Defaults to settings.max_chunks_retrieved.
        threshold: Minimum cosine similarity to include. Defaults to
                   settings.similarity_threshold.

    Returns:
        list of chunk dicts ordered by descending similarity:
            {id, document_id, content, source_path, page, section, similarity}
        Returns [] when no chunks exceed the threshold.
    """
    top_k = top_k or settings.max_chunks_retrieved
    threshold = threshold if threshold is not None else settings.similarity_threshold

    logger.debug("Retrieving top-%d chunks for query: %.80s…", top_k, query)

    query_embedding = _embed_query(query)

    store = ChunkStore()
    chunks = store.similarity_search(
        query_embedding=query_embedding,
        top_k=top_k,
        threshold=threshold,
    )

    logger.info("Retrieved %d chunks (query=%.60s…)", len(chunks), query)
    return chunks
