"""
    Domain exceptions for the LLM/RAG layer.
"""

class LLMError(Exception):
    """Base for all LLM-layer failures (lets callers catch the whole family)."""


class ProviderNotConfiguredError(LLMError):
    """A required API key / setting is missing."""

class RetrievalError(LLMError):
    """Embedding the query or querying the vector store failed."""