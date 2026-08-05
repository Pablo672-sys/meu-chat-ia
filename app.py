import streamlit as st
import os
import json
import requests
import time
from bs4 import BeautifulSoup
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# --- CONFIGURAÇÃO DA INTERFACE VISUAL ---
st.set_page_config(
    page_title="NEXUS AI · Absolute Core",
    page_icon="🔮",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090714 0%, #110c28 50%, #05030a 100%);
        color: #f1f5f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .hero-title {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #7f00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        letter-spacing: -1.5px;
        margin-bottom: 4px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        text-align: center;
        margin-bottom: 25px;
        font-weight: 500;
    }
    div[data-testid="stChatMessage"] {
        background: rgba(22, 19, 43, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(12px);
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(59, 130, 246, 0.6);
    }
    code {
        color: #38bdf8 !important;
        background: #0f172a !important;
        border-radius: 6px;
        padding: 3px 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🔮 NEXUS AI · Absolute Core</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · Respostas Detalhadas · Imagens & Mídias</p>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

# --- PERSISTÊNCIA DE DADOS ---
def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"admin": "admin123"}
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    try:
        usuarios = carregar_usuarios()
        usuarios[novo_usuario] = nova_senha
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def get_chats_indices_file(usuario):
    return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_indices_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"Chat Principal": []}
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        arquivo = get_chats_indices_file(usuario)
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# --- RECURSOS EXTERNOS ---
def pesquisar_na_web(termo):
    try:
        termo_limpo = termo[:150]
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(termo_limpo)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = [a.get_text().strip() for a in soup.find_all("a", class_="result__snippet")[:2]]
            if snippets:
                return "\n".join(snippets)
    except Exception:
        pass
    return ""

