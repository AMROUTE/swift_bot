from swift_rag.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("swift_rag.main:app", host="127.0.0.1", port=8000, reload=True)
