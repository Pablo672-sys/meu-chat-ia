import streamlit as st
import os
import json
import requests
import time
import re

# --- IMPORTAÇÕES PROTEGIDAS (Evita crashes no Streamlit) ---
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

try:
    import g4f
    from g4f.client import Client
    HAS_G4F = True
except ImportError:
    HAS_G4F = False

# --- CONFIGURAÇÃO DA INTERFACE VISUAL ---
st.set_page_config(
    page_title="AI DO PABLO · Supreme Core",
    page_icon="🤖",
    layout="centered"
)

# --- CSS ADAPTATIVO (LIGHT / DARK) ---
st.markdown("""
    <style>
    .stApp { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    
    .hero-title {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #00c6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: clamp(28px, 5vw, 42px);
        font-weight: 800;
        text-align: center;
        letter-spacing: -1.5px;
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
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.1) !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background: rgba(59, 130, 246, 0.05) !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background: rgba(128, 128, 128, 0.03) !important;
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    div[data-testid="stChatInput"] { padding-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · YouTube & Web · Imagens HD</p>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

# --- GERENCIAMENTO DE USUÁRIOS E CHATS ---
def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    try:
        usuarios = carregar_usuarios()
        usuarios[novo_usuario] = nova_senha
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f: json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception: pass

def get_chats_indices_file(usuario): return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_indices_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        with open(get_chats_indices_file(usuario), "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception: pass

# --- PESQUISA WEB (DuckDuckGo) ---
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    if not HAS_BS4 or len(termo) > 100: return ""
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(termo)}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [a.get_text().strip() for a in soup.find_all("a", class_="result__snippet")[:2]]
            return "\n".join(snippets) if snippets else ""
    except Exception: pass
    return ""

# --- MOTOR YOUTUBE (Transcrição) ---
def extrair_texto_youtube(url):
    if not HAS_YT: return ""
    try:
        video_id = None
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/watch" in url:
            video_id = url.split("v=")[1].split("&")[0]
            
        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
            # Limita a leitura para não estourar a memória do servidor
            texto_yt = " ".join([t['text'] for t in transcript])
            return texto_yt[:3000] 
    except Exception:
        return "[Não foi possível ler as legendas desse vídeo.]"
    return ""

# --- GERADOR DE MÍDIA ---
def gerar_url_midia(prompt_texto, tipo="imagem"):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    largura, altura = 1024, 1024
    prompt_lc = prompt_texto.lower()
    
    if "1920x1080" in prompt_lc or "widescreen" in prompt_lc: largura, altura = 1280, 720
    elif "portrait" in prompt_lc or "celular" in prompt_lc: largura, altura = 720, 1280
        
    modelo = "flux" if tipo == "imagem" else "turbo"
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width={largura}&height={altura}&model={modelo}&nologo=true"

# --- MOTOR DE INTELIGÊNCIA SUPREMA (MEMÓRIA BLINDADA) ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    contexto_yt = extrair_texto_youtube(prompt_usuario) if ("youtube.com" in prompt_usuario or "youtu.be" in prompt_usuario) else ""
    contexto_web = pesquisar_na_web(prompt_usuario) if not contexto_yt else ""
    
    dados_extras = ""
    if contexto_yt: dados_extras = f"\n\n[RESUMO DO VÍDEO]:\n{contexto_yt}"
    elif contexto_web: dados_extras = f"\n\n[DADOS DA PESQUISA]:\n{contexto_web}"

    instrucao_sistema = "Você é a AI DO PABLO, uma IA suprema, brutalmente inteligente. Responda sempre em português." + dados_extras

    # Monta a memória de forma inteligente para não estourar o servidor
    mensagens_payload = [{"role": "system", "content": instrucao_sistema}]
    
    # Puxa APENAS as últimas 4 mensagens e limita o tamanho delas!
    for m in historico_mensagens[-4:]:
        if m.get("type") not in ["image", "video"]:
            texto_limpo = m["content"][:800] # Amassa mensagens antigas se forem muito grandes
            mensagens_payload.append({"role": m["role"], "content": texto_limpo})
            
    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    # TENTATIVA 1: Motor Oficial (Mais inteligente para lembrar do chat)
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": mensagens_payload,
            "model": "openai",
            "seed": int(time.time()),
            "json": False
        }
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass
        
    # TENTATIVA 2: Motor de Emergência (Se a memória encher, ele manda só a pergunta atual)
    try:
        prompt_emergencia = f"{instrucao_sistema}\nUsuário diz: {prompt_usuario}"[:2000]
        prompt_enc = requests.utils.quote(prompt_emergencia)
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}", timeout=20)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass

    return "A conexão deu uma engasgada aqui. Pode mandar a pergunta de novo, meu nobre?"

# --- ESTADO DA SESSÃO E LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state: st.session_state.chat_selecionado = "Chat Principal"

# Para ser rápido no Streamlit, auto-login ativo:
st.session_state.logado = True
st.session_state.usuario_atual = "admin"

# --- PAINEL PRINCIPAL ---
if st.session_state.logado:
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
    mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

    st.sidebar.title("🛸 PAINEL DE CONTROLE")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    
    if HAS_MIC:
        st.sidebar.markdown("---")
        audio_chamada = mic_recorder(start_prompt="🔊 Falar com a IA", stop_prompt="⏹️ Enviar Áudio", key='gravador_chamada', use_container_width=True)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Minhas Conversas")
    
    lista_de_chats = list(conversas_usuario.keys())
    chat_escolhido = st.sidebar.selectbox("Selecionar Chat:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()
        
    if st.session_state.chat_selecionado != "Chat Principal":
        if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True):
            del conversas_usuario[st.session_state.chat_selecionado]
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = "Chat Principal"
            st.rerun()
            
    novo_nome_chat = st.sidebar.text_input("Criar Novo Chat:", key="new_chat_name", placeholder="Nome da conversa...").strip()
    if st.sidebar.button("➕ Novo Chat", use_container_width=True):
        if novo_nome_chat and novo_nome_chat not in conversas_usuario:
            conversas_usuario[novo_nome_chat] = []
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = novo_nome_chat
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Limpar Mensagens", use_container_width=True):
        conversas_usuario[st.session_state.chat_selecionado] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.rerun()

    # --- Renderização das mensagens ---
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            elif message.get("type") == "video":
                st.image(message["content"], caption="Mídia Gerada")
            else:
                st.markdown(message["content"])

    # --- Input do Chat ---
    texto_input = st.chat_input("Pergunte algo, peça imagens ou cole um link do YouTube...")

    if texto_input:
        # Salva o que o usuário digitou e atualiza a tela
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": texto_input})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        
        with st.chat_message("user"):
            st.markdown(texto_input)
        
        prompt_minusculo = texto_input.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])
        comando_video = any(cmd in prompt_minusculo for cmd in ["crie um video", "gere um video"])

        with st.chat_message("assistant"):
            if comando_video:
                with st.spinner("🎬 Renderizando mídia..."):
                    url_gerada = gerar_url_midia(texto_input, tipo="video")
                    st.image(url_gerada)
                    conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "video", "content": url_gerada})
                    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            
            elif comando_imagem:
                with st.spinner("🎨 Gerando imagem HD..."):
                    url_gerada = gerar_url_midia(texto_input, tipo="imagem")
                    st.image(url_gerada)
                    conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            
            else:
                with st.spinner("⚡ Processando na Inteligência Suprema..."):
                    resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], texto_input)
                    st.markdown(resposta_texto)
                    conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
