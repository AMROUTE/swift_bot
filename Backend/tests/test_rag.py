from swift_rag.models import Chunk
from swift_rag.embeddings import vector_literal
from swift_rag.rag import build_answer, make_chunk_payloads, normalize_text, retrieve, tokenize


def test_normalize_tokenize_and_chunk():
    text = "Hello   RAG\r\n\r\n\r\n知识库 检索"

    assert normalize_text(text) == "Hello RAG\n\n知识库 检索"
    assert "hello" in tokenize(text)
    assert "知识" in tokenize(text)

    chunks = make_chunk_payloads("doc-1", text)
    assert chunks[0]["id"] == "doc-1-0"
    assert chunks[0]["index"] == 1
    assert chunks[0]["terms"]


def test_retrieve_orders_matching_chunks(db_session, document_factory):
    document_factory("guide.md", "部署流程需要先运行 npm install，然后运行 npm run dev。")
    document_factory("other.md", "这里记录的是设计系统颜色和字体。")

    sources = retrieve(db_session, "npm run dev 怎么启动？")

    assert sources
    assert sources[0]["source"] == "guide.md"
    assert "npm run dev" in sources[0]["text"]


def test_build_answer_for_no_hits():
    answer = build_answer("不存在的问题", [])

    assert "没有找到足够依据" in answer["answer"]
    assert answer["citations"] == []


def test_build_answer_with_citations():
    source = {
        "id": "doc-1-0",
        "doc_id": "doc-1",
        "source": "guide.md",
        "index": 1,
        "text": "MVP 应该先支持上传文档、切块、检索、引用回答。",
        "score": 2.34567,
    }

    answer = build_answer("MVP 先做什么？", [source])

    assert "[1]" in answer["answer"]
    assert answer["citations"][0]["score"] == 2.3457


def test_vector_literal_formats_pgvector_input():
    assert vector_literal([0.1, -0.2, 3.0]) == "[0.1,-0.2,3.0]"
