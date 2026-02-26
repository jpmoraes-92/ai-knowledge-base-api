import pytest

async def test_health_check(client):
    """Garante que a API está de pé antes de tudo"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

async def test_upload_document_success(client):
    """Testa se o endpoint de ingestão de texto retorna 201 Created"""
    payload = {
        "title": "Doc Teste",
        "content": "Este é um teste automatizado com mais de dez caracteres. Prazo de 30 dias.",
        "source": "pytest"
    }
    response = await client.post("/api/v1/documents", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["total_chunks"] >= 1
    assert data["embedding_model"] == "text-embedding-3-small"

async def test_upload_pdf_invalid_format(client):
    """Testa se a API rejeita arquivos corrompidos ou falsos PDFs"""
    fake_pdf_bytes = b"Isso nao e um arquivo PDF valido"
    response = await client.post(
        "/api/v1/documents/pdf",
        data={"title": "Falso PDF", "source": "pytest"},
        files={"file": ("arquivo_falso.pdf", fake_pdf_bytes, "application/pdf")}
    )
    
    assert response.status_code == 400

async def test_ask_question_success(client):
    """Testa se o motor de busca RAG retorna 200 OK"""
    payload = {
        "question": "Qual é o prazo para renovar a licença?",
        "top_k": 3
    }
    response = await client.post("/api/v1/questions", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "tokens_used" in data
    assert isinstance(data["retrieved_chunks"], list)