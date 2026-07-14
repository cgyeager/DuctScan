"""
Embeddings client — wraps Voyage AI for document and query encoding.

Uses input_type="document" when embedding chunks (optimised for storage/retrieval)
and input_type="query" when embedding user queries (optimised for search).
"""

import logging

import voyageai

from app.core.config import settings

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
logger = logging.getLogger(__name__)

_client: voyageai.Client | None = None

VOYAGE_BATCH_SIZE = 128  # Voyage API max texts per request


_RETRYABLE = (Exception,)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,)
def _embed_batch(client, batch: list[str], model: str, input_type: str) -> list[list[float]]:
    """Embed ONE batch, with retry/backoff. This is the unit that retries."""
    result = client.embed(batch, model=model, input_type=input_type)
    return result.embeddings

def _get_client() -> voyageai.Client:
    global _client
    if _client is None:
        if not settings.voyage_api_key:
            raise RuntimeError("VOYAGE_API_KEY must be set in .env")
        _client = voyageai.Client(api_key=settings.voyage_api_key)
    return _client


def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of document chunks.

    Automatically batches to stay within the Voyage API's per-request limit.
    Returns embeddings in the same order as the input texts.
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), VOYAGE_BATCH_SIZE):
        batch = texts[i : i + VOYAGE_BATCH_SIZE]
        
        batch_embeddings = _embed_batch(client, batch, settings.voyage_model, "document")
        all_embeddings.extend(batch_embeddings)

    logger.debug("Embedded %d document chunks", len(texts))
    return all_embeddings


def embed_query(query: str) -> list[float]:
    """
    Embed a single user query for similarity search.

    Uses input_type='query' which Voyage optimises differently from documents.
    """
    if not query or not query.strip():
        raise ValueError("Cannot embed an empty query")

    client = _get_client()
    batch_embeddings = _embed_batch(client, [query], model=settings.voyage_model, input_type="query")
    return batch_embeddings[0]
