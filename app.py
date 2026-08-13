import streamlit as st
import os
import json
import requests
import time
import urllib.parse
import re

# ==========================================
# 1. IMPORTAÇÃO E VERIFICAÇÃO DE MÓDULOS
# ==========================================
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
except ImportError:
    HAS_MIC = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT = True
except ImportError:
    HAS_YT = False


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE & ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="AI DO PABLO · Supreme Core",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilo CSS Adaptativo (Light Mode e Dark Mode)
st.markdown("""
    <style>
    .stApp {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .hero-title {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #00c6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: clamp(28px, 5vw, 44px);
        font-weight: 800;
        text-align: center;
        letter-spacing: -1.5px;
        margin-top: -10px;
        margin-bottom: 5px;
    }
    
    .hero-subtitle {
        color: #64748b;
        font-size: clamp(12px, 3vw, 15px);
        text-align: center;
        margin-bottom: 25px;
        font-weight: 500;
    }
    
    div[data-testid="stChatMessage"] {
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.12) !important;
        transition: all 0.2s ease-in-out;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background: rgba(59, 130, 246, 0.06) !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background: rgba(128, 128, 128, 0.04) !important;
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35) !important;
    }
    
    div[data-testid="stChatInput"] {
        padding-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · YouTube & Web · Imagens HD · Multi-Sessão</p>', unsafe_allow_html=True)
st.markdown("---")


# ==========================================
# 3. GERENCIADOR DE CHATS E DADOS LOCAIS
# ==========================================
BANCO_USUARIOS = "usuarios_cadastrados.json"

def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    try:
        usuarios = carregar_usuarios()
        usuarios[novo_usuario] = nova_senha
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def get_chats_file(usuario):
    return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        with open(get_chats_file(usuario), "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


# ==========================================
# 4. FERRAMENTAS DE INTEGRAÇÃO (WEB & YOUTUBE)
# ==========================================
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    if not HAS_BS4 or len(termo.strip()) < 3:
        return ""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(termo)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = []
            for a in soup.find_all("a", class_="result__snippet")[:3]:
                texto = a.get_text().strip()
                if texto:
                    snippets.append(f"• {texto}")
            return "\n".join(snippets)
    except Exception:
        pass
    return ""

def extrair_texto_youtube(url):
    if not HAS_YT:
        return ""
    try:
        video_id = None
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        elif "youtube.com/watch" in url:
            video_id = url.split("v=")[1].split("&")[0].split("?")[0]
            
        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en', 'es'])
            texto_yt = " ".join([t['text'] for t in transcript])
            return texto_yt[:2500]
    except Exception:
        return "[Não foi possível carregar as legendas automáticas deste vídeo.]"
    return ""

def gerar_url_midia(prompt_texto, tipo="imagem"):
    encoded_prompt = urllib.parse.quote(prompt_texto)
    seed = int(time.time())
    largura, altura = 1024, 1024
    prompt_lc = prompt_texto.lower()
    
    if "1920x1080" in prompt_lc or "widescreen" in prompt_lc or "hd" in prompt_lc:
        largura, altura = 1280, 720
    elif "portrait" in prompt_lc or "celular" in prompt_lc or "vertical" in prompt_lc:
        largura, altura = 720, 1280
        
    modelo = "flux" if tipo == "imagem" else "turbo"
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width={largura}&height={altura}&model={modelo}&nologo=true"


# ==========================================
# 5. CÉREBRO DA AI DO PABLO
# ==========================================
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    link_yt = "youtube.com" in prompt_usuario or "youtu.be" in prompt_usuario
    contexto_yt = extrair_texto_youtube(prompt_usuario) if link_yt else ""
    contexto_web = pesquisar_na_web(prompt_usuario) if not contexto_yt else ""

    sys_prompt = (
        "Você é a AI DO PABLO, uma inteligência artificial suprema, altamente inteligente e prestativa.\n"
        "Responda sempre em português brasileiro de forma completa e clara."
    )
    if contexto_yt:
        sys_prompt += f"\n\n[CONTEÚDO DO VÍDEO DO YOUTUBE]:\n{contexto_yt}"
    elif contexto_web:
        sys_prompt += f"\n\n[INFORMAÇÕES DA WEB]:\n{contexto_web}"

    # MOTOR DUCKDUCKGO (100% Grátis, Sem Chave, Sem Erro 402)
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Accept": "text/event-stream",
            "x-vqd-accept": "1"
        })

        # 1. Pega o token temporário de acesso livre
        res_status = session.get("https://duckduckgo.com/duckchat/v1/status", timeout=5)
        vqd = res_status.headers.get("x-vqd-4")

        if vqd:
            # 2. Envia a pergunta
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": f"{sys_prompt}\n\nUsuário: {prompt_usuario}"}
                ]
            }
            headers_chat = {
                "Content-Type": "application/json",
                "x-vqd-4": vqd
            }
            res_chat = session.post("https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers_chat, timeout=12)

            if res_chat.status_code == 200:
                texto_resposta = ""
                for line in res_chat.text.split("\n"):
                    if line.startswith("data: "):
                        chunk = line.replace("data: ", "").strip()
                        if chunk != "[DONE]":
                            try:
                                data = json.loads(chunk)
                                if "message" in data:
                                    texto_resposta += data["message"]
                            except Exception:
                                pass
                if texto_resposta.strip():
                    return texto_resposta.strip()

    except Exception as e:
        pass

    # Backup com Busca Web caso o servidor pisque
    if contexto_web:
        return f"### 🌐 AI DO PABLO (Resultados da Pesquisa Web):\n\n{contexto_web}"
    
    return f"Recebi seu comando sobre **'{prompt_usuario}'**! Pode me mandar mais detalhes para eu te ajudar?"

# ==========================================
# 6. CONTROLE DE SESSÃO E PAINEL LATERAL
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = True

if "usuario_atual" not in st.session_state or not st.session_state.usuario_atual:
    st.session_state.usuario_atual = "admin"

if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"

mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

# Menu Lateral (Sidebar)
st.sidebar.title("🛸 PAINEL DE CONTROLE")

operador_nome = str(st.session_state.get("usuario_atual") or "admin").upper()
st.sidebar.write(f"Operador: **{operador_nome}**")

if HAS_MIC:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Entrada de Voz")
    mic_recorder(start_prompt="🔊 Gravar Áudio", stop_prompt="⏹️ Enviar Áudio", key='gravador_chamada', use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Minhas Conversas")

lista_de_chats = list(conversas_usuario.keys())
chat_escolhido = st.sidebar.selectbox(
    "Selecionar Conversa:",
    lista_de_chats,
    index=lista_de_chats.index(st.session_state.chat_selecionado)
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input("Novo Chat:", key="new_chat_input", placeholder="Nome do chat...").strip()
if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
    if novo_nome_chat and novo_nome_chat not in conversas_usuario:
        conversas_usuario[novo_nome_chat] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.session_state.chat_selecionado = novo_nome_chat
        st.rerun()

st.sidebar.markdown("---")

if st.session_state.chat_selecionado != "Chat Principal":
    if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True):
        del conversas_usuario[st.session_state.chat_selecionado]
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

if st.sidebar.button("🗑️ Limpar Mensagens", use_container_width=True):
    conversas_usuario[st.session_state.chat_selecionado] = []
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    st.rerun()


# ==========================================
# 7. EXIBIÇÃO DE CHAT E INPUTS
# ==========================================
for message in mensagens_atuais:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Imagem gerada pela AI DO PABLO")
        elif message.get("type") == "video":
            st.image(message["content"], caption="Mídia gerada pela AI DO PABLO")
        else:
            st.markdown(message["content"])

texto_input = st.chat_input("Pergunte algo, peça imagens ou cole um link do YouTube...")

if texto_input:
    conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": texto_input})
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    
    with st.chat_message("user"):
        st.markdown(texto_input)

    prompt_minusculo = texto_input.lower()
    comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de", "imagem de"])
    comando_video = any(cmd in prompt_minusculo for cmd in ["crie um video", "gere um video", "video de"])

    with st.chat_message("assistant"):
        if comando_video:
            with st.spinner("🎬 Gerando mídia visual..."):
                url_gerada = gerar_url_midia(texto_input, tipo="video")
                st.image(url_gerada, caption="Mídia gerada pela AI DO PABLO")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "video", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

        elif comando_imagem:
            with st.spinner("🎨 Pintando sua imagem em HD..."):
                url_gerada = gerar_url_midia(texto_input, tipo="imagem")
                st.image(url_gerada, caption="Imagem gerada pela AI DO PABLO")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

        else:
            with st.spinner("⚡ AI DO PABLO está pensando..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], texto_input)
                st.markdown(resposta_texto)
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
