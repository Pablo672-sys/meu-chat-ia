import streamlit as st
import os
import json
import requests
import time

# --- IMPORTAÇÕES PROTEGIDAS ---
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
st.set_page_config(page_title="AI DO PABLO · Supreme Core", page_icon="🤖", layout="centered")

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
    }
    div[data-testid="stChatInput"] { padding-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Desbloqueada · Web & YouTube · Imagens HD</p>', unsafe_allow_html=True)
st.markdown("---")

# --- GERENCIAMENTO DE CHATS ---
def carregar_todos_chats(usuario):
    arquivo = f"chats_salvos_{usuario}.json"
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        with open(f"chats_salvos_{usuario}.json", "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception: pass

# --- PESQUISA WEB E YOUTUBE ---
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    if not HAS_BS4 or len(termo) > 100: return ""
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(termo)}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [a.get_text().strip() for a in soup.find_all("a", class_="result__snippet")[:3]]
            return "\n".join(snippets) if snippets else ""
    except Exception: pass
    return ""

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
            texto_yt = " ".join([t['text'] for t in transcript])
            return texto_yt[:4000] 
    except Exception:
        return "[Erro ao ler legendas do vídeo.]"
    return ""

def gerar_url_midia(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&model=flux&nologo=true"

# --- MOTOR SUPREMO (SEM CHAVE - FORÇANDO PROVEDORES) ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    contexto_yt = extrair_texto_youtube(prompt_usuario) if ("youtube.com" in prompt_usuario or "youtu.be" in prompt_usuario) else ""
    contexto_web = pesquisar_na_web(prompt_usuario) if not contexto_yt else ""
    
    dados_extras = ""
    if contexto_yt: dados_extras = f"\n[LEGENDA DO VÍDEO]:\n{contexto_yt}"
    elif contexto_web: dados_extras = f"\n[PESQUISA WEB]:\n{contexto_web}"

    instrucao = "Você é a AI DO PABLO. Responda em português de forma clara." + dados_extras
    
    mensagens_payload = [{"role": "system", "content": instrucao}]
    for msg in historico_mensagens[-2:]:
        if msg.get("type") not in ["image", "video"]:
            mensagens_payload.append({"role": msg["role"], "content": msg["content"][:1000]})
    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    # TENTATIVA 1: Forçar DuckDuckGo (Mais tolerante com o Render)
    if HAS_G4F:
        try:
            client = Client(provider=g4f.Provider.DuckDuckGo)
            response = client.chat.completions.create(model="gpt-4", messages=mensagens_payload)
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
        except Exception:
            pass

        # TENTATIVA 2: Forçar Blackbox
        try:
            client = Client(provider=g4f.Provider.Blackbox)
            response = client.chat.completions.create(model="gpt-4", messages=mensagens_payload)
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
        except Exception:
            pass

    # TENTATIVA 3: O Pollinations Básico
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        prompt_enc = requests.utils.quote(f"{instrucao}\n\nUsuário: {prompt_usuario}")
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}", headers=headers, timeout=15)
        if r.status_code == 200 and r.text.strip(): return r.text.strip()
    except Exception:
        pass

    return "⚠️ Ops! Os firewalls dos servidores barraram a gente de novo por estarmos sem chave. Manda mais uma vez!"

# --- INÍCIO DO APP ---
st.session_state.logado = True
st.session_state.usuario_atual = "admin"
if "chat_selecionado" not in st.session_state: st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

# --- MENU LATERAL ---
st.sidebar.title("🛸 PAINEL DE CONTROLE")
lista_de_chats = list(conversas_usuario.keys())
chat_escolhido = st.sidebar.selectbox("Selecionar Chat:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input("Criar Novo Chat:").strip()
if st.sidebar.button("➕ Novo Chat", use_container_width=True):
    if novo_nome_chat and novo_nome_chat not in conversas_usuario:
        conversas_usuario[novo_nome_chat] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.session_state.chat_selecionado = novo_nome_chat
        st.rerun()

if st.sidebar.button("🗑️ Limpar Mensagens", use_container_width=True):
    conversas_usuario[st.session_state.chat_selecionado] = []
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    st.rerun()

# --- RENDERIZAR MENSAGENS ---
for message in mensagens_atuais:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"])
        else:
            st.markdown(message["content"])

# --- INPUT DO USUÁRIO ---
prompt_final = st.chat_input("Pergunte algo ou cole um link do YouTube...")

if prompt_final:
    conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    
    prompt_minusculo = prompt_final.lower()
    comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])

    if comando_imagem:
        with st.spinner("🎨 Gerando imagem HD..."):
            url_gerada = gerar_url_midia(prompt_final)
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
    else:
        with st.spinner("⚡ Hackeando rotas livres..."):
            resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
        
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.rerun()
