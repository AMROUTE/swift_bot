from sqlalchemy.exc import OperationalError

import swift_rag.main as main_module
from swift_rag.config import MAX_UPLOAD_BYTES


def test_health(client, monkeypatch):
    monkeypatch.setattr(main_module, "check_database", lambda: (True, None))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["database"]["ok"] is True


def test_health_reports_database_down(client, monkeypatch):
    monkeypatch.setattr(main_module, "check_database", lambda: (False, "OperationalError"))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["database"]["error"] == "OperationalError"


def test_database_errors_return_503(client, monkeypatch):
    def broken_list_documents(session):
        raise OperationalError("select 1", {}, Exception("connection refused"))

    monkeypatch.setattr(main_module, "list_documents", broken_list_documents)

    response = client.get("/documents")

    assert response.status_code == 503
    assert response.json()["error"] == "database unavailable"


def test_upload_list_ask_and_delete(client, db_session):
    upload = client.post(
        "/documents",
        files={"files": ("guide.md", b"npm run dev starts the local Vite server.", "text/markdown")},
    )
    assert upload.status_code == 201
    created = upload.json()["created"]
    assert created[0]["chunks"] == 1

    listing = client.get("/documents")
    assert listing.status_code == 200
    assert listing.json()["stats"]["documents"] == 1
    assert listing.json()["stats"]["chunks"] == 1

    answer = client.post("/ask", json={"question": "npm run dev"})
    assert answer.status_code == 200
    payload = answer.json()
    assert payload["citations"]
    assert "npm run dev" in payload["citations"][0]["text"]

    deleted = client.delete(f"/documents?id={created[0]['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == 1
    assert client.get("/documents").json()["stats"]["chunks"] == 0


def test_upload_rejects_unsupported_file(client):
    response = client.post(
        "/documents",
        files={"files": ("notes.pdf", b"%PDF", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["skipped"][0]["reason"] == "unsupported extension"


def test_upload_rejects_oversized_file(client):
    response = client.post(
        "/documents",
        files={"files": ("large.txt", b"x" * (MAX_UPLOAD_BYTES + 1), "text/plain")},
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]["skipped"][0]["reason"]


def test_delete_all(client):
    client.post("/documents", files={"files": ("one.md", b"one text", "text/markdown")})
    client.post("/documents", files={"files": ("two.md", b"two text", "text/markdown")})

    deleted = client.delete("/documents/all")

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == 2
    assert client.get("/documents").json()["stats"]["documents"] == 0
