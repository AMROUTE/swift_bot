# Swift Bot RAG Backend

Zero-dependency local backend for the first RAG MVP.

## Run

Install dependencies:

```sh
Backend/.venv/bin/python -m pip install -r Backend/requirements.txt
```

Current MVP backend uses only Python standard library modules, so this is a no-op for now.

```sh
Backend/.venv/bin/python Backend/app.py
```

Server starts at:

```txt
http://127.0.0.1:8000
```

If `8000` is busy:

```sh
RAG_PORT=8001 Backend/.venv/bin/python Backend/app.py
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

### Ask

```sh
curl \
  -H "Content-Type: application/json" \
  -d '{"question":"这个知识库 MVP 应该先做哪些功能？"}' \
  http://127.0.0.1:8000/ask
```

### Delete document

```sh
curl -X DELETE "http://127.0.0.1:8000/documents?id=<document_id>"
```

## Storage

Documents persist to:

```txt
Backend/data/documents.json
```
