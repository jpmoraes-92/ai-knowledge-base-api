```markdown
# 🧠 AI Knowledge Base API (RAG Engine & Conversational Agent)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-passing-brightgreen?logo=pytest&logoColor=white)

Um motor de Inteligência Artificial completo construído em Python. Este microserviço atua como um **Agente Cognitivo** que utiliza a arquitetura **RAG (Retrieval-Augmented Generation)** para ler documentos (Textos e PDFs), armazenar vetores matemáticos e responder perguntas com base num contexto privado, possuindo memória de conversação.

---

## 🚀 Arquitetura e Tech Stack

* **Backend & Roteamento:** FastAPI (100% Assíncrono) e Uvicorn.
* **Banco de Dados de Metadados:** MongoDB (via Motor Async) para salvar dados de documentos, logs e histórico de conversas.
* **Vector Store:** FAISS (Facebook AI Similarity Search) para cálculo de Distância Euclidiana (L2) ultrarrápida.
* **LLM & Embeddings:** Integração com OpenAI API (`gpt-4o-mini` e `text-embedding-3-small`).
* **Processamento de Documentos:** PyMuPDF para extração nativa de PDFs digitais.
* **DevOps & Infraestrutura:** Docker e Docker Compose para orquestração de containers.

---

## 🎯 Diferenciais Técnicos e Padrões de Engenharia

1. **Padrão Factory (Inversão de Controle):** O sistema alterna nativamente entre o consumo real da API OpenAI e um **Mock Local** usando a variável `USE_MOCK`. Ideal para desenvolvimento local sem gerar custos de cloud.
2. **Memória Conversacional de Agente:** O endpoint de RAG aceita um `session_id`. O sistema recupera ativamente o histórico recente da conversa no MongoDB e injeta no prompt da IA, transformando uma API estática num Chatbot inteligente com contexto de longo prazo.
3. **Smart Chunking com Overlap (Janela Deslizante):** Quebra inteligente de textos longos em pedaços menores com sobreposição nas bordas, garantindo que o FAISS não perca o contexto de frases cortadas pela metade.
4. **Observabilidade (Tracing Middleware):** Middleware customizado que injeta IDs únicos de requisição (`X-Request-ID`) e latência (`X-Process-Time`) nos cabeçalhos HTTP e logs do terminal, facilitando o tracking de erros em produção.
5. **Analytics via Aggregation Pipeline:** Cálculos de tokens gastos e documentos mais acessados processados diretamente no motor do MongoDB para alta performance.
6. **Suíte de Testes Assíncronos:** Cobertura de testes de integração com `pytest` e `httpx`, simulando requisições reais sem afetar a base de produção.

---

## 🛠️ Como rodar o projeto (Docker)

A maneira mais recomendada de rodar a aplicação é utilizando o Docker Compose, que subirá automaticamente a API e o banco de dados MongoDB na mesma rede.

### 1. Configure as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto contendo as seguintes variáveis:

```env
MONGO_URI=mongodb://mongo:27017
DATABASE_NAME=ai_kb_db
OPENAI_API_KEY=sk-sua-chave-aqui
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
TOP_K=3
USE_MOCK=False # Mude para True se quiser rodar sem gastar créditos da OpenAI

```

### 2. Suba os Containers

Execute o comando na raiz do projeto:

```bash
docker compose up --build -d

```

A API estará disponível e documentada no Swagger UI através do endereço:
👉 **http://localhost:8000/docs**

Para acompanhar os logs e o Tracing de requisições em tempo real:

```bash
docker compose logs -f api

```

---

## 🧪 Como executar os Testes Automatizados

O projeto conta com uma suíte rigorosa de testes de integração rodando num loop de eventos isolado.

Para rodar (necessário ter o Python local configurado):

```bash
# Ative o ambiente virtual e rode:
pytest -v

```

---

## 📖 Exemplos de Uso (Endpoints Principais)

### 1. Ingestão de PDF (`POST /api/v1/documents/pdf`)

Faz o parse de um PDF, gera embeddings (1536 dimensões) e salva no MongoDB e no FAISS.

* **Body:** `multipart/form-data` contendo o arquivo e o título.

### 2. Consulta RAG com Memória (`POST /api/v1/questions`)

Faz uma pergunta ao documento, cruzando o RAG com o histórico de conversa.

```json
{
  "question": "Qual é o prazo para renovar a licença?",
  "top_k": 3,
  "session_id": "12345-abcde"
}

```

### 3. Analytics (`GET /api/v1/analytics/documents`)

Retorna os metadados gerenciais processados via Pipeline de Agregação no banco de dados.

---

*Desenvolvido como demonstração de excelência em Engenharia de Software Backend e Integração com IAs Generativas por Juliano Pereira de Moraes*

```