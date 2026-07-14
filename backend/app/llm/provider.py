"""LLM provider abstraction.

The RAG/agentic layer talks to an ``LLMProvider`` interface so the concrete
backend (direct Anthropic API for local dev, AWS Bedrock in production) is
swappable via configuration, not code changes.

TODO(llm): implement both providers and the RAG plumbing in a later phase.
"""

import os
from abc import ABC, abstractmethod
from anthropic import Anthropic
from app.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.schemas.models import ChatMessage


class LLMProvider(ABC):
    """Interface every LLM backend must implement."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Answer a chat turn (grounded in analysis results via RAG)."""
        ...


class DirectAPIProvider(LLMProvider):
    """Talks to the Anthropic API directly. Intended for local development.

    TODO(llm): implement using the ``anthropic`` SDK (add it to pyproject when you
    start): read the API key from env, build the message list from
    ``request.history`` + ``request.message``, call the API, return the reply.
    """
    def __init__(self):
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY must be set in .env")
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        msg:str = request.message
        history: str = ''

        history += "Message History Start\n"
        for h in request.history:
            history += h.role
            history += '\n'
            history += h.content
            history += '\n\n'
        history += "Message History End\n"

        if request.analysis != None: 
            history += "Refractivity M Profile\n"
            history += "Heights:"
            history += str(request.analysis.m_profile.height_m)
            history += "m-units:"
            history += str(request.analysis.m_profile.m_units)
            history += "\n"
                
        history += "New Message\n"
        history += msg

        chat_message = ChatMessage(role="user", content=history)

        response = self.client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            messages=[{"role": chat_message.role, "content": chat_message.content}],
        )

        return ChatResponse(reply=response.content[0].text)

class BedrockProvider(LLMProvider):
    """Talks to AWS Bedrock. Intended for the deployed environment.

    TODO(llm): implement using ``boto3``/``anthropic[bedrock]`` in the AWS phase.
    """

    async def chat(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError("BedrockProvider.chat: implement Bedrock call")


def get_provider() -> LLMProvider:
    """Select the provider from the ``LLM_PROVIDER`` env var (default: direct)."""
    name = settings.llm_provider #os.environ.get("LLM_PROVIDER", "direct").lower()
    if name == "bedrock":
        return BedrockProvider()
    return DirectAPIProvider()

