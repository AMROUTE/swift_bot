# Swift Bot RAG Backend

FastAPI backend for the local RAG MVP. It stores documents and chunks in Postgres with pgvector enabled, while the MVP retrieval path still uses lightweight keyword/TF-IDF scoring.

## Setup

Install Python dependencies:

```sh
Backend/.venv/bin/python -m pip install -r Backend/requirements.txt
```

Copy environment defaults if needed:

```sh
cp .env.example .env
```

Start Postgres + pgvector:

```sh
docker compose up -d postgres
```

The container is exposed on host port `55432` to avoid conflicts with any local Postgres already using `5432`.

Run the API:

```sh
cd Backend
.venv/bin/uvicorn swift_rag.main:app --host 127.0.0.1 --port 8000 --reload
```

Server starts at:

```txt
http://127.0.0.1:8000
```

## API

### Health

```sh
curl http://127.0.0.1:8000/health
```

### List documents

```sh
curl http://127.0.0.1:8000/documents
```

### Upload documents

```sh
curl -F "files=@README.md" http://127.0.0.1:8000/documents
```

Supported MVP formats:

- `.txt`
- `.md`
- `.markdown`
- `.csv`
- `.json`
- `.log`

Single-file upload limit defaults to 5 MB.

### Ask

```sh
curl \
  -H "Content-Type: application/json" \
  -d '{"question":"这个知识库 MVP 应该先做哪些功能？"}' \
  http://127.0.0.1:8000/ask
```

### Delete one document

```sh
curl -X DELETE "http://127.0.0.1:8000/documents?id=<document_id>"
```

### Delete all documents

```sh
curl -X DELETE http://127.0.0.1:8000/documents/all
```

## Tests

```sh
cd Backend
.venv/bin/python -m pytest
```

## Storage

The old JSON store at `Backend/data/documents.json` is retained as a backup only. The new backend reads and writes Postgres.