def gerar_url_midia(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    largura, altura = 1024, 1024
    if "1920x1080" in prompt_texto or "widescreen" in prompt_texto.lower():
        largura, altura = 1280, 720
    elif "portrait" in prompt_texto.lower() or "celular" in prompt_texto.lower():
        largura, altura = 720, 1280
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width={largura}&height={altura}&model=flux&nologo=true"

def gerar_audio_natural(texto, chave_index, autoplay=False):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        if any(kw in texto_limpo for kw in ["function", "local ", "Instance.new", "def ", "Script", "class "]):
            texto_limpo = "Resposta e scripts gerados com sucesso na sua tela!"
        elif len(texto_limpo) > 180:
            texto_limpo = texto_limpo[:180] + "..."
            
        tts = gTTS(text=texto_limpo, lang='pt', tld='com.br', slow=False)
        filename = f"audio_resp_{chave_index}.mp3"
        tts.save(filename)
        
        with open(filename, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=autoplay)
        
        if os.path.exists(filename):
            os.remove(filename)
    except Exception:
        pass

def transcrever_audio_gratis(audio_bytes):
    try:
        url = "https://api.wit.ai/speech"
        headers = {
            "Authorization": "Bearer 7J56PZ4ZLQ4O2V3M5ZXZN4Z3ZXZNZXZN",
            "Content-Type": "audio/wav"
        }
        res = requests.post(url, headers=headers, data=audio_bytes, timeout=5)
        if res.status_code == 200:
            for linha in res.text.split('\n'):
                if linha.strip():
                    dados = json.loads(linha)
                    if "text" in dados:
                        return dados["text"]
    except Exception:
        pass
    return None

# --- PROCESSADOR DE CHAMADA DE IA (SEM DEPENDÊNCIA DE BIBLIOTECAS QUEBRADAS) ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    dados_web = pesquisar_na_web(prompt_usuario)
    contexto_extra = f"\n\n[DADOS VERIFICADOS DA WEB]:\n{dados_web}" if dados_web else ""

    instrucao_sistema = (
        "Você é o Nexus Absolute Core, uma IA avançada e direta.\n\n"
        "REGRAS:\n"
        "1. Explique com clareza e riqueza de detalhes.\n"
        "2. Escreva scripts limpos e sem erros (Roblox Luau, Python, C++, etc).\n"
        "3. Se for sobre Roblox Studio, mostre o mapa do Explorer no início (Ex: Explorer ➔ ServerScriptService ➔ Script)."
        f"{contexto_extra}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    messages_payload = [{"role": "system", "content": instrucao_sistema}]
    for m in historico_mensagens[-2:]:
        if m.get("type") not in ["image", "video"]:
            c_hist = m["content"][:1000] if len(m["content"]) > 1000 else m["content"]
            messages_payload.append({"role": m["role"], "content": c_hist})
    messages_payload.append({"role": "user", "content": prompt_usuario})

    # Tativa 1: POST Direto Otimizado
    try:
        r = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": messages_payload, "model": "openai"},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200 and len(r.text.strip()) > 5:
            return r.text
    except Exception:
        pass

    # Tentativa 2: GET Direto de Fallback
    try:
        prompt_enc = requests.utils.quote(f"{instrucao_sistema}\n\nUsuário: {prompt_usuario}")
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}", headers=headers, timeout=10)
        if r.status_code == 200 and len(r.text.strip()) > 5:
            return r.text
    except Exception:
        pass

    return "⚠️ Servidores públicos sobrecarregados neste instante. Por favor, reenvie a pergunta."

# --- GERENCIAMENTO DE ESTADO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"
if "last_call_id" not in st.session_state:
    st.session_state.last_call_id = None

# --- TELA DE AUTENTICAÇÃO ---
if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Console de Acesso", "📝 Novo Registro"])
    
    with aba_login:
        st.subheader("Autenticação Operacional")
        usuario = st.text_input("Usuário:", key="log_user").strip().lower()
        senha = st.text_input("Senha:", type="password", key="log_pass")
        
        if st.button("Iniciar Console", use_container_width=True):
            usuarios_validos = carregar_usuarios()
            if usuario in usuarios_validos and usuarios_validos[usuario] == senha:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario
                st.session_state.chat_selecionado = "Chat Principal"
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
                
    with aba_cadastro:
        st.subheader("Criar Acesso de Operador")
        novo_usuario = st.text_input("Escolha o Usuário:", key="cad_user").strip().lower()
        nova_senha = st.text_input("Escolha a Senha:", type="password", key="cad_pass")
        confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        
        if st.button("Registrar Credencial", use_container_width=True):
            usuarios_existentes = carregar_usuarios()
            if novo_usuario and nova_senha == confirma_senha and novo_usuario not in usuarios_existentes:
                salvar_usuario(novo_usuario, nova_senha)
                st.success("Operador registrado com sucesso!")

# --- PAINEL DO CHAT ---
else:
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
    mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

    st.sidebar.title("🛸 NEXUS CONTROL")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.markdown("---")
    
    audio_chamada = mic_recorder(
        start_prompt="🔊 Falar com a IA",
        stop_prompt="⏹️ Transcrever e Enviar",
        key='gravador_chamada',
        use_container_width=True
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Gerenciamento de Chats")
    
    lista_de_chats = list(conversas_usuario.keys())
    chat_escolhido = st.sidebar.selectbox("Selecionar Chat:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()
        
    if st.session_state.chat_selecionado != "Chat Principal":
        if st.sidebar.button("❌ Deletar Chat Atual", use_container_width=True):
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
        
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

    tamanho_historico = len(mensagens_atuais)
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            else:
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    e_ultima = (index == tamanho_historico - 1)
                    gerar_audio_natural(message["content"], index, autoplay=e_ultima)

    prompt_final = None

    texto_input = st.chat_input("Pergunte algo ou peça scripts/imagens...")
    if texto_input:
        prompt_final = texto_input

    if audio_chamada and audio_chamada.get('id') != st.session_state.last_call_id:
        st.session_state.last_call_id = audio_chamada.get('id')
        texto_voz = transcrever_audio_gratis(audio_chamada['bytes'])
        if texto_voz:
            prompt_final = texto_voz

    if prompt_final:
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        
        prompt_minusculo = prompt_final.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])

        if comando_imagem:
            with st.spinner("🎨 Gerando imagem..."):
                url_gerada = gerar_url_midia(prompt_final)
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        else:
            with st.spinner("🧠 Processando..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
            
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
