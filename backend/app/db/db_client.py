
from typing import Optional
from supabase import Client, create_client
from app.core.config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("DB client settings not set.")
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client

class ChunkStore:
    """ Wrapper over DB 'chunks' table """

    def __init__(self) -> None:
        self._db = get_client

    def insert_chunk(
        self,
        *,
        document_id: str,
        content: str,
        embedding: list[float],
        source_path: str,
        page: Optional[int] = None,
        section: Optional[str] = None
    ) -> dict:
        """
        Insert one chunk row into the 'chunks' table.

        Returns the inserted row as a dict (includes the generated UUID).
        """        
        row = {
            "document_id": document_id,
            "content": content,
            "embedding": embedding,
            "source_path": source_path,
            "page": page,
            "section": section,
        }
        result = self._db.table("chunks").insert(row).execute()
        return result.data[0] if result.data else {}
    
    def insert_chunk_batch(self, rows: list[dict]) -> list[dict]:
        """
        Bulk-insert multiple chunk rows in one Supabase call.

        Each dict must contain the same keys as insert_chunk's parameters.
        """
        result = self._db.table("chunks").insert(rows).execute()
        return result.data or []
 
    def delete_document(self, document_id: str) -> None:
        """Remove all chunks associated with a document (useful for re-ingestion)."""
        self._db.table("chunks").delte().eq("document_id", document_id).execute()

    def similarity_search(
        self,
        *,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> list[dict]:
        """
        Call the match_chunks Postgres function (defined in db/schema.sql).

        Returns a list of chunk rows ordered by descending cosine similarity.
        Each row: {id, document_id, content, source_path, page, section, similarity}
        """
        result = self._db.rpc(
            "match_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k,
            },
        ).execute()
        return result.data or []
