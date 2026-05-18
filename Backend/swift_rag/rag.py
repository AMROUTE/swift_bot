from __future__ import annotations

import math
import re
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .config import ALLOWED_EXTENSIONS, CHUNK_OVERLAP, CHUNK_SIZE, MAX_UPLOAD_BYTES, TOP_K
from .models import Chunk, Document, utc_now


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "you",
    "are",
    "was",
    "from",
    "into",
    "have",
    "has",
    "what",
    "when",
    "where",
    "how",
    "why",
    "about",
    "请",
    "的",
    "了",
    "和",
    "是",
    "在",
    "我",
    "我们",
    "这个",
    "一下",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))).strip()


def tokenize(text: str) -> list[str]:
    lower = text.lower()
    latin = re.findall(r"[a-z0-9_+-]{2,}", lower)
    cjk = re.findall(r"[\u4e00-\u9fff]{1,2}", lower)
    return [term for term in [*latin, *cjk] if term not in STOP_WORDS]


def make_chunk_payloads(document_id: str, text: str) -> list[dict]:
    paragraphs = re.split(r"\n\s*\n", normalize_text(text))
    prepared: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        next_buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(next_buffer) <= CHUNK_SIZE:
            buffer = next_buffer
            continue

        if buffer:
            prepared.append(buffer)

        if len(paragraph) <= CHUNK_SIZE:
            buffer = paragraph
            continue

        step = CHUNK_SIZE - CHUNK_OVERLAP
        for start in range(0, len(paragraph), step):
            prepared.append(paragraph[start : start + CHUNK_SIZE])
        buffer = ""

    if buffer:
        prepared.append(buffer)

    return [
        {
            "id": f"{document_id}-{index}",
            "document_id": document_id,
            "index": index + 1,
            "text": chunk_text,
            "terms": tokenize(chunk_text),
        }
        for index, chunk_text in enumerate(prepared)
    ]


def document_summary(document: Document) -> dict:
    return {
        "id": document.id,
        "name": document.name,
        "size": document.size,
        "created_at": document.created_at.isoformat(),
        "chunks": len(document.chunks),
    }


def list_documents(session: Session) -> dict:
    documents = (
        session.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .order_by(Document.created_at.desc())
        )
        .scalars()
        .all()
    )
    chunk_count = session.scalar(select(func.count(Chunk.id))) or 0
    return {
        "documents": [document_summary(document) for document in documents],
        "stats": {
            "documents": len(documents),
            "chunks": chunk_count,
            "characters": sum(len(document.text) for document in documents),
        },
    }


def validate_upload(filename: str, raw: bytes) -> str | None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return "unsupported extension"
    if len(raw) > MAX_UPLOAD_BYTES:
        return f"file exceeds {MAX_UPLOAD_BYTES} bytes"
    return None


def create_document(session: Session, filename: str, raw: bytes) -> Document:
    text = normalize_text(raw.decode("utf-8", errors="replace"))
    document_id = str(uuid.uuid4())
    document = Document(
        id=document_id,
        name=Path(filename).name,
        size=len(raw),
        text=text,
        created_at=utc_now(),
    )
    document.chunks = [Chunk(**payload) for payload in make_chunk_payloads(document_id, text)]
    session.add(document)
    session.flush()
    return document


def delete_document(session: Session, document_id: str) -> int:
    document = session.get(Document, document_id)
    if document is None:
        return 0
    session.delete(document)
    return 1


def delete_all_documents(session: Session) -> int:
    documents = session.execute(select(Document).options(selectinload(Document.chunks))).scalars().all()
    total = len(documents)
    for document in documents:
        session.delete(document)
    return total


def score_chunk(chunk: Chunk, query_terms: list[str], chunks: list[Chunk]) -> float:
    if not query_terms:
        return 0.0

    frequencies: dict[str, int] = {}
    for term in chunk.terms:
        frequencies[term] = frequencies.get(term, 0) + 1

    unique_chunk_terms = set(chunk.terms)
    unique_query_terms = set(query_terms)
    score = 0.0

    for term in unique_query_terms:
        tf = frequencies.get(term, 0)
        if not tf:
            continue

        chunks_with_term = len([item for item in chunks if term in item.terms]) or 1
        idf = math.log((len(chunks) + 1) / chunks_with_term)
        score += (1 + math.log(tf)) * (1 + idf)

    overlap = len([term for term in unique_query_terms if term in unique_chunk_terms])
    return score + overlap / math.sqrt(len(unique_chunk_terms) or 1)


def retrieve(session: Session, question: str) -> list[dict]:
    chunks = (
        session.execute(
            select(Chunk)
            .options(selectinload(Chunk.document))
            .order_by(Chunk.document_id, Chunk.index)
        )
        .scalars()
        .all()
    )
    query_terms = tokenize(question)
    scored = [
        {
            "id": chunk.id,
            "doc_id": chunk.document_id,
            "source": chunk.document.name,
            "index": chunk.index,
            "text": chunk.text,
            "terms": chunk.terms,
            "score": score_chunk(chunk, query_terms, chunks),
        }
        for chunk in chunks
    ]
    return sorted([chunk for chunk in scored if chunk["score"] > 0], key=lambda item: item["score"], reverse=True)[
        :TOP_K
    ]


def build_answer(question: str, sources: list[dict]) -> dict:
    if not sources:
        return {
            "answer": "知识库里没有找到足够依据。可以上传更多文档，或换个更具体的问题。",
            "citations": [],
        }

    query_terms = set(tokenize(question))
    facts = []

    for source in sources:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[。！？.!?])\s+|\n+", source["text"])
            if sentence.strip()
        ]
        ranked = sorted(
            [
                {
                    "source": source,
                    "sentence": sentence,
                    "hits": len([term for term in tokenize(sentence) if term in query_terms]),
                }
                for sentence in sentences
            ],
            key=lambda item: item["hits"],
            reverse=True,
        )
        facts.extend([item for item in ranked if item["hits"] > 0][:2])

    if not facts:
        facts = [{"source": source, "sentence": source["text"][:220]} for source in sources[:3]]

    lines = [
        f"{index + 1}. {fact['sentence']} [{fact['source']['index']}]"
        for index, fact in enumerate(facts[:5])
    ]

    return {
        "answer": "基于当前知识库，可以这样回答：\n\n" + "\n".join(lines),
        "citations": [
            {
                "id": source["id"],
                "doc_id": source["doc_id"],
                "source": source["source"],
                "index": source["index"],
                "text": source["text"],
                "score": round(source["score"], 4),
            }
            for source in sources
        ],
    }
