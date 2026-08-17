import streamlit as st
import os
import json
import requests
import time
import urllib.parse
import re
import hashlib
import logging

# ==========================================
# 0. CONFIGURAÇÃO DE LOGS
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 1. VERIFICAÇÃO E IMPORTAÇÃO DE MÓDULOS
# ==========================================
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning("BeautifulSoup não instalado - pesquisa web desativada")

try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
except ImportError:
    HAS_MIC = False
    logger.warning("Mic recorder não instalado - áudio desativado")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT = True
except ImportError:
    HAS_YT = False
    logger.warning("YouTube API não instalada - transcrição desativada")


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
# 3. SISTEMA DE LOGIN E CADASTRO (Com Hash)
# ==========================================
BANCO_USUARIOS = "usuarios_cadastrados.json"

def hash_senha(senha):
    """Hasha a senha com SHA-256 para segurança básica"""
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    """Carrega usuários do banco com tratamento de erro"""
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Arquivo de usuários corrompido")
            return {"admin": hash_senha("admin123")}
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            return {"admin": hash_senha("admin123")}
    return {"admin": hash_senha("admin123")}

def salvar_usuario(novo_usuario, nova_senha):
    """Salva novo usuário com senha hasheada"""
    try:
        usuarios = carregar_usuarios()
        # Valida entrada
        if not novo_usuario or not nova_senha:
            return False
        usuarios[novo_usuario] = hash_senha(nova_senha)
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar usuário: {e}")
        return False

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
            user_login = st.text_input("Usuário", placeholder="Digite seu nome de usuário").strip()
            pass_login = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)
            
            if btn_entrar:
                if not user_login or not pass_login:
                    st.error("❌ Usuário e senha são obrigatórios!")
                else:
                    usuarios_db = carregar_usuarios()
                    if user_login in usuarios_db and usuarios_db[user_login] == hash_senha(pass_login):
                        st.session_state.logado = True
                        st.session_state.usuario_atual = user_login
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                    
    with tab_cadastro:
        with st.form("form_cadastro"):
            novo_user = st.text_input("Criar Usuário", placeholder="Escolha um nome de usuário").strip()
            nova_pass = st.text_input("Criar Senha", type="password", placeholder="Escolha uma senha forte")
            btn_cadastrar = st.form_submit_button("Cadastrar", use_container_width=True)
            
            if btn_cadastrar:
                if not novo_user or not nova_pass:
                    st.error("⚠️ Usuário e senha são obrigatórios!")
                elif len(novo_user) < 3 or len(nova_pass) < 3:
                    st.warning("⚠️ Usuário e senha precisam ter no mínimo 3 caracteres.")
                else:
                    usuarios_db = carregar_usuarios()
                    if novo_user in usuarios_db:
                        st.error("⚠️ Esse usuário já existe! Escolha outro.")
                    else:
                        if salvar_usuario(novo_user, nova_pass):
                            st.success("✅ Conta criada com sucesso! Agora você pode fazer Login.")
                        else:
                            st.error("❌ Erro ao criar conta. Tente novamente.")
                    
    st.stop()


# ==========================================
# 4. GERENCIADOR DE CHATS (Por Usuário)
# ==========================================
def carregar_todos_chats(usuario):
    """Carrega chats com validação"""
    try:
        arquivo = f"chats_salvos_{usuario}.json"
        if os.path.exists(arquivo):
            with open(arquivo, "r", encoding="utf-8") as f:
                chats = json.load(f)
                # Garante que sempre tem "Chat Principal"
                if not isinstance(chats, dict):
                    return {"Chat Principal": []}
                if "Chat Principal" not in chats:
                    chats["Chat Principal"] = []
                return chats
    except Exception as e:
        logger.error(f"Erro ao carregar chats: {e}")
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    """Salva chats com tratamento de erro"""
    try:
        if not isinstance(todos_chats, dict):
            logger.error("Dados de chat inválidos")
            return False
        with open(f"chats_salvos_{usuario}.json", "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar chats: {e}")
        return False


# ==========================================
# 5. FERRAMENTAS DE PESQUISA (WEB E YOUTUBE)
# ==========================================
@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_na_web(termo):
    """Pesquisa na web via DuckDuckGo (sem API key necessária)"""
    if not HAS_BS4:
        return ""
    
    termo_limpo = termo.strip()
    if len(termo_limpo) < 2:
        return ""
    
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(termo_limpo)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=8)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = []
            
            # Tenta encontrar resultados
            for item in soup.find_all("span", class_="result__snippet")[:5]:
                texto = item.get_text().strip()
                if texto and len(texto) > 10:
                    snippets.append(f"• {texto[:200]}")
            
            return "\n".join(snippets) if snippets else ""
    except requests.Timeout:
        logger.warning("Timeout na pesquisa web")
    except Exception as e:
        logger.warning(f"Erro na pesquisa web: {e}")
    
    return ""

