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


# ==========================================
# 2. CONFIGURAÇÃO DA INTERFACE & ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="AI DO PABLO · Supreme Core",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

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
    }
    
    .login-container {
        background: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema Multi-Linguagem · Busca Web & YT</p>', unsafe_allow_html=True)
st.markdown("---")


# ==========================================
# 3. SISTEMA DE LOGIN E CADASTRO
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

# Controle de Sessão Global
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""

# Tela de Login (Trava o restante do app se não logado)
if not st.session_state.logado:
    st.markdown("### 🔐 Acesso ao Sistema")
    
    tab_login, tab_cadastro = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    with tab_login:
        with st.form("form_login"):
            user_login = st.text_input("Usuário", placeholder="Digite seu nome de usuário")
            pass_login = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_entrar:
                usuarios_db = carregar_usuarios()
                if user_login in usuarios_db and usuarios_db[user_login] == pass_login:
                    st.session_state.logado = True
                    st.session_state.usuario_atual = user_login
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")
                    
    with tab_cadastro:
        with st.form("form_cadastro"):
            novo_user = st.text_input("Criar Usuário", placeholder="Escolha um nome de usuário")
            nova_pass = st.text_input("Criar Senha", type="password", placeholder="Escolha uma senha forte")
            btn_cadastrar = st.form_submit_button("Cadastrar", use_container_width=True)
            
            if btn_cadastrar:
                usuarios_db = carregar_usuarios()
                if novo_user in usuarios_db:
                    st.error("⚠️ Esse usuário já existe! Escolha outro.")
                elif len(novo_user) < 3 or len(nova_pass) < 3:
                    st.warning("⚠️ O usuário e a senha precisam ter pelo menos 3 caracteres.")
                else:
                    salvar_usuario(novo_user, nova_pass)
                    st.success("✅ Conta criada com sucesso! Agora você pode fazer Login na aba ao lado.")
                    
    st.stop() # Interrompe o carregamento da página até logar


# ==========================================
# 4. GERENCIADOR DE CHATS (Por Usuário)
# ==========================================
def carregar_todos_chats(usuario):
    arquivo = f"chats_salvos_{usuario}.json"
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        with open(f"chats_salvos_{usuario}.json", "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


# ==========================================
# 5. FERRAMENTAS DE PESQUISA (WEB E YOUTUBE)
# ==========================================
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    if not HAS_BS4 or len(termo.strip()) < 2:
        return ""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(termo)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = []
            for a in soup.find_all("a", class_="result__snippet")[:4]:
                texto = a.get_text().strip()
                if texto and len(texto) > 15:
                    snippets.append(f"- {texto}") 
            return "\n".join(snippets)
    except Exception:
        pass
    return ""

def extrair_texto_youtube(prompt_texto):
    if not HAS_YT:
        return ""
    try:
        urls = re.findall(r'(https?://[^\s]+)', prompt_texto)
        video_id = None
        for url in urls:
            if "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
                break
            elif "youtube.com/watch" in url:
                video_id = url.split("v=")[1].split("&")[0].split("?")[0]
                break
            
        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en', 'es'])
            texto_yt = " ".join([t['text'] for t in transcript])
            return texto_yt[:2000]
    except Exception:
        pass
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
# 6. CÉREBRO COMPLETO DA IA
# ==========================================
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    p_clean = prompt_usuario.lower().strip()

    saudacoes_exatas = ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "tudo bem", "quem é você", "quem e voce"]
    if p_clean in saudacoes_exatas:
        return "Fala, mano! AI DO PABLO na área. Pode perguntar sobre qualquer assunto, pedir códigos em qualquer linguagem ou pesquisar o que quiser!"

    contexto_web = pesquisar_na_web(prompt_usuario)
    contexto_yt = extrair_texto_youtube(prompt_usuario)

    sys_prompt = (
        "Você é a AI DO PABLO, uma Inteligência Artificial Suprema, versátil e programadora Full-Stack.\n\n"
        "REGRAS DE OURO:\n"
        "1. VOCÊ SABE DE TUDO: Responda perguntas sobre qualquer assunto (história, ciência, atualidades, matemática, dicas) com precisão absoluta baseada nos dados da Web.\n"
        "2. PROGRAMAÇÃO MULTI-LINGUAGEM: Você cria, ensina e conserta códigos em QUALQUER linguagem (Python, JavaScript, HTML, C++, C#, Lua/Roblox, Java, etc.). Gere o código completo e ensine como usar.\n"
        "3. FORMATAÇÃO LEVE E BONITA: Você DEVE explicar muito bem as coisas, MAS NUNCA gere blocos gigantes de texto. Quebre sua explicação usando listas (bullet points), negrito nas partes importantes e parágrafos curtos. Torne a leitura rápida e prazerosa.\n"
        "4. IDIOMA: Responda sempre em português do Brasil de forma amigável."
    )

    if contexto_web:
        sys_prompt += f"\n\n[DADOS DE PESQUISA DA WEB (Use para basear sua resposta)]: {contexto_web}"
    if contexto_yt:
        sys_prompt += f"\n\n[DADOS DO VÍDEO DO YOUTUBE]: {contexto_yt}"

    prompt_instrucao = f"{sys_prompt}\n\nPedido do usuário: {prompt_usuario}"

    try:
        url_api = f"https://text.pollinations.ai/{urllib.parse.quote(prompt_instrucao[:1800])}?model=qwen-coder"
        res = requests.get(url_api, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        
        if res.status_code == 200 and res.text and len(res.text.strip()) > 5:
            if "402 Payment" not in res.text and "deprecated" not in res.text:
                return res.text.strip()
    except Exception:
        pass

    if contexto_web:
        return (
            f"### 🌐 AI DO PABLO (Resultados Encontrados)\n\n"
            f"Fiz uma busca rápida sobre **'{prompt_usuario}'** e encontrei estes pontos cruciais:\n\n"
            f"{contexto_web}\n\n"
            f"*Se quiser que eu faça um código sobre isso ou me aprofunde mais em um dos tópicos, é só mandar!*"
        )

    return f"Entendi o que você quer sobre **'{prompt_usuario}'**! Me dá só mais um detalhe do que você precisa para eu escrever a resposta completa ou o código perfeito para você!"


# ==========================================
# 7. CONTROLE DO PAINEL LATERAL
# ==========================================
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"

mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

st.sidebar.title("🛸 PAINEL DE CONTROLE")
operador_nome = str(st.session_state.usuario_atual).upper()
st.sidebar.write(f"Operador: **{operador_nome}**")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario_atual = ""
    st.rerun()

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
# 8. EXIBIÇÃO DE CHAT E INPUTS
# ==========================================
for message in mensagens_atuais:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Imagem gerada pela AI DO PABLO")
        elif message.get("type") == "video":
            st.image(message["content"], caption="Mídia gerada pela AI DO PABLO")
        else:
            st.markdown(message["content"])

texto_input = st.chat_input("Peça qualquer código, pesquise dados ou peça imagens...")

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
            with st.spinner("⚡ AI DO PABLO está processando sua resposta..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], texto_input)
                st.markdown(resposta_texto)
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
