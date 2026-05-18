from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import check_database, get_session
from .rag import (
    build_answer,
    create_document,
    delete_all_documents,
    delete_document,
    document_summary,
    list_documents,
    retrieve,
    validate_upload,
)


class AskRequest(BaseModel):
    question: str


app = FastAPI(title="Swift Bot RAG", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
def database_error_handler(request: Request, error: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "database unavailable",
            "detail": "Postgres is unavailable. Start it with `docker compose up -d postgres`.",
        },
    )


@app.get("/health")
def health() -> dict:
    database_ok, database_error = check_database()

    return {
        "ok": database_ok,
        "service": "swift-bot-rag",
        "time": datetime.now(timezone.utc).isoformat(),
        "database": {
            "ok": database_ok,
            "error": database_error,
        },
    }


@app.get("/documents")
def get_documents(session: Session = Depends(get_session)) -> dict:
    return list_documents(session)


@app.post("/documents", status_code=201)
async def post_documents(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
) -> dict:
    created = []
    skipped = []

    for file in files:
        filename = Path(file.filename or "").name
        raw = await file.read()
        reason = validate_upload(filename, raw)
        if reason:
            skipped.append({"name": filename, "reason": reason})
            continue

        document = create_document(session, filename, raw)
        created.append(document_summary(document))

    if not created and skipped:
        session.rollback()
        raise HTTPException(status_code=400, detail={"skipped": skipped})

    session.commit()
    return {"created": created, "skipped": skipped}


@app.delete("/documents/all")
def delete_documents_all(session: Session = Depends(get_session)) -> dict:
    deleted = delete_all_documents(session)
    session.commit()
    return {"deleted": deleted}


@app.delete("/documents")
def delete_documents(id: str, session: Session = Depends(get_session)) -> dict:
    deleted = delete_document(session, id)
    session.commit()
    return {"deleted": deleted, "id": id}


@app.post("/ask")
def post_ask(payload: AskRequest, session: Session = Depends(get_session)) -> dict:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    sources = retrieve(session, question)
    return {"question": question, **build_answer(question, sources)}