def extrair_texto_youtube(prompt_texto):
    """Extrai transcrição do YouTube (se link for fornecido)"""
    if not HAS_YT:
        return ""
    
    try:
        # Regex melhorada para capturar IDs do YouTube
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})'
        ]
        
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, prompt_texto)
            if match:
                video_id = match.group(1)
                break
        
        if video_id and len(video_id) == 11:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, 
                    languages=['pt', 'en', 'es']
                )
                texto_yt = " ".join([t['text'] for t in transcript])
                return texto_yt[:2000]
            except Exception as e:
                logger.warning(f"Erro ao extrair transcrição YT: {e}")
    except Exception as e:
        logger.warning(f"Erro em extrair_texto_youtube: {e}")
    
    return ""

def gerar_url_midia(prompt_texto, tipo="imagem"):
    """Gera URL para imagem/vídeo via API gratuita"""
    try:
        encoded_prompt = urllib.parse.quote(prompt_texto[:100])  # Limita tamanho
        seed = int(time.time()) % 1000000
        
        largura, altura = 1024, 1024
        prompt_lc = prompt_texto.lower()
        
        if any(x in prompt_lc for x in ["1920x1080", "widescreen", "hd", "landscape"]):
            largura, altura = 1280, 720
        elif any(x in prompt_lc for x in ["portrait", "celular", "vertical"]):
            largura, altura = 720, 1280
        
        modelo = "flux" if tipo == "imagem" else "turbo"
        
        # URL com parâmetros seguros
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?seed={seed}&width={largura}&height={altura}&model={modelo}&nologo=true"
        )
        return url
    except Exception as e:
        logger.error(f"Erro ao gerar URL de mídia: {e}")
        return ""


# ==========================================
# 6. CÉREBRO COMPLETO DA IA (SEM CHAVE)
# ==========================================
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    p_clean = prompt_usuario.lower().strip()

    # Saudações rápidas para conversas comuns
    saudacoes_comuns = ["oi", "olá", "ola", "tudo bem", "e ai", "fala", "salve", "beleza", "bom dia", "boa tarde", "boa noite"]
    if any(s in p_clean for s in saudacoes_comuns) and len(p_clean) < 25:
        return "Opa! Tudo certo por aí. O que você quer pesquisar agora, mano?"

    agradecimentos = ["obrigado", "valeu", "tmj", "brigadão", "vlw"]
    if any(a in p_clean for a in agradecimentos) and len(p_clean) < 15:
        return "Tamo junto! Precisando é só mandar a letra."

    # Executa a pesquisa real na web para capturar dados atualizados
    contexto_web = pesquisar_na_web(prompt_usuario)
    contexto_yt = extrair_texto_youtube(prompt_usuario)

    sys_prompt = (
        "Você é a AI DO PABLO, uma inteligência artificial especialista em pesquisas e checagem de fatos.\n"
        "REGRAS:\n"
        "1. Responda à pergunta do usuário baseando-se estritamente nas informações pesquisadas na Web e no YouTube.\n"
        "2. Não invente dados e não cometa erros. Se a informação estiver nos dados da web, explique com clareza e precisão.\n"
        "3. Seja direto e objetivo, explicando em tópicos curtos ou parágrafos leves para facilitar a leitura."
    )

    if contexto_web:
        sys_prompt += f"\n\n[DADOS REAIS DA WEB]:\n{contexto_web}"
    if contexto_yt:
        sys_prompt += f"\n\n[DADOS DO YOUTUBE]:\n{contexto_yt}"

    # Envia via POST para suportar textos e perguntas longas sem cortar
    try:
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt_usuario}
            ],
            "model": "openai"
        }
        res = requests.post("https://text.pollinations.ai/", json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        
        if res.status_code == 200 and res.text and len(res.text.strip()) > 5:
            if "402 Payment" not in res.text and "deprecated" not in res.text:
                return res.text.strip()
    except Exception:
        pass

    # Resposta baseada diretamente na pesquisa se a IA principal oscilar
    if contexto_web:
        return f"### 🌐 AI DO PABLO (Resultados da Pesquisa):\n\n{contexto_web}"

    return f"Não consegui localizar dados suficientes sobre '{prompt_usuario}' neste momento. Tente reformular a pergunta com outras palavras!"

# ==========================================
# 7. CONTROLE DO PAINEL LATERAL
# ==========================================
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = "Chat Principal"

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
    audio_data = mic_recorder(
        start_prompt="🔊 Gravar",
        stop_prompt="⏹️ Enviar",
        key='gravador_chamada',
        use_container_width=True
    )
    if audio_data:
        st.sidebar.info("✅ Áudio capturado (suporte completo em breve)")

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Minhas Conversas")

lista_de_chats = list(conversas_usuario.keys()) if conversas_usuario else ["Chat Principal"]
if "Chat Principal" not in lista_de_chats:
    lista_de_chats.insert(0, "Chat Principal")

try:
    index_atual = lista_de_chats.index(st.session_state.chat_selecionado)
except ValueError:
    index_atual = 0

chat_escolhido = st.sidebar.selectbox(
    "Selecionar Conversa:",
    lista_de_chats,
    index=index_atual
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input(
    "Novo Chat:",
    key="new_chat_input",
    placeholder="Nome do chat..."
).strip()

if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
    if novo_nome_chat:
        if novo_nome_chat in conversas_usuario:
            st.sidebar.error("⚠️ Esse chat já existe!")
        else:
            conversas_usuario[novo_nome_chat] = []
            if salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario):
                st.session_state.chat_selecionado = novo_nome_chat
                st.rerun()
    else:
        st.sidebar.warning("⚠️ Digite um nome para o chat!")

st.sidebar.markdown("---")

if st.session_state.chat_selecionado != "Chat Principal":
    if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True):
        if st.session_state.chat_selecionado in conversas_usuario:
            del conversas_usuario[st.session_state.chat_selecionado]
            if salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario):
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
    with st.chat_message(message.get("role", "user")):
        msg_type = message.get("type")
        msg_content = message.get("content", "")
        
        if msg_type == "image":
            try:
                st.image(msg_content, caption="🖼️ Imagem gerada pela AI DO PABLO")
            except Exception as e:
                st.error(f"Erro ao exibir imagem: {e}")
        elif msg_type == "video":
            try:
                st.image(msg_content, caption="🎬 Mídia gerada pela AI DO PABLO")
            except Exception as e:
                st.error(f"Erro ao exibir vídeo: {e}")
        else:
            st.markdown(msg_content)

