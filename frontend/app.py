import streamlit as st
import requests
import uuid

st.set_page_config(page_title="AI Knowledge Base", page_icon="🧠", layout="wide")

API_URL = "http://api:8000/api/v1"

# Função para resetar o chat
def clear_chat():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Memória limpa! Faça upload de um PDF ou faça sua pergunta."}]

if "session_id" not in st.session_state:
    clear_chat()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1150/1150592.png", width=80)
    st.title("Administração RAG")
    
    # NOVO: Botão para limpar a memória
    if st.button("🧹 Nova Conversa (Limpar Memória)", use_container_width=True):
        clear_chat()
        st.rerun()

    st.markdown("---")
    
    st.subheader("📄 Upload de Documento")
    uploaded_file = st.file_uploader("Arraste seu PDF aqui", type=["pdf"])
    
    if st.button("Processar e Salvar", use_container_width=True):
        if uploaded_file is not None:
            with st.spinner("Lendo PDF e gerando Embeddings..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {"title": uploaded_file.name, "source": "streamlit"}
                
                try:
                    response = requests.post(f"{API_URL}/documents/pdf", files=files, data=data)
                    if response.status_code == 201:
                        st.success("✅ PDF processado com sucesso!")
                    else:
                        st.error(f"Erro: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Falha na comunicação com a API: {e}")
        else:
            st.warning("Selecione um arquivo primeiro.")
            
    st.markdown("---")
    st.caption(f"🆔 Sessão: `{st.session_state.session_id[:8]}`")

# --- ÁREA CENTRAL (CHAT) ---
st.title("🧠 Chatbot Inteligente com RAG")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ex: Qual a pena para o crime de homicídio?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pesquisando em centenas de páginas..."):
            # UPGRADE: top_k aumentado para 10 para lidar com PDFs gigantes!
            payload = {
                "question": prompt + " (se for um termo jurídico, busque também por sinônimos legais no texto)",
                "top_k": 10, 
                "session_id": st.session_state.session_id
            }
            try:
                response = requests.post(f"{API_URL}/questions", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    tokens = data["tokens_used"]
                    latency = data["latency_ms"]
                    
                    st.markdown(answer)
                    st.caption(f"⚡ Tempo: {latency}ms | 🪙 Tokens: {tokens} | 📚 Fragmentos lidos: 10")
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Erro ao gerar resposta.")
            except Exception as e:
                st.error(f"O Backend parece estar fora do ar. {e}")