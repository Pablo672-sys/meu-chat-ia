import streamlit as st
import os
import json
import requests
import time
import urllib.parse
import re

# ==========================================
# 1. VERIFICAÇÃO E IMPORTAÇÃO DE MÓDULOS
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

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    import g4f
    HAS_G4F = True
except ImportError:
    HAS_G4F = False


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE & CSS
# ==========================================
st.set_page_config(
    page_title="AI DO PABLO · Supreme Core",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Estilos Globais */
    .stApp {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Cabeçalho Principal */
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
    
    /* Customização das Mensagens de Chat */
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
    
    /* Botões Customizados */
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
    
    /* Rodapé do Chat Input */
    div[data-testid="stChatInput"] {
        padding-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · YouTube & Web · Imagens HD · Multi-Sessão</p>', unsafe_allow_html=True)
st.markdown("---")


# ==========================================
# 3. BANCO DE DADOS LOCAL (USUÁRIOS E CHATS)
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
# 4. FERRAMENTAS DE PESQUISA & YOUTUBE
# ==========================================
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    if not HAS_BS4 or len(termo.strip()) < 3:
        return ""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(termo)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = []
            for a in soup.find_all("a", class_="result__snippet")[:3]:
                texto = a.get_text().strip()
                if texto:
                    snippets.append(texto)
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
        return "[Aviso: Não foi possível carregar as legendas automáticas deste vídeo.]"
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
# 5. MOTOR DA INTELIGÊNCIA SUPREMA (ROBUSTO)
# ==========================================
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    # Detecta se há link do YouTube ou necessidade de Web
    link_yt = "youtube.com" in prompt_usuario or "youtu.be" in prompt_usuario
    contexto_yt = extrair_texto_youtube(prompt_usuario) if link_yt else ""
    contexto_web = pesquisar_na_web(prompt_usuario) if not contexto_yt else ""
    
    dados_extras = ""
    if contexto_yt:
        dados_extras = f"\n\n[CONTEÚDO DO VÍDEO DO YOUTUBE]:\n{contexto_yt}"
    elif contexto_web:
        dados_extras = f"\n\n[INFORMAÇÕES ENCONTRADAS NA WEB]:\n{contexto_web}"

    sys_prompt = (
        "Você é a AI DO PABLO, uma IA suprema, muito inteligente, amigável e prestativa.\n"
        "Responda sempre em português brasileiro de forma completa e clara.\n"
        "Se houver dados de pesquisa web ou transcrição do YouTube abaixo, use-os para responder perfeitamente."
        f"{dados_extras}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }

    # ROTA 1: API POST do Pollinations (Com payload de histórico estruturado)
    try:
        msgs_payload = [{"role": "system", "content": sys_prompt}]
        for m in historico_mensagens[-3:]:
            if m.get("type") not in ["image", "video"]:
                msgs_payload.append({
                    "role": "assistant" if m["role"] == "assistant" else "user",
                    "content": str(m["content"])[:600]
                })
        msgs_payload.append({"role": "user", "content": str(prompt_usuario)})

        res = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": msgs_payload, "model": "openai", "seed": int(time.time())},
            headers=headers,
            timeout=12
        )
        if res.status_code == 200 and res.text and len(res.text.strip()) > 2:
            return res.text.strip()
    except Exception:
        pass

    # ROTA 2: API GET do Pollinations (Com prompt formatado limpo)
    try:
        prompt_completo = f"{sys_prompt}\n\nUsuário pergunta: {prompt_usuario}"
        prompt_encoded = urllib.parse.quote(prompt_completo[:1500], safe='')
        url_get = f"https://text.pollinations.ai/{prompt_encoded}"
        
        res_get = requests.get(url_get, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        if res_get.status_code == 200 and res_get.text and len(res_get.text.strip()) > 2:
            return res_get.text.strip()
    except Exception:
        pass

    # ROTA 3: API Reserva
    try:
        url_reserva = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_usuario[:500], safe='')}?system={urllib.parse.quote('Você é a AI DO PABLO', safe='')}"
        res_reserva = requests.get(url_reserva, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res_reserva.status_code == 200 and res_reserva.text and len(res_reserva.text.strip()) > 2:
            return res_reserva.text.strip()
    except Exception:
        pass

    return "A AI DO PABLO está processando muitas requisições no momento. Por favor, envie sua mensagem novamente!"


# ==========================================
# 6. CONTROLE DE SESSÃO E ESTADO
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = True

if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = "admin"

if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"


# ==========================================
# 7. PAINEL LATERAL (SIDEBAR) & CONTROLES
# ==========================================
conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"

mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

st.sidebar.title("🛸 PAINEL DE CONTROLE")
st.sidebar.write(f"Operador Conectado: **{st.session_state.usuario_atual.upper()}**")

if HAS_MIC:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Entrada de Voz")
    audio_chamada = mic_recorder(
        start_prompt="🔊 Gravar Áudio",
        stop_prompt="⏹️ Enviar para AI DO PABLO",
        key='gravador_chamada',
        use_container_width=True
    )

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

novo_nome_chat = st.sidebar.text_input("Novo Chat:", key="new_chat_input", placeholder="Ex: Projeto Python...").strip()
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
# 8. EXIBIÇÃO DE MENSAGENS NO CHAT
# ==========================================
for index, message in enumerate(mensagens_atuais):
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Imagem gerada pela AI DO PABLO")
        elif message.get("type") == "video":
            st.image(message["content"], caption="Mídia gerada pela AI DO PABLO")
        else:
            st.markdown(message["content"])


# ==========================================
# 9. ENTRADA DO USUÁRIO & PROCESSAMENTO
# ==========================================
prompt_final = None

# Captura via input de texto
texto_input = st.chat_input("Pergunte algo, peça imagens ou cole um link do YouTube...")
if texto_input:
    prompt_final = texto_input

# Captura via áudio (se disponível)
if HAS_MIC and 'audio_chamada' in locals() and audio_chamada:
    if audio_chamada.get('bytes'):
        prompt_final = "[Mensagem de Voz Recebida]"

# Processamento da entrada
if prompt_final:
    # 1. Adiciona a mensagem do usuário
    conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    
    with st.chat_message("user"):
        st.markdown(prompt_final)

    prompt_minusculo = prompt_final.lower()
    comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de", "imagem de"])
    comando_video = any(cmd in prompt_minusculo for cmd in ["crie um video", "gere um video", "video de"])

    # 2. Resposta da IA
    with st.chat_message("assistant"):
        if comando_video:
            with st.spinner("🎬 Gerando mídia visual..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="video")
                st.image(url_gerada, caption="Mídia gerada pela AI DO PABLO")
                conversas_usuario[st.session_state.chat_selecionado].append({
                    "role": "assistant",
                    "type": "video",
                    "content": url_gerada
                })
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

        elif comando_imagem:
            with st.spinner("🎨 Pintando sua imagem em HD..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="imagem")
                st.image(url_gerada, caption="Imagem gerada pela AI DO PABLO")
                conversas_usuario[st.session_state.chat_selecionado].append({
                    "role": "assistant",
                    "type": "image",
                    "content": url_gerada
                })
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

        else:
            with st.spinner("⚡ AI DO PABLO está pensando..."):
                resposta_texto = chamar_ia_suprema(
                    conversas_usuario[st.session_state.chat_selecionado],
                    prompt_final
                )
                st.markdown(resposta_texto)
                conversas_usuario[st.session_state.chat_selecionado].append({
                    "role": "assistant",
                    "content": resposta_texto
                })
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