texto_input = st.chat_input("Peça qualquer coisa: pesquise, crie imagens, faça perguntas...")

if texto_input:
    texto_input = texto_input.strip()
    
    # Adiciona mensagem do usuário
    conversas_usuario[st.session_state.chat_selecionado].append({
        "role": "user",
        "content": texto_input
    })
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    
    with st.chat_message("user"):
        st.markdown(texto_input)

    prompt_lower = texto_input.lower()
    
    # Detecta comando de imagem
    eh_imagem = any(cmd in prompt_lower for cmd in [
        "crie uma imagem", "gere uma imagem", "desenhe", "foto de",
        "imagem de", "cria imagem", "gera imagem", "picture of"
    ])
    
    # Detecta comando de vídeo
    eh_video = any(cmd in prompt_lower for cmd in [
        "crie um video", "gere um video", "video de", "cria video",
        "gera video", "create video"
    ])

    with st.chat_message("assistant"):
        if eh_video:
            with st.spinner("🎬 Gerando mídia visual..."):
                url_gerada = gerar_url_midia(texto_input, tipo="video")
                if url_gerada:
                    try:
                        st.image(url_gerada, caption="🎬 Mídia gerada")
                        conversas_usuario[st.session_state.chat_selecionado].append({
                            "role": "assistant",
                            "type": "video",
                            "content": url_gerada
                        })
                        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                    except Exception as e:
                        st.error(f"Erro ao gerar vídeo: {e}")
                else:
                    st.warning("⚠️ Erro ao gerar vídeo")

        elif eh_imagem:
            with st.spinner("🎨 Pintando sua imagem..."):
                url_gerada = gerar_url_midia(texto_input, tipo="imagem")
                if url_gerada:
                    try:
                        st.image(url_gerada, caption="🖼️ Imagem gerada")
                        conversas_usuario[st.session_state.chat_selecionado].append({
                            "role": "assistant",
                            "type": "image",
                            "content": url_gerada
                        })
                        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                    except Exception as e:
                        st.error(f"Erro ao gerar imagem: {e}")
                else:
                    st.warning("⚠️ Erro ao gerar imagem")

        else:
            with st.spinner("⚡ AI DO PABLO está processando..."):
                resposta_texto = chamar_ia_suprema(
                    conversas_usuario[st.session_state.chat_selecionado],
                    texto_input
                )
                st.markdown(resposta_texto)
                conversas_usuario[st.session_state.chat_selecionado].append({
                    "role": "assistant",
                    "content": resposta_texto
                })
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
