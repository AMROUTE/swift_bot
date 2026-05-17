from __future__ import annotations

import cgi
import json
import math
import os
import re
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


HOST = "127.0.0.1"
PORT = int(os.environ.get("RAG_PORT", "8000"))
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_PATH = DATA_DIR / "documents.json"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 160
TOP_K = 5

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

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".log"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DOCUMENTS_PATH.exists():
        DOCUMENTS_PATH.write_text("[]", encoding="utf-8")


def load_documents() -> list[dict]:
    ensure_store()
    try:
        return json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_documents(documents: list[dict]) -> None:
    ensure_store()
    DOCUMENTS_PATH.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))).strip()


def tokenize(text: str) -> list[str]:
    lower = text.lower()
    latin = re.findall(r"[a-z0-9_+-]{2,}", lower)
    cjk = re.findall(r"[\u4e00-\u9fff]{1,2}", lower)
    return [term for term in [*latin, *cjk] if term not in STOP_WORDS]


def make_chunks(document: dict) -> list[dict]:
    paragraphs = re.split(r"\n\s*\n", normalize_text(document["text"]))
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
            "id": f"{document['id']}-{index}",
            "doc_id": document["id"],
            "source": document["name"],
            "index": index + 1,
            "text": text,
            "terms": tokenize(text),
        }
        for index, text in enumerate(prepared)
    ]


def all_chunks(documents: list[dict]) -> list[dict]:
    return [chunk for document in documents for chunk in make_chunks(document)]


def score_chunk(chunk: dict, query_terms: list[str], chunks: list[dict]) -> float:
    if not query_terms:
        return 0

    frequencies: dict[str, int] = {}
    for term in chunk["terms"]:
        frequencies[term] = frequencies.get(term, 0) + 1

    unique_chunk_terms = set(chunk["terms"])
    unique_query_terms = set(query_terms)
    score = 0.0

    for term in unique_query_terms:
        tf = frequencies.get(term, 0)
        if not tf:
            continue

        docs_with_term = len([item for item in chunks if term in item["terms"]]) or 1
        idf = math.log((len(chunks) + 1) / docs_with_term)
        score += (1 + math.log(tf)) * (1 + idf)

    overlap = len([term for term in unique_query_terms if term in unique_chunk_terms])
    return score + overlap / math.sqrt(len(unique_chunk_terms) or 1)


def retrieve(question: str, documents: list[dict]) -> list[dict]:
    chunks = all_chunks(documents)
    query_terms = tokenize(question)
    scored = [
        {**chunk, "score": score_chunk(chunk, query_terms, chunks)}
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
        "answer": f"基于当前知识库，可以这样回答：\n\n" + "\n".join(lines),
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


def document_summary(document: dict) -> dict:
    return {
        "id": document["id"],
        "name": document["name"],
        "size": document["size"],
        "created_at": document["created_at"],
        "chunks": len(make_chunks(document)),
    }


class RagHandler(BaseHTTPRequestHandler):
    server_version = "SwiftBotRAG/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self.send_json({"ok": True, "service": "swift-bot-rag", "time": now_iso()})
            return

        if parsed.path == "/documents":
            documents = load_documents()
            self.send_json(
                {
                    "documents": [document_summary(document) for document in documents],
                    "stats": {
                        "documents": len(documents),
                        "chunks": len(all_chunks(documents)),
                        "characters": sum(len(document["text"]) for document in documents),
                    },
                }
            )
            return

        self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/documents":
            self.create_documents()
            return

        if parsed.path == "/ask":
            payload = self.read_json()
            question = str(payload.get("question", "")).strip()
            if not question:
                self.send_error_json(HTTPStatus.BAD_REQUEST, "question is required")
                return

            sources = retrieve(question, load_documents())
            self.send_json({"question": question, **build_answer(question, sources)})
            return

        self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/documents":
            self.send_error_json(HTTPStatus.NOT_FOUND, "Route not found")
            return

        document_id = parse_qs(parsed.query).get("id", [""])[0]
        if not document_id:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "id is required")
            return

        documents = load_documents()
        next_documents = [document for document in documents if document["id"] != document_id]
        save_documents(next_documents)
        self.send_json({"deleted": len(documents) - len(next_documents), "id": document_id})

    def create_documents(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "multipart/form-data is required")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )

        files = form["files"] if "files" in form else []
        if not isinstance(files, list):
            files = [files]

        documents = load_documents()
        created = []
        skipped = []

        for file_item in files:
            filename = Path(file_item.filename or "").name
            extension = Path(filename).suffix.lower()
            if extension not in ALLOWED_EXTENSIONS:
                skipped.append({"name": filename, "reason": "unsupported extension"})
                continue

            raw = file_item.file.read()
            text = normalize_text(raw.decode("utf-8", errors="replace"))
            document = {
                "id": str(uuid.uuid4()),
                "name": filename,
                "size": len(raw),
                "text": text,
                "created_at": now_iso(),
            }
            documents.insert(0, document)
            created.append(document_summary(document))

        save_documents(documents)
        self.send_json({"created": created, "skipped": skipped}, HTTPStatus.CREATED)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"error": message}, status)

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def run() -> None:
    ensure_store()
    server = ThreadingHTTPServer((HOST, PORT), RagHandler)
    print(f"Swift Bot RAG backend running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
