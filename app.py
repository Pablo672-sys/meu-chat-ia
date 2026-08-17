# ==========================================
# 0. IMPORTS E CONFIGURAÇÕES GLOBAIS
# ==========================================
import streamlit as st
import os
import json
import requests
import time
import urllib.parse
import re
import hashlib
import logging
from typing import Dict, List, Any, Optional

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes de Arquivos
BANCO_USUARIOS_FILE = "usuarios_cadastrados.json"
LOG_USUARIO_ATIVO = "usuario_ativo.log" # Para tentar manter o último usuário logado

# Tenta carregar módulos opcionais
HAS_BS4 = False
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
    logger.info("BeautifulSoup importado com sucesso.")
except ImportError:
    logger.warning("BeautifulSoup não instalado. Pesquisa web estará desativada.")

HAS_MIC = False
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
    logger.info("Mic recorder importado com sucesso.")
except ImportError:
    logger.warning("Mic recorder não instalado. Gravação de áudio estará desativada.")

HAS_YT = False
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT = True
    logger.info("YouTubeTranscriptApi importado com sucesso.")
except ImportError:
    logger.warning("YouTube API não instalada. Transcrição de YouTube estará desativada.")

# ==========================================
# 1. CONFIGURAÇÃO DA INTERFACE & ESTILOS CSS
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

    /* Estilos para o container de login */
    .login-container {
        background: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }

    /* Esconder os ícones de re-run da Streamlit nas mensagens */
    .stChatMessage > div:first-child > div:first-child > div:nth-child(2) {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema Multi-Linguagem · Busca Web & YT</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 2. GERENCIAMENTO DE USUÁRIOS E LOGIN (Com Hash)
# ==========================================

def hash_senha(senha: str) -> str:
    """Hasha a senha com SHA-256 para segurança básica."""
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios() -> Dict[str, str]:
    """Carrega usuários do banco com tratamento de erro."""
    if os.path.exists(BANCO_USUARIOS_FILE):
        try:
            with open(BANCO_USUARIOS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
                if not isinstance(usuarios, dict): # Garante que é um dicionário
                    logger.error("Arquivo de usuários corrompido ou formato inválido. Resetando.")
                    return {"admin": hash_senha("admin123")} # Reset para padrão seguro
                return usuarios
        except json.JSONDecodeError:
            logger.error(f"Falha ao decodificar JSON do arquivo de usuários: {BANCO_USUARIOS_FILE}. Resetando.")
            return {"admin": hash_senha("admin123")}
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar usuários de {BANCO_USUARIOS_FILE}: {e}")
            return {"admin": hash_senha("admin123")}
    else:
        # Cria o arquivo com um usuário admin padrão se não existir
        logger.info(f"Arquivo de usuários '{BANCO_USUARIOS_FILE}' não encontrado. Criando com usuário 'admin'.")
        senha_admin_hashed = hash_senha("admin123")
        try:
            with open(BANCO_USUARIOS_FILE, "w", encoding="utf-8") as f:
                json.dump({"admin": senha_admin_hashed}, f, ensure_ascii=False, indent=4)
            return {"admin": senha_admin_hashed}
        except Exception as e:
            logger.error(f"Falha ao criar arquivo de usuários padrão: {e}")
            return {} # Retorna vazio em caso de falha crítica

def salvar_usuario(novo_usuario: str, nova_senha: str) -> bool:
    """Salva novo usuário com senha hasheada."""
    if not novo_usuario or not nova_senha:
        logger.warning("Tentativa de salvar usuário com nome ou senha vazios.")
        return False
        
    usuarios = carregar_usuarios()
    if novo_usuario in usuarios:
        logger.warning(f"Tentativa de criar usuário que já existe: '{novo_usuario}'.")
        return False # Usuário já existe

    usuarios[novo_usuario] = hash_senha(nova_senha)
    try:
        with open(BANCO_USUARIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
        logger.info(f"Usuário '{novo_usuario}' cadastrado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar usuário '{novo_usuario}' no arquivo {BANCO_USUARIOS_FILE}: {e}")
        return False

def carregar_ultimo_usuario_logado() -> Optional[str]:
    """Tenta carregar o último usuário logado de um arquivo."""
    if os.path.exists(LOG_USUARIO_ATIVO):
        try:
            with open(LOG_USUARIO_ATIVO, "r", encoding="utf-8") as f:
                usuario = f.read().strip()
                if usuario:
                    return usuario
        except Exception as e:
            logger.error(f"Erro ao carregar último usuário logado de {LOG_USUARIO_ATIVO}: {e}")
    return None

def salvar_ultimo_usuario_logado(usuario: str):
    """Salva o usuário logado atual."""
    try:
        with open(LOG_USUARIO_ATIVO, "w", encoding="utf-8") as f:
            f.write(usuario)
    except Exception as e:
        logger.error(f"Erro ao salvar último usuário logado '{usuario}' em {LOG_USUARIO_ATIVO}: {e}")

# Inicialização do estado da sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

# Tenta logar automaticamente o último usuário
if not st.session_state.logado:
    ultimo_usuario = carregar_ultimo_usuario_logado()
    if ultimo_usuario:
        st.session_state.usuario_atual = ultimo_usuario
        # Não logamos automaticamente, pois o usuário pode querer fazer login com outro.
        # Ele será apresentado com a tela de login, mas com o campo usuário preenchido.

# Tela de Login/Cadastro (Bloqueia o resto do app se não logado)
if not st.session_state.logado:
    st.markdown("### 🔐 Acesso ao Sistema")
    
    tab_login, tab_cadastro = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    with tab_login:
        with st.form("form_login", clear_on_submit=True):
            user_login = st.text_input("Usuário", placeholder="Digite seu nome de usuário", value=st.session_state.usuario_atual if st.session_state.usuario_atual else "").strip()
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
                        st.session_state.chat_selecionado = "Chat Principal" # Reseta para chat principal ao logar
                        salvar_ultimo_usuario_logado(user_login)
                        st.success("✅ Login realizado com sucesso! Bem-vindo(a) de volta!")
                        # Usar time.sleep para dar tempo de a mensagem de sucesso aparecer antes de recarregar
                        time.sleep(1) 
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos! Tente novamente.")
                    
    with tab_cadastro:
        with st.form("form_cadastro", clear_on_submit=True):
            novo_user = st.text_input("Criar Usuário", placeholder="Escolha um nome de usuário").strip()
            nova_pass = st.text_input("Criar Senha", type="password", placeholder="Escolha uma senha forte (mínimo 3 caracteres)")
            btn_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
            
            if btn_cadastrar:
                if not novo_user or not nova_pass:
                    st.error("⚠️ Usuário e senha são obrigatórios!")
                elif len(novo_user) < 3 or len(nova_pass) < 3:
                    st.warning("⚠️ Usuário e senha precisam ter no mínimo 3 caracteres.")
                else:
                    if salvar_usuario(novo_user, nova_pass):
                        st.success("✅ Conta criada com sucesso! Agora você pode fazer Login.")
                        # Limpa os campos após sucesso
                        st.session_state.new_chat_input = "" # Limpa campo de novo nome de chat se estiver aberto
                    else:
                        # A função salvar_usuario já loga o erro específico
                        st.error("❌ Esse nome de usuário já existe ou ocorreu um erro ao salvar. Verifique as mensagens de log ou tente outro nome.")
                    
    st.stop() # Bloqueia a execução do restante do script se não logado

# ==========================================
# 3. GERENCIADOR DE CHATS (Por Usuário)
# ==========================================
def get_chat_file_path(usuario: str) -> str:
    """Retorna o caminho do arquivo de chats para um usuário específico."""
    return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario: str) -> Dict[str, List[Dict[str, Any]]]:
    """Carrega chats de um usuário com validação e garante estrutura mínima."""
    arquivo_chats = get_chat_file_path(usuario)
    try:
        if os.path.exists(arquivo_chats):
            with open(arquivo_chats, "r", encoding="utf-8") as f:
                chats_data = json.load(f)
                # Validação robusta da estrutura dos dados carregados
                if not isinstance(chats_data, dict):
                    logger.error(f"Formato inválido em '{arquivo_chats}'. Resetando para padrão.")
                    return {"Chat Principal": []}
                
                # Garante que sempre tenha "Chat Principal" e que os chats sejam listas de dicionários
                if "Chat Principal" not in chats_data:
                    chats_data["Chat Principal"] = []
                
                for chat_name, messages in chats_data.items():
                    if not isinstance(messages, list):
                        logger.warning(f"Chat '{chat_name}' em '{arquivo_chats}' tem formato inválido. Resetando.")
                        chats_data[chat_name] = []
                    else:
                        # Valida cada mensagem dentro do chat
                        valid_messages = []
                        for msg in messages:
                            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                                valid_messages.append(msg)
                            else:
                                logger.warning(f"Mensagem inválida encontrada no chat '{chat_name}': {msg}")
                        chats_data[chat_name] = valid_messages
                
                return chats_data
        else:
            logger.info(f"Arquivo de chats '{arquivo_chats}' não encontrado. Criando novo.")
            return {"Chat Principal": []} # Retorna estrutura padrão se o arquivo não existir
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON de '{arquivo_chats}'. Arquivo pode estar corrompido. Resetando.")
        return {"Chat Principal": []}
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar chats de '{arquivo_chats}': {e}")
        return {"Chat Principal": []}

def salvar_todos_chats(usuario: str, todos_chats: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Salva chats de um usuário com tratamento de erro."""
    if not isinstance(todos_chats, dict):
        logger.error("Tentativa de salvar dados de chat em formato inválido (não é dicionário).")
        return False
    
    arquivo_chats = get_chat_file_path(usuario)
    try:
        with open(arquivo_chats, "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
        logger.debug(f"Chats salvos com sucesso para o usuário '{usuario}' em '{arquivo_chats}'.")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar chats em '{arquivo_chats}': {e}")
        return False

# ==========================================
# 4. FERRAMENTAS DE PESQUISA (WEB E YOUTUBE)
# ==========================================
@st.cache_data(show_spinner=False, ttl=3600) # Cache por 1 hora
def pesquisar_na_web(termo: str) -> str:
    """Pesquisa na web via DuckDuckGo (sem API key necessária) e retorna snippets."""
    if not HAS_BS4:
        logger.warning("Pesquisa web desativada: BeautifulSoup não encontrado.")
        return "Pesquisa web indisponível (BeautifulSoup não instalado)."
    
    termo_limpo = termo.strip()
    if len(termo_limpo) < 2:
        return ""
    
    try:
        # Use um user-agent comum para evitar bloqueios
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url_encoded = urllib.parse.quote(termo_limpo)
        url = f"https://html.duckduckgo.com/html/?q={url_encoded}"
        
        response = requests.get(url, headers=headers, timeout=10) # Timeout de 10 segundos
        response.raise_for_status() # Lança exceção para códigos de erro HTTP (4xx, 5xx)
        
        soup = BeautifulSoup(response.text, "html.parser")
        snippets = []
        
        # Busca por elementos que geralmente contêm os snippets
        # Este seletor pode precisar de ajustes se o layout do DuckDuckGo mudar
        results = soup.find_all("div", class_="result__body")
        if not results:
            results = soup.find_all("a", class_="result__a") # Outro seletor alternativo
        
        for item in results[:5]: # Pega os 5 primeiros resultados mais relevantes
            snippet_tag = item.find("span", class_="result__snippet")
            if snippet_tag:
                texto = snippet_tag.get_text().strip()
                if texto and len(texto) > 10:
                    # Limita o tamanho do snippet para não sobrecarregar
                    snippets.append(f"• {texto[:250]}{'...' if len(texto) > 250 else ''}")
            else:
                # Tenta pegar o texto do link principal se não houver snippet
                link_tag = item.find("a", class_="result__a")
                if link_tag:
                    texto_link = link_tag.get_text().strip()
                    if texto_link and len(texto_link) > 10:
                         snippets.append(f"• {texto_link[:250]}{'...' if len(texto_link) > 250 else ''}")

        if not snippets:
            logger.info(f"Nenhum snippet encontrado para '{termo_limpo}' na pesquisa web.")
            return ""
            
        return "\n".join(snippets)

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout ao tentar pesquisar na web por '{termo_limpo}'.")
        return "Erro: A pesquisa na web demorou demais para responder."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao pesquisar na web por '{termo_limpo}': {e}")
        return f"Erro ao acessar a pesquisa na web: {e}"
    except Exception as e:
        logger.error(f"Erro inesperado ao processar pesquisa web para '{termo_limpo}': {e}")
        return "Ocorreu um erro inesperado durante a pesquisa na web."

def extrair_texto_youtube(prompt_texto: str) -> str:
    """Extrai transcrição de um link do YouTube (se fornecido)."""
    if not HAS_YT:
        logger.warning("Extrator de YouTube desativado: YouTubeTranscriptApi não instalado.")
        return ""
    
    # Regex mais robusta para capturar IDs de vídeo do YouTube em vários formatos
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=|embed\/|v\/|shorts\/|)([\w-]{11})(?:\S+)?'
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, prompt_texto)
        if match:
            video_id = match.group(1)
            if len(video_id) == 11:
                break # Encontrou um ID válido, sai do loop
    
    if not video_id:
        # logger.debug("Nenhum link de vídeo do YouTube encontrado no prompt.")
        return "" # Não há link de vídeo no prompt

    try:
        logger.info(f"Tentando extrair transcrição para o vídeo ID: {video_id}")
        # Tenta obter a transcrição em português, inglês ou espanhol.
        # Se falhar, pode lançar uma exceção.
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Tenta encontrar uma transcrição em pt, en, es na ordem de preferência
        transcript = None
        try:
            transcript = transcript_list.find_transcript(['pt', 'en', 'es'])
        except Exception as e_find:
             logger.warning(f"Não foi possível encontrar transcrições diretas para PT/EN/ES no vídeo {video_id}. Tentando obter a primeira disponível. Erro: {e_find}")
             # Tenta pegar a primeira transcrição disponível se as preferenciais falharem
             transcript = transcript_list.find_generated_transcript(['en']) # Tenta gerada se não houver manual
             if not transcript:
                 transcript = transcript_list.find_transcript(['en']) # Tenta manual se houver
        
        if not transcript:
             logger.warning(f"Nenhuma transcrição encontrada ou gerada para o vídeo ID: {video_id}")
             return ""
             
        transcript_text = transcript.fetch()
        texto_completo = " ".join([t['text'] for t in transcript_text])
        
        # Limita o tamanho para não sobrecarregar a IA principal
        return texto_completo[:3000] # Pega até 3000 caracteres
        
    except Exception as e:
        logger.error(f"Erro ao extrair transcrição do YouTube para o vídeo ID {video_id}: {e}")
        return f"Erro ao obter transcrição do YouTube para o vídeo: {e}"

def gerar_url_midia(prompt_texto: str, tipo: str = "imagem") -> str:
    """Gera URL para imagem ou vídeo via API gratuita (Pollinations.ai)."""
    if not prompt_texto:
        return ""
        
    try:
        # Limita o prompt para evitar problemas com URLs muito longas
        prompt_limitado = prompt_texto[:150]
        encoded_prompt = urllib.parse.quote(prompt_limitado)
        
        seed = int(time.time()) % 1000000 # Semente aleatória baseada no tempo
        
        # Define dimensões padrão
        largura, altura = 1024, 1024
        prompt_lc = prompt_limitado.lower()
        
        # Lógica para ajustar dimensões com base em palavras-chave
        if any(x in prompt_lc for x in ["1920x1080", "widescreen", "hd", "paisagem", "landscape", "horizontal"]):
            largura, altura = 1280, 720
        elif any(x in prompt_lc for x in ["retrato", "vertical", "celular", "celular", "portrait"]):
            largura, altura = 720, 1280
        elif any(x in prompt_lc for x in ["quadrado", "square"]):
             largura, altura = 1080, 1080
        
        # Seleciona o modelo apropriado
        modelo = "flux" if tipo == "imagem" else "turbo" # 'flux' é bom para imagens, 'turbo' para vídeo/animação
        
        # Monta a URL com parâmetros seguros
        base_url = "https://image.pollinations.ai/prompt/"
        params = {
            "seed": seed,
            "width": largura,
            "height": altura,
            "model": modelo,
            "nologo": "true" # Remove o logo da Pollinations
        }
        
        # Codifica os parâmetros
        params_encoded = "&".join([f"{key}={urllib.parse.quote(str(value))}" for key, value in params.items()])
        
        url_gerada = f"{base_url}{encoded_prompt}?{params_encoded}"
        
        logger.info(f"URL de mídia gerada para tipo '{tipo}': {url_gerada[:100]}...") # Loga parte da URL
        return url_gerada
        
    except Exception as e:
        logger.error(f"Erro ao gerar URL de mídia com prompt '{prompt_texto[:50]}...': {e}")
        return "" # Retorna string vazia em caso de erro

# ==========================================
# 5. CÉREBRO COMPLETO DA IA (SEM CHAVE)
# ==========================================
# Função de cache para respostas da IA para evitar chamadas repetidas e custosas
# O TTL (Time To Live) pode ser ajustado. 3600s = 1 hora.
@st.cache_data(show_spinner=False, ttl=3600)
def chamar_ia_suprema_cached(prompt_usuario: str, contexto_web: str, contexto_yt: str) -> str:
    """Chama a IA principal e retorna a resposta."""
    
    p_clean = prompt_usuario.lower().strip()

    # Respostas rápidas para saudações e agradecimentos comuns
    saudacoes_comuns = ["oi", "olá", "ola", "tudo bem", "e ai", "fala", "salve", "beleza", "bom dia", "boa tarde", "boa noite", "opa"]
    if any(s in p_clean for s in saudacoes_comuns) and len(p_clean) < 25:
        return "Opa! Tudo certo por aí. O que você quer pesquisar agora, mano?"

    agradecimentos = ["obrigado", "valeu", "tmj", "brigadão", "vlw", "obrigada"]
    if any(a in p_clean for a in agradecimentos) and len(p_clean) < 15:
        return "Tamo junto! Precisando é só mandar a letra."

    # Constrói o prompt do sistema
    sys_prompt_parts = [
        "Você é a AI DO PABLO, uma inteligência artificial especialista em pesquisas e checagem de fatos.",
        "REGRAS:",
        "1. Responda à pergunta do usuário baseando-se ESTREITAMENTE nas informações pesquisadas na Web e no YouTube.",
        "2. NÃO INVENTE DADOS e não cometa erros. Se a informação estiver nos dados da web/YT, explique com clareza e precisão.",
        "3. Seja direto e objetivo, explicando em tópicos curtos ou parágrafos leves para facilitar a leitura.",
        "4. Se não houver informações suficientes nos dados fornecidos, informe que não foi possível encontrar."
    ]

    if contexto_web:
        sys_prompt_parts.append(f"\n[DADOS REAIS DA WEB]:\n{contexto_web}")
    if contexto_yt:
        sys_prompt_parts.append(f"\n[DADOS DO YOUTUBE]:\n{contexto_yt}")
        
    sys_prompt = "\n".join(sys_prompt_parts)

    # Tenta chamar a API principal
    try:
        payload = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt_usuario}
            ],
            "model": "openai" # Pode ser que precise mudar isso dependendo da API
        }
        
        # Endpoint da API (verifique se este é o endpoint correto para a sua conta/serviço)
        api_url = "https://text.pollinations.ai/" 
        
        response = requests.post(api_url, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=30) # Timeout maior para IA
        response.raise_for_status() # Verifica se a requisição foi bem-sucedida

        resposta_api = response.text.strip()

        if "402 Payment Required" in resposta_api or "You sent too many requests" in resposta_api:
            logger.warning("API de texto retornou erro de pagamento ou limite de requisições.")
            raise Exception("Limite de requisições ou pagamento necessário para a API de texto.")
        elif not resposta_api or len(resposta_api) < 10:
            logger.warning("API de texto retornou uma resposta vazia ou muito curta.")
            raise Exception("API de texto retornou dados insuficientes.")
        
        logger.info("Resposta da IA principal recebida com sucesso.")
        return resposta_api

    except requests.exceptions.Timeout:
        logger.warning("Timeout ao chamar a API de texto (IA principal).")
        return "Erro: A IA demorou demais para responder. Tente novamente."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao chamar a IA principal: {e}")
        return f"Erro na comunicação com a IA principal: {e}"
    except Exception as e:
        logger.error(f"Erro inesperado ao chamar a IA principal: {e}")
        # Se a IA falhar, tenta usar os dados da web como fallback
        if contexto_web:
            logger.info("IA principal falhou, retornando fallback da pesquisa web.")
            return f"Desculpe, tive um problema para processar sua solicitação com a IA. Aqui estão os resultados da pesquisa na web:\n\n{contexto_web}"
        else:
            return f"Ocorreu um erro inesperado e não consegui obter uma resposta. Por favor, tente reformular sua pergunta."

def chamar_ia_suprema(historico_mensagens: List[Dict[str, Any]], prompt_usuario: str) -> str:
    """
    Função principal para chamar a IA. Ela decide se usa cache ou chama diretamente.
    Desativa o cache por enquanto para garantir que sempre busca os dados mais recentes.
    """
    
    # 1. Extrai contexto da web e YouTube ANTES de chamar a IA principal
    contexto_web = pesquisar_na_web(prompt_usuario)
    contexto_yt = extrair_texto_youtube(prompt_usuario)
    
    # 2. Chama a IA (ou seu cache) com os dados coletados
    # Descomente a linha abaixo e comente a de baixo para ativar o cache da IA
    # resposta = chamar_ia_suprema_cached(prompt_usuario, contexto_web, contexto_yt)
    resposta = chamar_ia_suprema_cached(prompt_usuario, contexto_web, contexto_yt) # Mantém cache ativo por padrão
    
    # 3. Retorna a resposta
    return resposta

# ==========================================
# 6. CONTROLE DO PAINEL LATERAL
# ==========================================
# Carrega todos os chats do usuário atual
conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

# Garante que o chat selecionado exista
if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = "Chat Principal"
    logger.info(f"Chat selecionado '{st.session_state.chat_selecionado}' não encontrado, resetado para 'Chat Principal'.")

# Obtém as mensagens do chat selecionado
mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

# Configuração da Sidebar
st.sidebar.title("🛸 PAINEL DE CONTROLE")
operador_nome = str(st.session_state.usuario_atual).upper()
st.sidebar.write(f"Operador: **{operador_nome}**")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario_atual = ""
    salvar_ultimo_usuario_logado("") # Limpa o log do último usuário
    logger.info("Usuário deslogado.")
    st.rerun()

# Se o microfone estiver disponível
if HAS_MIC:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Entrada de Voz")
    audio_data = mic_recorder(
        start_prompt="🔊 Gravar",
        stop_prompt="⏹️ Parar e Processar",
        key='gravador_chamada',
        use_container_width=True,
        sample_rate=44100 # Sample rate comum
    )
    if audio_data:
        # AQUI VOCÊ ADICIONARIA A LÓGICA DE TRANSCRIÇÃO SE TIVER BIBLIOTECAS
        st.sidebar.info("✅ Áudio capturado. Processamento de voz completo em breve.")
        # Exemplo de como seria se você tivesse uma função de transcrição:
        # try:
        #     texto_transcrito = transcrever_audio(audio_data) # Sua função de transcrição
        #     st.sidebar.text_area("Texto Transcrito:", value=texto_transcrito, height=100)
        #     # Você poderia então inserir 'texto_transcrito' no input principal
        # except Exception as e:
        #     st.sidebar.error(f"Erro ao transcrever áudio: {e}")

# Seção de Gerenciamento de Chats
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Minhas Conversas")

lista_de_chats = sorted(list(conversas_usuario.keys())) if conversas_usuario else ["Chat Principal"]
if "Chat Principal" not in lista_de_chats:
    lista_de_chats.insert(0, "Chat Principal")
    conversas_usuario["Chat Principal"] = [] # Garante que exista

try:
    index_atual = lista_de_chats.index(st.session_state.chat_selecionado)
except ValueError:
    index_atual = 0
    st.session_state.chat_selecionado = "Chat Principal" # Reseta se o chat selecionado foi deletado

chat_escolhido = st.sidebar.selectbox(
    "Selecionar Conversa:",
    lista_de_chats,
    index=index_atual,
    key="selectbox_chat"
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

# Campo para criar novo chat
novo_nome_chat = st.sidebar.text_input(
    "Nome para novo chat:",
    key="new_chat_input",
    placeholder="Ex: Ideias para projeto X..."
).strip()

if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
    if novo_nome_chat:
        if novo_nome_chat in conversas_usuario:
            st.sidebar.error("⚠️ Esse nome de chat já existe! Escolha outro.")
        else:
            conversas_usuario[novo_nome_chat] = [] # Cria o novo chat vazio
            if salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario):
                st.session_state.chat_selecionado = novo_nome_chat # Define o novo chat como selecionado
                st.session_state.new_chat_input = "" # Limpa o campo de texto
                st.rerun()
            else:
                st.sidebar.error("❌ Erro ao salvar o novo chat.")
    else:
        st.sidebar.warning("⚠️ Por favor, digite um nome para o novo chat!")

# Botões de ação para o chat atual (se não for o "Chat Principal")
st.sidebar.markdown("---")
if st.session_state.chat_selecionado != "Chat Principal":
    if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True, type="secondary"):
        if st.session_state.chat_selecionado in conversas_usuario:
            del conversas_usuario[st.session_state.chat_selecionado]
            if salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario):
                st.session_state.chat_selecionado = "Chat Principal" # Volta para o chat principal
                st.rerun()
            else:
                st.sidebar.error("❌ Erro ao apagar o chat.")

if st.sidebar.button("🗑️ Limpar Mensagens do Chat Atual", use_container_width=True, type="secondary"):
    if st.session_state.chat_selecionado in conversas_usuario:
        conversas_usuario[st.session_state.chat_selecionado] = [] # Esvazia a lista de mensagens
        if salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario):
            st.rerun() # Recarrega para mostrar o chat limpo
        else:
            st.sidebar.error("❌ Erro ao limpar mensagens do chat.")

# ==========================================
# 7. EXIBIÇÃO DO CHAT E INPUTS DE USUÁRIO
# ==========================================

# Exibe as mensagens do chat selecionado
for message in mensagens_atuais:
    role = message.get("role", "user")
    content = message.get("content", "")
    msg_type = message.get("type", "text") # Tipo pode ser 'text', 'image', 'video'

    with st.chat_message(role):
        if msg_type == "image":
            try:
                st.image(content, caption="🖼️ Imagem gerada pela IA")
            except Exception as e:
                st.error(f"Erro ao exibir imagem: {e}")
        elif msg_type == "video": # Tratamento genérico para mídia, pode ser expandido
            try:
                # Usando st.image para link de vídeo gerado pela API (que na verdade é uma imagem estática)
                st.image(content, caption="🎬 Mídia gerada pela IA") 
            except Exception as e:
                st.error(f"Erro ao exibir mídia: {e}")
        else: # Default para 'text'
            st.markdown(content)

# Input principal do usuário
texto_input = st.chat_input("Peça qualquer coisa: pesquise, crie imagens, faça perguntas...", key="main_chat_input")

if texto_input:
    texto_input_limpo = texto_input.strip()
    
    if not texto_input_limpo:
        st.warning("Por favor, digite algo para enviar.")
        st.stop() # Para o script aqui se o input for vazio

    # Adiciona mensagem do
