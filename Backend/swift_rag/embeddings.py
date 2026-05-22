from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from .config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, OPENAI_API_KEY


def embeddings_configured() -> bool:
    return bool(OPENAI_API_KEY)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [text.strip() for text in texts]
    if not cleaned:
        return []
    if not embeddings_configured():
        raise RuntimeError("OPENAI_API_KEY is required for embeddings")

    response = get_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=cleaned,
        encoding_format="float",
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"
