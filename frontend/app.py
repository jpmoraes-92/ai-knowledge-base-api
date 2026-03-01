import streamlit as st
import requests
import uuid
import time

# Configuração da página
st.set_page_config(page_title="AI Knowledge Base", page_icon="🧠", layout="wide")
API_URL = "http://api:8000/api/v1"

# ==========================================
# 1. GESTÃO DE ESTADO (SESSÃO)
# ==========================================
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou a IA do seu repositório. Faça o upload de um PDF para começarmos!"}]

def clear_chat():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Memória limpa! Faça upload de um PDF ou faça sua pergunta."}]

def login(username, password):
    try:
        response = requests.post(f"{API_URL}/auth/login", data={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.user_id = data["user_id"]
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com o servidor da API: {e}")

def logout():
    st.session_state.access_token = None
    st.session_state.user_id = None
    clear_chat()
    st.rerun()

# ==========================================
# 2. INTERFACE DE LOGIN (Deslogado)
# ==========================================
if not st.session_state.access_token:
    st.title("🔐 Acesso Restrito - RAG Enterprise")
    st.markdown("Por favor, autentique-se para acessar o seu cofre de documentos.")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted and username and password:
            with st.spinner("Autenticando..."):
                login(username, password)

# ==========================================
# 3. INTERFACE PRINCIPAL (Logado)
# ==========================================
else:
    # O "Crachá" que vamos mostrar para o Backend em todas as chamadas
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1150/1150592.png", width=80)
        st.subheader(f"👤 {st.session_state.user_id}")
        if st.button("🚪 Sair", use_container_width=True):
            logout()
            
        if st.button("🧹 Nova Conversa (Limpar Memória)", use_container_width=True):
            clear_chat()
            st.rerun()
            
        st.markdown("---")
        st.subheader("📄 Upload de Documento")
        uploaded_file = st.file_uploader("Arraste seu PDF aqui", type=["pdf"])
        
        # LÓGICA DO BACKGROUND TASK (ISSUE 2)
        if st.button("Processar em Background", use_container_width=True):
            if uploaded_file is not None:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {"title": uploaded_file.name, "source": "streamlit"}
                
                response = requests.post(f"{API_URL}/documents/pdf", headers=headers, files=files, data=data)
                
                if response.status_code == 202:
                    task_id = response.json()["task_id"]
                    progress_text = "Enviado para fila. Processando..."
                    progress_bar = st.progress(0, text=progress_text)
                    
                    # O Polling: Fica perguntando a cada 1 segundo se a IA já terminou de ler
                    while True:
                        status_res = requests.get(f"{API_URL}/documents/status/{task_id}", headers=headers)
                        if status_res.status_code == 200:
                            status = status_res.json()["status"]
                            if status == "Completed":
                                progress_bar.progress(100, text="✅ Leitura concluída e salva no FAISS!")
                                break
                            elif status.startswith("Failed"):
                                st.error(f"❌ Erro no processamento: {status}")
                                break
                            else:
                                time.sleep(1) # Espera 1 segundo para perguntar de novo
                else:
                    st.error("Falha ao enviar documento.")
            else:
                st.warning("Selecione um arquivo primeiro.")
                
        st.markdown("---")
        st.caption(f"🆔 Sessão: `{st.session_state.session_id[:8]}`")

    # --- ÁREA CENTRAL (CHAT COM STREAMING - ISSUE 3) ---
    st.title("🧠 Chatbot Inteligente com RAG")
    
    # Desenha as mensagens antigas
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Recebe a pergunta nova
    if prompt := st.chat_input("Ex: Qual o resumo do documento?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            payload = {
                "question": prompt,
                "top_k": 3, 
                "session_id": st.session_state.session_id
            }
            
            try:
                # O segredo do streaming: stream=True
                response = requests.post(f"{API_URL}/questions/stream", headers=headers, json=payload, stream=True)
                
                if response.status_code == 200:
                    # Função geradora para ler os pedaços (chunks) que chegam da API
                    def stream_generator():
                        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                yield chunk

                    # A Mágica do Streamlit: Ele cuida de digitar na tela!
                    full_answer = st.write_stream(stream_generator())
                    
                    # Salva a resposta completa na memória do Chat
                    st.session_state.messages.append({"role": "assistant", "content": full_answer})
                elif response.status_code == 401:
                    st.error("Sessão expirada. Faça login novamente.")
                else:
                    st.error("Erro ao gerar resposta.")
            except Exception as e:
                st.error(f"O Backend parece estar fora do ar. {e}")