import streamlit as st
import os
import json
import requests
import time

# --- IMPORTAÇÕES PROTEGIDAS (Evita crashes) ---
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
st.markdown('<p class="hero-subtitle">Inteligência Web & YouTube · Imagens HD · Visão Suprema</p>', unsafe_allow_html=True)
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
            texto_yt = " ".join([t['text'] for t in transcript])
            return texto_yt[:4000] # Limite para não estourar a memória
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

# --- MOTOR DE INTELIGÊNCIA SUPREMA (COM DISFARCE E MAIS TEMPO) ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    contexto_yt = extrair_texto_youtube(prompt_usuario) if ("youtube.com" in prompt_usuario or "youtu.be" in prompt_usuario) else ""
    contexto_web = pesquisar_na_web(prompt_usuario) if not contexto_yt else ""
    
    dados_extras = ""
    if contexto_yt: dados_extras = f"\n\n[TRANSCRIÇÃO DO YOUTUBE]:\n{contexto_yt}"
    elif contexto_web: dados_extras = f"\n\n[DADOS DA WEB]:\n{contexto_web}"

    instrucao_sistema = (
        "Você é a AI DO PABLO, uma IA suprema, brutalmente inteligente e criativa.\n"
        "REGRAS:\n"
        "1. Responda de forma didática e profunda.\n"
        "2. Se receber um texto do YouTube, resuma, analise e entregue o que o usuário pedir sobre o vídeo.\n"
        "3. Entregue códigos perfeitos e completos se solicitado."
        f"{dados_extras}"
    )

    mensagens_payload = [{"role": "system", "content": instrucao_sistema}]
    for m in historico_mensagens[-2:]:
        if m.get("type") not in ["image", "video"]:
            c_hist = m["content"][:1000] if len(m["content"]) > 1000 else m["content"]
            mensagens_payload.append({"role": m["role"], "content": c_hist})
    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    # Disfarce de Navegador para enganar o bloqueio
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/plain"
    }
    
    # TENTATIVA 1: POST com 30 segundos de paciência
    try:
        url = "https://text.pollinations.ai/"
        payload = {"messages": mensagens_payload, "model": "openai", "json": False, "seed": int(time.time())}
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass

    # TENTATIVA 2: GET com 30 segundos de paciência
    try:
        prompt_enc = requests.utils.quote(f"{instrucao_sistema}\n\nUsuário: {prompt_usuario}")
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}", headers=headers, timeout=30)
        if r.status_code == 200 and r.text.strip(): 
            return r.text.strip()
    except Exception:
        pass

    return "Ainda estou tentando furar o bloqueio do servidor da nuvem, a conexão aqui tá osso! Manda a pergunta mais uma vez?"

# --- ESTADO DA SESSÃO E LOGIN ---
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario_atual" not in st.session_state: st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state: st.session_state.chat_selecionado = "Chat Principal"

if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Acessar Console", "📝 Nova Credencial"])
    with aba_login:
        usuario = st.text_input("Usuário:", key="log_user").strip().lower()
        senha = st.text_input("Senha:", type="password", key="log_pass")
        if st.button("Iniciar Sessão", use_container_width=True):
            usuarios_validos = carregar_usuarios()
            if usuario in usuarios_validos and usuarios_validos[usuario] == senha:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario
                st.session_state.chat_selecionado = "Chat Principal"
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
                
    with aba_cadastro:
        novo_usuario = st.text_input("Escolha o Usuário:", key="cad_user").strip().lower()
        nova_senha = st.text_input("Escolha a Senha:", type="password", key="cad_pass")
        confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        if st.button("Cadastrar", use_container_width=True):
            usuarios_existentes = carregar_usuarios()
            if novo_usuario and nova_senha == confirma_senha and novo_usuario not in usuarios_existentes:
                salvar_usuario(novo_usuario, nova_senha)
                st.success("Cadastro realizado com sucesso!")

# --- PAINEL PRINCIPAL ---
else:
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
        
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            elif message.get("type") == "video":
                st.image(message["content"], caption="Mídia Gerada")
            else:
                st.markdown(message["content"])

    prompt_final = None
    texto_input = st.chat_input("Pergunte algo, peça imagens ou cole um link do YouTube...")
    if texto_input: prompt_final = texto_input

    if prompt_final:
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        
        prompt_minusculo = prompt_final.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])
        comando_video = any(cmd in prompt_minusculo for cmd in ["crie um video", "gere um video"])

        if comando_video:
            with st.spinner("🎬 Renderizando mídia..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="video")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "video", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        elif comando_imagem:
            with st.spinner("🎨 Gerando imagem HD..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="imagem")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        else:
            with st.spinner(" Pesquisado..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
            
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
