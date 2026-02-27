import os

from ollama import AsyncClient

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:7b")  # or any model you have

async def generate_stream(messages: list, model: str = DEFAULT_MODEL):
    """
    Send a chat request to Ollama and yield response chunks.
    Messages should be in OpenAI format: [{"role": "user", "content": "..."}]
    """
    client = AsyncClient(host=OLLAMA_BASE_URL)
    async for chunk in await client.chat(model=model, messages=messages, stream=True):
        if chunk and "message" in chunk and "content" in chunk["message"]:
            yield chunk["message"]["content"]