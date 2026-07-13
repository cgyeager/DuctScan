"""LLM provider abstraction.

The RAG/agentic layer talks to an ``LLMProvider`` interface so the concrete
backend (direct Anthropic API for local dev, AWS Bedrock in production) is
swappable via configuration, not code changes.

TODO(llm): implement both providers and the RAG plumbing in a later phase.
"""

import os
from abc import ABC, abstractmethod

from app.schemas import ChatRequest, ChatResponse


class LLMProvider(ABC):
    """Interface every LLM backend must implement."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Answer a chat turn (eventually: grounded in analysis results via RAG)."""
        ...


class DirectAPIProvider(LLMProvider):
    """Talks to the Anthropic API directly. Intended for local development.

    TODO(llm): implement using the ``anthropic`` SDK (add it to pyproject when you
    start): read the API key from env, build the message list from
    ``request.history`` + ``request.message``, call the API, return the reply.
    """

    async def chat(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError("DirectAPIProvider.chat: implement direct API call")


class BedrockProvider(LLMProvider):
    """Talks to AWS Bedrock. Intended for the deployed environment.

    TODO(llm): implement using ``boto3``/``anthropic[bedrock]`` in the AWS phase.
    """

    async def chat(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError("BedrockProvider.chat: implement Bedrock call")


def get_provider() -> LLMProvider:
    """Select the provider from the ``LLM_PROVIDER`` env var (default: direct)."""
    name = os.environ.get("LLM_PROVIDER", "direct").lower()
    if name == "bedrock":
        return BedrockProvider()
    return DirectAPIProvider()
