import fitz
import logging
import re
from fastapi import HTTPException
from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Limpa ruídos, cabeçalhos e rodapés inúteis do PDF antes de vetorizar"""
    
    # 1. Remove cabeçalhos exatos da sua apostila
    text = re.sub(r'(?i)DIREITO PENAL II', '', text)
    text = re.sub(r'(?i)Profª:\s*Ana Maria Duarte', '', text)
    
    # 2. Remove numeração de páginas (Ex: "Página 7", "Página 112")
    text = re.sub(r'(?i)Página\s*\d+', '', text)
    
    # 3. Remove aquele bloco chato de observação que poluiu o nosso log
    # Usamos re.DOTALL para a regex entender que o bloco pode ter quebras de linha no meio
    text = re.sub(r'(?i)Obs\.\s*:\s*Parte dos esquemas desta apostila.*?Curso\s*Semestral\s*\d{4}/\d\.', '', text, flags=re.DOTALL)
    
    # 4. Remove links/URLs de blogs que apareceram soltos no texto
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'\S+\.blogspot\.com\S*', '', text)
    
    # 5. Limpeza de formatação: 
    # Transforma 3 ou mais quebras de linha seguidas em apenas 2 (para não perder a noção de parágrafo)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Transforma múltiplos espaços em branco em um só
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def smart_chunker(text: str, chunk_size: int = 1000, overlap: int = 150):
    """
    Divide o texto em pedaços com um limite de caracteres, 
    garantindo uma sobreposição (overlap) e evitando cortar palavras ao meio.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Se chegamos no final do texto, pega o resto e encerra
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Procura o último espaço vazio ANTES do limite do chunk, 
        # para não fatiar uma palavra pela metade.
        last_space = text.rfind(' ', start, end)
        if last_space != -1 and last_space > start:
            end = last_space

        # Adiciona o chunk validado
        chunks.append(text[start:end].strip())

        # O INÍCIO DO PRÓXIMO CHUNK:
        # Volta o cursor no texto baseado no tamanho do overlap
        start = end - overlap
        
        # Como o overlap pode ter caído no meio de uma palavra, 
        # avançamos até o próximo espaço vazio.
        if start < text_length:
            first_space = text.find(' ', start, end)
            if first_space != -1:
                start = first_space + 1

    return [c for c in chunks if c] # Retorna removendo possíveis chunks vazios

class IngestionService:
    async def process_document(self, title: str, content: str, source: str, user_id: str):
        chunks = smart_chunker(content, chunk_size=1000, overlap=150)
        
        doc_id = await mongo_service.create_document(
            title=title, 
            source=source, 
            total_chunks=len(chunks), 
            embedding_model=settings.embedding_model,
            user_id=user_id # Passando para o Mongo
        )
        
        try:
            embeddings = await openai_service.get_embeddings(chunks)
        except Exception as e:
            logger.error(f"Erro na OpenAI: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Falha ao gerar embeddings: {str(e)}")
        
        for i, (text, vector) in enumerate(zip(chunks, embeddings)):
            vector_id = vector_service.add_vector(vector)
            await mongo_service.save_chunk(doc_id, i, text, vector_id, user_id) # Passando para o Mongo
            
        return {
            "document_id": doc_id,
            "total_chunks": len(chunks),
            "embedding_model": settings.embedding_model,
            "user_id": user_id
        }

    async def process_pdf(self, title: str, file_bytes: bytes, source: str, user_id: str):
        try:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            except Exception:
                raise ValueError("O arquivo enviado está corrompido ou não é um PDF válido.")
                
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"

            # 👇 A MÁGICA ACONTECE AQUI: Passamos a vassoura antes de salvar! 👇
            clean_full_text = clean_text(full_text)

            if not clean_full_text.strip():
                raise ValueError("O PDF não possui camada de texto digital ou ficou vazio após a limpeza.")

            logger.info(f"📄 PDF lido e higienizado com sucesso: {len(clean_full_text)} caracteres extraídos (antes: {len(full_text)}).")
            
            # Repassamos o texto limpo para a próxima etapa
            return await self.process_document(title=title, content=clean_full_text, source=source, user_id=user_id)

        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
ingestion_service = IngestionService()