"""LLM provider abstraction.

The RAG/agentic layer talks to an ``LLMProvider`` interface so the concrete
backend (direct Anthropic API for local dev, AWS Bedrock in production) is
swappable via configuration, not code changes.
"""

from abc import ABC, abstractmethod
from anthropic import AsyncAnthropic
from fastapi.concurrency import run_in_threadpool
from app.schemas import ChatRequest, ChatResponse
from app.core.config import settings
from app.schemas.models import ChatMessage
from app.llm.instruction import TOP_INSTRUCTION, BOTTOM_INSTRUCTION
from app.llm.search import retrieve_chunks
from app.llm.exceptions import ProviderNotConfiguredError, RetrievalError, LLMError


TOP_K_DEFAULT = 3

def _format_context(chunks: list[dict]) -> str:
    """
    Turn retrieved chunks into a labeled source list the model can cite.
        [Source 1: <section>, page <page>]
        <content>

        [Source 2: <section>, page <page>]
        <content>
    """
    
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        section = chunk["section"] or "Document"        # None-fallback you planned
        page = chunk["page"]
        label = f"[Source {i}: {section}, page {page}]" if page is not None else f"[Source {i}: {section}]"
        blocks.append(f"{label}\n{chunk['content']}")
    return "\n\n".join(blocks)



class LLMProvider(ABC):
    """Interface every LLM backend must implement."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Answer a chat turn (grounded in analysis results via RAG)."""
        ...


class DirectAPIProvider(LLMProvider):
    """Talks to the Anthropic API directly. Intended for local development.
    """
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ProviderNotConfiguredError("ANTHROPIC_API_KEY must be set in .env")
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(self, request: ChatRequest) -> ChatResponse:


        try:
            chunks = await run_in_threadpool(
                retrieve_chunks,
                query=request.message, 
                top_k=TOP_K_DEFAULT,
            )
        except LLMError:
            raise
        except Exception as exc:
            raise RetrievalError(f"chunk retrieval failed: {exc}") from exc

        if not chunks:
            pass

        context = _format_context(chunks)
        prompt = f"{TOP_INSTRUCTION}\n\nCONTEXT:\n{context}\n\n"

        prompt += "Message History Start\n"
        for h in request.history:
            prompt += h.role
            prompt += '\n'
            prompt += h.content
            prompt += '\n\n'
        prompt += "Message History End\n"

        if request.analysis:
            heights = request.analysis.m_profile.height_m
            m_units = request.analysis.m_profile.m_units
            ducts   = request.analysis.ducts

            prompt +=f"M-Profile:\nHeights\n{heights}\nM-Units\n{m_units}\n"
        
            prompt +="Ducts\n"
            for d in ducts:
                prompt += f"type:{d.type}, base(m):{d.base_height_m}, top(m):{d.top_height_m}, "
                prompt += f"thickness:{d.thickness_m}, strength(m-units):{d.strength_dm}"
            prompt += "\n\n"

        prompt +=f"QUESTION:\n{request.message}\n\n{BOTTOM_INSTRUCTION}"

        chat_message = ChatMessage(role="user", content=prompt)

        response = await self.client.messages.create(
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

