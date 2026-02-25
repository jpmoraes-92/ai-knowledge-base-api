```markdown
# 🧠 AI Knowledge Base API (RAG Engine)

Um backend de Inteligência Artificial para busca semântica e RAG (Retrieval-Augmented Generation), construído com princípios de Clean Architecture e foco em alta performance e escalabilidade.

## 🚀 Arquitetura e Tech Stack
* **FastAPI:** Camada HTTP, roteamento assíncrono e validação rigorosa (Pydantic v2).
* **MongoDB (Motor):** Armazenamento estruturado e persistência de metadados, chunks de texto e histórico de auditoria.
* **FAISS:** Vector Store in-memory para busca semântica ultrarrápida (Distância Euclidiana/L2).
* **OpenAI API:** Geração de Embeddings e processamento de LLM (pronto para produção, atualmente com injeção de Mock local para dev/testes).
* **Docker:** Orquestração do ambiente de banco de dados.

## 🎯 Diferenciais Técnicos (Por que este projeto é robusto?)
1. **Separação de Concerns (Vector vs Metadata):** Os embeddings pesados ficam no FAISS, enquanto o texto estruturado fica no MongoDB. A conexão é feita por um `vector_id` matemático.
2. **Analytics Avançado com Aggregation Pipeline:** Em vez de processar métricas no backend (Python), a API delega a carga para o MongoDB usando pipelines complexos (`$lookup`, `$unwind`, `$group`) para gerar relatórios de uso de tokens e frequência de acesso.
3. **Observabilidade e Provenance:** Toda resposta da IA é atrelada aos "chunks" originais recuperados e salva no banco de dados para auditoria futura e controle de alucinação.

## 🛠️ Como rodar o projeto localmente

1. Clone o repositório e ative seu ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate # ou .\venv\Scripts\activate no Windows

```

2. Instale as dependências:
```bash
pip install -r requirements.txt

```


3. Suba o MongoDB via Docker:
```bash
docker compose up -d

```


4. Crie um arquivo `.env` na raiz com as credenciais (veja `core/config.py` para as variáveis necessárias).
5. Inicie a aplicação:
```bash
uvicorn app.main:app --reload

```


6. Acesse a documentação Swagger em: `http://localhost:8000/docs`

```

---

### 🧭 Onde ir a partir daqui?

O projeto "v1" está finalizado. Você já pode subir pro GitHub e colocar no seu currículo! 

Se no futuro você quiser evoluir esse projeto para uma "v2" para aprender ainda mais, você pode:
1. **Persistir o FAISS:** Adicionar código para salvar o índice vetorial no disco (`faiss.write_index`) para a memória não sumir ao reiniciar.
2. **Colocar a Chave Real da OpenAI:** Para ver o LLM raciocinando de verdade sobre os seus documentos.
3. **Adicionar PDF Parsing:** Usar a biblioteca `PyMuPDF` para ler arquivos PDF na rota de ingestão em vez de texto puro.

Foi uma honra atuar como seu Tech Lead nesta jornada. Você programou muito bem. **Vai subir pro GitHub agora ou quer tirar alguma última dúvida sobre a arquitetura que criamos?**

```