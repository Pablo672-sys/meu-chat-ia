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
# O formato foi levemente ajustado para incluir o nível do log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes de Arquivos
BANCO_USUARIOS_FILE = "usuarios_cadastrados.json"
LOG_USUARIO_ATIVO = "usuario_ativo.log" # Para tentar manter o último usuário logado

# Tenta carregar módulos opcionais com flags
HAS_BS4 = False
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
    logger.info("Módulo BeautifulSoup importado com sucesso. Pesquisa web estará habilitada.")
except ImportError:
    logger.warning("BeautifulSoup não instalado. Pesquisa web estará desativada. Instale com: pip install beautifulsoup4")

HAS_MIC = False
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
    logger.info("Módulo streamlit_mic_recorder importado com sucesso. Gravador de áudio estará habilitado.")
except ImportError:
    logger.warning("Mic recorder não instalado. Gravador de áudio estará desativado. Instale com: pip install streamlit-mic-recorder")

HAS_YT = False
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YT = True
    logger.info("Módulo YouTubeTranscriptApi importado com sucesso. Transcrição de YouTube estará habilitada.")
except ImportError:
    logger.warning("YouTube API não instalada. Transcrição de YouTube estará desativada. Instale com: pip install youtube-transcript-api")

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
    
    /* Estilos para mensagens de chat */
    div[data-testid="stChatMessage"] {
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.12) !important;
    }
    
    /* Usuário */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background: rgba(59, 130, 246, 0.06) !important;
    }
    
    /* Assistente */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background: rgba(128, 128, 128, 0.04) !important;
    }
    
    /* Botões principais */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    
    /* Container de login */
    .login-container {
        background: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }

    /* Esconder o ícone de re-run em mensagens (opcional, para um visual mais limpo) */
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
    """Carrega usuários do banco com tratamento de erro e validação de formato."""
    if os.path.exists(BANCO_USUARIOS_FILE):
        try:
            with open(BANCO_USUARIOS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
                if not isinstance(usuarios, dict): # Garante que é um dicionário
                    logger.error(f"Arquivo de usuários '{BANCO_USUARIOS_FILE}' corrompido ou formato inválido. Resetando para padrão.")
                    # Reseta para um estado seguro com um admin padrão
                    senha_admin_hashed = hash_senha("admin123")
                    with open(BANCO_USUARIOS_FILE, "w", encoding="utf-8") as f_reset:
                        json.dump({"admin": senha_admin_hashed}, f_reset, ensure_ascii=False, indent=4)
                    return {"admin": senha_admin_hashed}
                return usuarios
        except json.JSONDecodeError:
            logger.error(f"Falha ao decodificar JSON do arquivo de usuários: '{BANCO_USUARIOS_FILE}'. Resetando.")
            senha_admin_hashed = hash_senha("admin123")
            try:
                with open(BANCO_USUARIOS_FILE, "w", encoding="utf-8") as f:
                    json.dump({"admin": senha_admin_hashed}, f, ensure_ascii=False, indent=4)
                return {"admin": senha_admin_hashed}
            except Exception as e_write:
                logger.error(f"Falha ao reescrever arquivo de usuários após erro de JSON: {e_write}")
                return {} # Retorna vazio em caso de falha crítica de escrita
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar usuários de '{BANCO_USUARIOS_FILE}': {e}")
            # Em caso de erro inesperado, tenta retornar um estado seguro
            try:
                with open(BANCO_USUARIOS_FILE, "r", encoding="utf-8") as f: # Tenta ler de novo
                    usuarios = json.load(f)
                    if isinstance(usuarios, dict): return usuarios
            except: pass # Ignora se a leitura de fallback falhar
            return {"admin": hash_senha("admin123")} # Retorna padrão se tudo falhar
    else:
        # Cria o arquivo com um usuário admin padrão se não existir
        logger.info(f"Arquivo de usuários '{BANCO_USUARIOS_FILE}' não encontrado. Criando com usuário 'admin' (senha: admin123).")
        senha_admin_hashed = hash_senha("admin123")
        try:
            with open(BANCO_USUARIOS_FILE, "w", encoding="utf-8") as f:
                json.dump({"admin": senha_admin_hashed}, f, ensure_ascii=False, indent=4)
            return {"admin": senha_admin_hashed}
        except Exception as e:
            logger.error(f"Falha ao criar arquivo de usuários padrão '{BANCO_USUARIOS_FILE}': {e}")
            return {} # Retorna vazio em caso de falha crítica

def salvar_usuario(novo_usuario: str, nova_senha: str) -> bool:
    """Salva novo usuário com senha hasheada, verificando se o usuário já existe."""
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
        logger.error(f"Erro ao salvar usuário '{novo_usuario}' no arquivo '{BANCO_USUARIOS_FILE}': {e}")
        return False

def carregar_ultimo_usuario_logado() -> Optional[str]:
    """Tenta carregar o último usuário logado de um arquivo de log."""
    if os.path.exists(LOG_USUARIO_ATIVO):
        try:
            with open(LOG_USUARIO_ATIVO, "r", encoding="utf-8") as f:
                usuario = f.read().strip()
                if usuario:
                    logger.info(f"Último usuário logado encontrado: '{usuario}'.")
                    return usuario
        except Exception as e:
            logger.error(f"Erro ao carregar último usuário logado de '{LOG_USUARIO_ATIVO}': {e}")
    return None

def salvar_ultimo_usuario_logado(usuario: str):
    """Salva o usuário logado atual em um arquivo."""
    try:
        with open(LOG_USUARIO_ATIVO, "w", encoding="utf-8") as f:
            f.write(usuario)
        logger.info(f"Último usuário logado salvo: '{usuario}'.")
    except Exception as e:
        logger.error(f"Erro ao salvar último usuário logado '{usuario}' em '{LOG_USUARIO_ATIVO}': {e}")

# Inicialização do estado da sessão para controle de login e chats
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

# Tenta carregar o último usuário logado para preencher o campo de login
ultimo_usuario_logado = carregar_ultimo_usuario_logado()
if ultimo_usuario_logado:
    st.session_state.usuario_atual = ultimo_usuario_logado # Preenche o campo, mas não loga automaticamente

# --- Tela de Login/Cadastro ---
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
                        salvar_ultimo_usuario_logado(user_login) # Salva o usuário logado
                        st.success("✅ Login realizado com sucesso! Bem-vindo(a) de volta!")
                        time.sleep(1.5) # Pausa breve para o usuário ver a mensagem
                        st.rerun() # Recarrega a página para mostrar o app logado
                    else:
                        st.error("❌ Usuário ou senha incorretos! Tente novamente.")
                    
    with tab_cadastro:
        with st.form("form_cadastro", clear_on_submit=True):
            novo_user = st.text_input("Criar Usuário", placeholder="Escolha um nome de usuário (mín. 3 caracteres)").strip()
            nova_pass = st.text_input("Criar Senha", type="password", placeholder="Escolha uma senha forte (mín. 3 caracteres)")
            btn_cadastrar = st.form_submit_button("Cadastrar Conta", use_container_width=True)
            
            if btn_cadastrar:
                if not novo_user or not nova_pass:
                    st.error("⚠️ Usuário e senha são obrigatórios!")
                elif len(novo_user) < 3 or len(nova_pass) < 3:
                    st.warning("⚠️ Usuário e senha precisam ter no mínimo 3 caracteres.")
                else:
                    # Tenta salvar o novo usuário
                    if salvar_usuario(novo_user, nova_pass):
                        st.success("✅ Conta criada com sucesso! Agora você pode fazer Login.")
                        # Limpa os campos do formulário de cadastro
                        st.session_state.new_chat_input = "" # Limpa se o campo estava aberto
                    else:
                        # A função salvar_usuario já loga o erro específico
                        st.error("❌ Esse nome de usuário já existe ou ocorreu um erro ao salvar. Verifique as mensagens de log ou tente outro nome.")
                    
    st.stop() # Bloqueia a execução do restante do script se o usuário não estiver logado

# ==========================================
# 3. GERENCIADOR DE CHATS (Por Usuário)
# ==========================================
def get_chat_file_path(usuario: str) -> str:
    """Retorna o caminho do arquivo JSON de chats para um usuário específico."""
    # Garante que o nome do usuário seja usado de forma segura no nome do arquivo
    safe_usuario_name = re.sub(r'[^\w\-_\. ]', '_', usuario) # Substitui caracteres não permitidos
    return f"chats_salvos_{safe_usuario_name}.json"

def carregar_todos_chats(usuario: str) -> Dict[str, List[Dict[str, Any]]]:
    """Carrega todos os chats de um usuário com validação robusta da estrutura dos dados."""
    arquivo_chats = get_chat_file_path(usuario)
    try:
        if os.path.exists(arquivo_chats):
            with open(arquivo_chats, "r", encoding="utf-8") as f:
                chats_data = json.load(f)
                
                # Validação profunda da estrutura dos dados carregados
                if not isinstance(chats_data, dict):
                    logger.error(f"Formato inválido no arquivo de chats '{arquivo_chats}'. Resetando para padrão.")
                    return {"Chat Principal": []}
                
                # Garante que sempre exista o "Chat Principal"
                if "Chat Principal" not in chats_data:
                    chats_data["Chat Principal"] = []
                
                # Valida cada chat e suas mensagens
                chats_validados = {}
                for chat_name, messages in chats_data.items():
                    if not isinstance(messages, list):
                        logger.warning(f"Chat '{chat_name}' em '{arquivo_chats}' tem formato inválido (não é lista). Resetando.")
                        chats_validados[chat_name] = []
                    else:
                        # Valida cada mensagem individualmente
                        mensagens_validas = []
                        for msg in messages:
                            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                                mensagens_validas.append(msg)
                            else:
                                logger.warning(f"Mensagem inválida encontrada no chat '{chat_name}' do arquivo '{arquivo_chats}': {msg}. Ignorando.")
                        chats_validados[chat_name] = mensagens_validas
                
                # Adiciona o Chat Principal se ele foi resetado e não foi incluído na iteração
                if "Chat Principal" not in chats_validados:
                     chats_validados["Chat Principal"] = []

                return chats_validados
        else:
            # Arquivo não existe, cria com um chat principal vazio
            logger.info(f"Arquivo de chats '{arquivo_chats}' não encontrado. Criando novo com 'Chat Principal'.")
            return {"Chat Principal": []} 
            
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do arquivo de chats '{arquivo_chats}'. O arquivo pode estar corrompido. Resetando.")
        # Em caso de erro de JSON, tenta salvar um estado padrão
        try:
            with open(arquivo_chats, "w", encoding="utf-8") as f:
                json.dump({"Chat Principal": []}, f, ensure_ascii=False, indent=4)
            return {"Chat Principal": []}
        except Exception as e_write:
            logger.error(f"Falha ao reescrever arquivo de chats após erro de JSON: {e_write}")
            return {} # Retorna vazio se não conseguir nem reescrever
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar chats de '{arquivo_chats}': {e}")
        # Tenta retornar um estado seguro
        return {"Chat Principal": []} 

def salvar_todos_chats(usuario: str, todos_chats: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Salva todos os chats de um usuário em um arquivo JSON com tratamento de erro."""
    if not isinstance(todos_chats, dict):
        logger.error("Tentativa de salvar dados de chat em formato inválido (não é um dicionário).")
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
@st.cache_data(show_spinner=False, ttl=3600) # Cache das pesquisas web por 1 hora
def pesquisar_na_web(termo: str) -> str:
    """Pesquisa na web via DuckDuckGo e retorna snippets relevantes."""
    if not HAS_BS4:
        logger.warning("Pesquisa web desativada: BeautifulSoup não está instalado.")
        return "Pesquisa web indisponível (BeautifulSoup não instalado). Instale com `pip install beautifulsoup4`."
    
    termo_limpo = termo.strip()
    if len(termo_limpo) < 2: # Termo muito curto, provavelmente não é uma pesquisa válida
        return ""
    
    try:
        # Define headers para simular um navegador real
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url_encoded = urllib.parse.quote(termo_limpo)
        url = f"https://html.duckduckgo.com/html/?q={url_encoded}"
        
        response = requests.get(url, headers=headers, timeout=10) # Timeout de 10 segundos
        response.raise_for_status() # Lança exceção para códigos de erro HTTP (4xx, 5xx)
        
        soup = BeautifulSoup(response.text, "html.parser")
        snippets = []
        
        # Tentativa de encontrar os resultados usando seletores comuns do DuckDuckGo
        # Estes seletores podem precisar de ajuste se o layout do DuckDuckGo mudar
        div_resultados = soup.find_all("div", class_="result__body")
        if not div_resultados: # Tenta um seletor alternativo se o primeiro falhar
            div_resultados = soup.find_all("a", class_="result__a") 
        
        for item in div_resultados[:5]: # Pega os 5 primeiros resultados
            snippet_tag = item.find("span", class_="result__snippet")
            if snippet_tag:
                texto = snippet_tag.get_text().strip()
                if texto and len(texto) > 10: # Garante que o snippet não seja vazio ou muito curto
                    snippets.append(f"• {texto[:250]}{'...' if len(texto) > 250 else ''}") # Limita o tamanho
            else:
                # Se não houver snippet, tenta pegar o texto do link principal
                link_tag = item.find("a", class_="result__a")
                if link_tag:
                    texto_link = link_tag.get_text().strip()
                    if texto_link and len(texto_link) > 10:
                         snippets.append(f"• {texto_link[:250]}{'...' if len(texto_link) > 250 else ''}")

        if not snippets:
            logger.info(f"Nenhum snippet relevante encontrado para '{termo_limpo}' na pesquisa web.")
            return "" # Retorna vazio se nenhum resultado útil for encontrado
            
        return "\n".join(snippets)

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout ao tentar pesquisar na web por '{termo_limpo}'.")
        return "Erro: A pesquisa na web demorou demais para responder (Timeout)."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao pesquisar na web por '{termo_limpo}': {e}")
        return f"Erro ao acessar a pesquisa na web: {e}"
    except Exception as e:
        logger.error(f"Erro inesperado ao processar pesquisa web para '{termo_limpo}': {e}")
        return "Ocorreu um erro inesperado durante a pesquisa na web. Tente novamente."

def extrair_texto_youtube(prompt_texto: str) -> str:
    """Extrai a transcrição de um link do YouTube se ele estiver presente no prompt."""
    if not HAS_YT:
        logger.warning("Extrator de YouTube desativado: YouTubeTranscriptApi não está instalado.")
        return ""
    
    # Expressão regular para capturar IDs de vídeo do YouTube em vários formatos
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=|embed\/|v\/|shorts\/|)([\w-]{11})(?:\S+)?'
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, prompt_texto)
        if match:
            video_id = match.group(1)
            if len(video_id) == 11: # IDs de vídeo do YouTube têm 11 caracteres
                break # Encontrou um ID válido, para a busca
    
    if not video_id:
        # logger.debug("Nenhum link de vídeo do YouTube detectado no prompt.") # Log muito verboso, descomente se precisar depurar
        return "" # Retorna string vazia se nenhum link for encontrado

    try:
        logger.info(f"Tentando extrair transcrição para o vídeo ID: {video_id}")
        
        # Lista as transcrições disponíveis para o vídeo
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        # Tenta encontrar transcrições em português, inglês ou espanhol na ordem de preferência
        try:
            transcript = transcript_list.find_transcript(['pt', 'en', 'es'])
            logger.info(f"Encontrada transcrição manual em: {transcript.language}")
        except Exception: # Se falhar, tenta pegar uma transcrição gerada automaticamente
             logger.warning(f"Não foi possível encontrar transcrição manual em PT/EN/ES para o vídeo {video_id}. Tentando transcrição gerada.")
             try:
                 transcript = transcript_list.find_generated_transcript(['en']) # Tenta gerada em inglês como fallback
                 logger.info(f"Encontrada transcrição gerada em: {transcript.language}")
             except Exception as e_gen:
                 logger.warning(f"Não foi possível encontrar transcrição gerada para o vídeo {video_id}. Erro: {e_gen}")
                 return "" # Se nem gerada funcionar, retorna vazio

        if not transcript:
             logger.warning(f"Nenhuma transcrição (manual ou gerada) encontrada para o vídeo ID: {video_id}")
             return ""
             
        # Busca o conteúdo da transcrição e concatena
        transcript_content = transcript.fetch()
        texto_completo = " ".join([t['text'] for t in transcript_content])
        
        # Limita o tamanho do texto para não sobrecarregar a IA principal
        return texto_completo[:3000] # Retorna os primeiros 3000 caracteres
        
    except Exception as e:
        logger.error(f"Erro ao extrair transcrição do YouTube para o vídeo ID '{video_id}': {e}")
        return f"Erro ao obter transcrição do YouTube: {e}" # Informa o erro ao usuário

def gerar_url_midia(prompt_texto: str, tipo: str = "imagem") -> str:
    """Gera uma URL para mídia (imagem ou vídeo) usando a API Pollinations.ai."""
    if not prompt_texto:
        return ""
        
    try:
        prompt_limitado = prompt_texto[:150] # Limita o tamanho do prompt para evitar problemas
        encoded_prompt = urllib.parse.quote(prompt_limitado) # Codifica o prompt para a URL
        
        seed = int(time.time()) % 1000000 # Gera uma semente aleatória baseada no tempo
        
        # Define dimensões padrão
        largura, altura = 1024, 1024
        prompt_lc = prompt_limitado.lower()
        
        # Lógica para ajustar dimensões com base em palavras-chave no prompt
        if any(x in prompt_lc for x in ["1920x1080", "widescreen", "hd", "paisagem", "landscape", "horizontal"]):
            largura, altura = 1280, 720
        elif any(x in prompt_lc for x in ["retrato", "vertical", "celular", "mobile", "portrait"]):
            largura, altura = 720, 1280
        elif any(x in prompt_lc for x in ["quadrado", "square"]):
             largura, altura = 1080, 1080
        
        # Seleciona o modelo da API: 'flux' é bom para imagens estáticas, 'turbo' para vídeos/animações
        modelo = "flux" if tipo == "imagem" else "turbo"
        
        # Monta a URL com parâmetros seguros
        base_url = "https://image.pollinations.ai/prompt/"
        params = {
            "seed": seed,
            "width": largura,
            "height": altura,
            "model": modelo,
            "nologo": "true" # Remove o logo da Pollinations da imagem/vídeo
        }
        
        # Codifica os parâmetros da URL
        params_encoded = "&".join([f"{key}={urllib.parse.quote(str(value))}" for key, value in params.items()])
        
        url_gerada = f"{base_url}{encoded_prompt}?{params_encoded}"
        
        logger.info(f"URL de mídia gerada ({tipo}): {url_gerada[:100]}...") # Loga parte da URL gerada
        return url_gerada
        
    except Exception as e:
        logger.error(f"Erro ao gerar URL de mídia com prompt '{prompt_texto[:50]}...': {e}")
        return "" # Retorna string vazia em caso de falha

# ==========================================
# 5. CÉREBRO COMPLETO DA IA (SEM CHAVE)
# ==========================================
# Cache para as respostas da IA principal para evitar chamadas redundantes
# TTL (Time To Live): 3600 segundos = 1 hora. Ajustável.
@st.cache_data(show_spinner=False, ttl=3600) 
def chamar_ia_suprema_cached(prompt_usuario: str, contexto_web: str, contexto_yt: str) -> str:
    """
    Chama a IA principal (via API) e retorna a resposta.
    Utiliza cache para evitar chamadas repetidas com os mesmos inputs.
    """
    
    p_clean = prompt_usuario.lower().strip()

    # Respostas rápidas para saudações e agradecimentos comuns (melhora a experiência)
    saudacoes_comuns = ["oi", "olá", "ola", "tudo bem", "e ai", "fala", "salve", "beleza", "bom dia", "boa tarde", "boa noite", "opa"]
    if any(s in p_clean for s in saudacoes_comuns) and len(p_clean) < 25:
        return "Opa! Tudo certo por aí. O que você quer pesquisar agora, mano?"

    agradecimentos = ["obrigado", "valeu", "tmj", "brigadão", "vlw", "obrigada"]
    if any(a in p_clean for a in agradecimentos) and len(p_clean) < 15:
        return "Tamo junto! Precisando é só mandar a letra."

    # Constrói o prompt do sistema com as informações coletadas
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

    # Prepara o payload para a API de texto
    payload = {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt_usuario}
        ],
        # O modelo pode precisar ser ajustado dependendo da API disponível
        # "model": "openai" # Exemplo de modelo, pode ser outro
    }
    
    # Endpoint da API de texto (Pollinations.ai) - Verifique se é o correto
    api_url = "https://text.pollinations.ai/" 
    
    try:
        logger.info(f"Enviando prompt para a IA principal via POST para: {api_url}")
        response = requests.post(api_url, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=45) # Timeout maior (45s) para a IA
        response.raise_for_status() # Verifica se a requisição foi bem-sucedida (código 2xx)

        resposta_api = response.text.strip()

        # Verificações comuns de erros da API
        if "402 Payment Required" in resposta_api or "You sent too many requests" in resposta_api:
            logger.warning("API de texto retornou erro de pagamento ou limite de requisições.")
            raise Exception("Limite de requisições ou pagamento necessário para a API de texto.")
        elif not resposta_api or len(resposta_api) < 10:
            logger.warning("API de texto retornou uma resposta vazia ou muito curta.")
            raise Exception("API de texto retornou dados insuficientes.")
        
        logger.info("Resposta da IA principal recebida e processada com sucesso.")
        return resposta_api

    except requests.exceptions.Timeout:
        logger.warning("Timeout ao chamar a API de texto (IA principal).")
        return "Erro: A IA demorou demais para responder. Tente novamente em alguns instantes."
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de requisição ao chamar a IA principal: {e}")
        return f"Erro na comunicação com a IA principal: {e}. Verifique a conexão ou tente mais tarde."
    except Exception as e:
        logger.error(f"Erro inesperado ao chamar a IA principal: {e}")
        # Implementa um fallback para a pesquisa web se a IA falhar
        if contexto_web:
            logger.info("IA principal falhou, retornando fallback da pesquisa web.")
            return f"Desculpe, tive um problema para processar sua solicitação com a IA. Aqui estão os resultados da pesquisa na web que consegui:\n\n{contexto_web}"
        else:
            return "Ocorreu um erro inesperado e não consegui obter uma resposta. Por favor, tente reformular sua pergunta ou verifique os logs para mais detalhes."

def chamar_ia_suprema(historico_mensagens: List[Dict[str, Any]], prompt_usuario: str) -> str:
    """
    Função principal para interagir com a IA.
    Orquestra a coleta de contexto (web, YT) e a chamada da IA (com cache).
    """
    
    # 1. Coleta de contexto: Realiza as buscas antes de chamar a IA principal
    contexto_web = pesquisar_na_web(prompt_usuario)
    contexto_yt = extrair_texto_youtube(prompt_usuario)
    
    # 2. Chama a função cacheada que interage com a API da IA
    # A função `chamar_ia_suprema_cached` gerencia o cache e a chamada real da API.
    resposta_ia = chamar_ia_suprema_cached(prompt_usuario, contexto_web, contexto_yt)
    
    # 3. Retorna a resposta final da IA
    return resposta_ia

# ==========================================
# 6. CONTROLE DO PAINEL LATERAL (SIDEBAR)
# ==========================================
# Carrega todos os chats salvos para o usuário atualmente logado
conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

# Garante que o chat selecionado pelo usuário exista no dicionário de chats
if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = "Chat Principal" # Se não existir, volta para o principal
    logger.info(f"Chat selecionado '{st.session_state.chat_selecionado}' não foi encontrado nos dados carregados. Resetado para 'Chat Principal'.")

# Obtém a lista de mensagens do chat que está atualmente selecionado
mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

# --- Configuração da Sidebar ---
st.sidebar.title("🛸 PAINEL DE CONTROLE")
operador_nome = str(st.session_state.usuario_atual).upper()
st.sidebar.write(f"Operador: **{operador_nome}**")

# Botão de Logout
if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario_atual = ""
    salvar_ultimo_usuario_logado("") # Limpa o log do último usuário
    logger.info("Usuário deslogado.")
    st.rerun()

# --- Componente de Microfone (com tratamento de erro) ---
if HAS_MIC:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Entrada de Voz")
    
    try:
        # Inicializa o gravador de áudio
        audio_data = mic_recorder(
            start_prompt="🔊 Gravar",
            stop_prompt="⏹️ Parar e Processar",
            key='gravador_chamada_principal', # Chave única para o componente
            use_container_width=True,
            sample_rate=44100 # Sample rate comum para áudio
        )
        
        # Processa os dados de áudio se a gravação foi concluída
        if audio_data:
            # AQUI VOCÊ ADICIONARIA A LÓGICA DE TRANSCRIÇÃO SE TIVER BIBLIOTECAS E FUNÇÕES PRONTAS
            # Exemplo:
            # try:
            #     # Certifique-se de ter uma função 'transcrever_audio' definida em algum lugar
            #     # E as bibliotecas necessárias (e.g., SpeechRecognition, pydub, ffmpeg)
            #     texto_transcrito = transcrever_audio(audio_data) 
            #     st.sidebar.text_area("Texto Transcrito:", value=texto_transcrito, height=100)
            #     # Você poderia então inserir 'texto_transcrito' no input principal
            #     # st.session_state.main_chat_input = texto_transcrito # Isso requer um pouco mais de lógica para funcionar
            # except Exception as e:
            #     st.sidebar.error(f"Erro ao transcrever áudio: {e}")
            #     logger.error(f"Erro durante a transcrição de áudio: {e}")
            
            st.sidebar.info("✅ Áudio capturado. O processamento de voz está em desenvolvimento.")
            logger.info("Áudio capturado com sucesso pelo mic_recorder.")

    except TypeError as e:
        # Captura o erro específico do mic_recorder
        logger.error(f"Erro de TypeError ao inicializar o mic_recorder: {e}. O componente de áudio foi desativado temporariamente.")
        st.sidebar.warning("⚠️ O gravador de voz não pôde ser iniciado devido a um erro interno. Componente desativado.")
        # Para evitar que o erro se repita nesta sessão, podemos "desativar" o HAS_MIC virtualmente
        # MAS A CAUSA RAÍZ DO TYPEERROR DEVE SER INVESTIGADA (versão do streamlit, dependências)
        # Se o problema persistir, talvez seja necessário remover ou reinstalar o componente.
        
    except Exception as e:
        # Captura qualquer outro erro inesperado relacionado ao mic_recorder
        logger.error(f"Erro inesperado ao usar o mic_recorder: {e}")
