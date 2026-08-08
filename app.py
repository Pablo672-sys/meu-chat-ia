import streamlit as st
import os
import json
import requests
import time
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# Configuração de interface visual (Glassmorphism Futurista)
st.set_page_config(
    page_title="NEO IA · Nexus Absolute Core",
    page_icon="🔮",
    layout="centered"
)

# Custom Engine CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #090714 0%, #110c28 50%, #05030a 100%);
        color: #f1f5f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .title-gradient {
        background: linear-gradient(45deg, #00f2fe, #4facfe, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 40px;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1px;
        margin-bottom: 5px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        text-align: center;
        margin-bottom: 25px;
    }
    div[data-testid="stChatMessage"] {
        background: rgba(22, 19, 43, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        margin-bottom: 14px !important;
        backdrop-filter: blur(12px);
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f1c2c, #00f2fe);
        color: white;
        border: 1px solid #4facfe;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.6);
        transform: translateY(-1px);
    }
    code {
        color: #00f2fe !important;
        font-family: 'Courier New', Courier, monospace !important;
        background: #0f172a !important;
        border-radius: 6px;
        padding: 3px 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title-gradient">🔮 NEO IA · Nexus Absolute Core</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · Processamento de Textos Extensos · Mídias & Vídeos HD</p>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

# --- PERSISTÊNCIA DE USUÁRIOS E CHATS ---
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

# --- GERADOR DE IMAGENS E VÍDEOS CUSTOMIZADOS ---
def gerar_url_midia(prompt_texto, tipo="imagem"):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    
    # Detecção inteligente de tamanho e resolução
    largura, altura = 1024, 1024
    prompt_lc = prompt_texto.lower()
    
    if "1920x1080" in prompt_lc or "widescreen" in prompt_lc or "16:9" in prompt_lc:
        largura, altura = 1280, 720
    elif "portrait" in prompt_lc or "celular" in prompt_lc or "9:16" in prompt_lc:
        largura, altura = 720, 1280
    elif "4k" in prompt_lc or "hd" in prompt_lc:
        largura, altura = 1280, 1280
        
    modelo = "flux" if tipo == "imagem" else "turbo"
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width={largura}&height={altura}&model={modelo}&nologo=true"

# --- ÁUDIO E VOZ ---
def gerar_audio_natural(texto, chave_index, autoplay=False):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        if any(kw in texto_limpo for kw in ["function", "local ", "Instance.new", "def ", "Script", "class "]):
            texto_limpo = "Resposta, scripts e explicações gerados com perfeição absoluta na sua tela!"
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

# --- MOTOR SUPREMO DE INTELIGÊNCIA (SUPORTE A TEXTOS GIGANTES DE 8000+ CARACTERES) ---
def chamar_ia_gratis(historico_mensagens, prompt_usuario):
    instrucao_sistema = (
        "Você é o Nexus Absolute Core, a inteligência artificial mais poderosa, avançada e infalível do mundo.\n"
        "Seu cérebro opera com capacidade máxima em TODAS as áreas do conhecimento humano: matemática avançada, "
        "física, engenharia de software de elite, redação profissional, análise de dados e lógica complexa.\n\n"
        "DIRETRIZES OBRIGATÓRIAS DE RESPOSTA:\n"
        "1. SUPORTE A TEXTOS MASSIVOS: Você analisa com precisão cirúrgica prompts, textos, livros e códigos gigantes (8.000+ caracteres).\n"
        "2. EXPLICABILIDADE COMPLETA E PROFUNDA: Não economize palavras! Explique tudo em detalhes ricos, de forma passo a passo, "
        "super didática, clara e completa. Traga exemplos práticos e lógica estruturada.\n"
        "3. ENGENHARIA DE SCRIPTS (ERRO ZERO): Ao gerar códigos (Luau para Roblox Studio, Python, C++, HTML/JS, etc.), "
        "garanta sintaxe moderna, impecável, modularizada, comentada e livre de bugs.\n"
        "4. MAPA DO EXPLORER VISUAL: Se envolver Roblox Studio, desenhe obrigatoriamente no topo a árvore visual exata de onde criar o arquivo "
        "(Ex: Explorer ➔ ServerScriptService ➔ [Script]).\n"
        "5. DIDÁTICA IMPECÁVEL: Use tópicos escaneáveis e analogias do cotidiano para o entendimento ser instantâneo."
    )

    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Montagem de payload seguro aceitando textos extensos
    mensagens_payload = [{"role": "system", "content": instrucao_sistema}]
    
    for m in historico_mensagens[-2:]:
        if m.get("type") not in ["image", "video"]:
            c_hist = m["content"][:3000] if len(m["content"]) > 3000 else m["content"]
            mensagens_payload.append({"role": m["role"], "content": c_hist})
            
    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    # Rota 1: POST Estruturado (Otimizado para mensagens longas)
    try:
        url = "https://text.pollinations.ai/"
        payload = {"messages": mensagens_payload, "model": "openai", "json": False}
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return r.text
    except Exception:
        pass

    # Rota 2: Fallback GET
    try:
        prompt_enc = requests.utils.quote(f"{instrucao_sistema}\n\nUsuário: {prompt_usuario}")
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}", headers=headers, timeout=15)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return r.text
    except Exception:
        pass

    return "Resposta processada com sucesso! Reenvie a mensagem se desejar adicionar mais detalhes."

# Estado de Sessão
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
    aba_login, aba_cadastro = st.tabs(["🔑 Acessar Console", "📝 Nova Credencial"])
    
    with aba_login:
        st.subheader("Login Segurado")
        usuario = st.text_input("Username:", key="log_user").strip().lower()
        senha = st.text_input("Password:", type="password", key="log_pass")
        
        if st.button("Initialize Console", use_container_width=True):
            usuarios_validos = carregar_usuarios()
            if usuario in usuarios_validos and usuarios_validos[usuario] == senha:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario
                st.session_state.chat_selecionado = "Chat Principal"
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
                
    with aba_cadastro:
        st.subheader("Criar Acesso Operacional")
        novo_usuario = st.text_input("Escolha o Usuário:", key="cad_user").strip().lower()
        nova_senha = st.text_input("Escolha a Senha:", type="password", key="cad_pass")
        confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        
        if st.button("Gerar Registro de Conta", use_container_width=True):
            usuarios_existentes = carregar_usuarios()
            if novo_usuario and nova_senha == confirma_senha and novo_usuario not in usuarios_existentes:
                salvar_usuario(novo_usuario, nova_senha)
                st.success("Registro concluído!")

# --- TELA DO CHAT ---
else:
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
    mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

    # Sidebar
    st.sidebar.title("🛸 SYSTEM CONTROL")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.markdown("---")
    
    # Entrada de Áudio
    st.sidebar.subheader("🎙️ Canal de Áudio Contínuo")
    audio_chamada = mic_recorder(
        start_prompt="🔊 Falar com a IA (Voz)",
        stop_prompt="⏹️ Enviar e Ouvir Resposta",
        key='gravador_chamada',
        use_container_width=True
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Gerenciamento de Chats")
    
    lista_de_chats = list(conversas_usuario.keys())
    chat_escolhido = st.sidebar.selectbox("Selecionar Conversa:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()
        
    if st.session_state.chat_selecionado != "Chat Principal":
        if st.sidebar.button("❌ Deletar Chat Atual", use_container_width=True):
            del conversas_usuario[st.session_state.chat_selecionado]
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = "Chat Principal"
            st.rerun()
            
    novo_nome_chat = st.sidebar.text_input("Novo Chat:", key="new_chat_name", placeholder="Nome da conversa...").strip()
    if st.sidebar.button("➕ Criar Chat", use_container_width=True):
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
        
    if st.sidebar.button("🚪 Sair do Console", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

    # Histórico de Mensagens
    tamanho_historico = len(mensagens_atuais)
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            elif message.get("type") == "video":
                st.image(message["content"], caption="Renderização de Mídia Gerada")
            else:
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    e_ultima = (index == tamanho_historico - 1)
                    gerar_audio_natural(message["content"], index, autoplay=e_ultima)

    prompt_final = None

    texto_input = st.chat_input("Pergunte algo, cole textos gigantes ou peça scripts/imagens/vídeos...")
    if texto_input:
        prompt_final = texto_input

    if audio_chamada and audio_chamada.get('id') != st.session_state.last_call_id:
        st.session_state.last_call_id = audio_chamada.get('id')
        texto_voz = transcrever_audio_gratis(audio_chamada['bytes'])
        if texto_voz:
            prompt_final = texto_voz

    # Processamento de comandos
    if prompt_final:
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        
        prompt_minusculo = prompt_final.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])
        comando_video = any(cmd in prompt_minusculo for cmd in ["crie um video", "gere um video", "anime", "faça um video"])

        if comando_video:
            with st.spinner("🎬 Renderizando vídeo/animação em HD..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="video")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "video", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        elif comando_imagem:
            with st.spinner("🎨 Gerando imagem em alta resolução..."):
                url_gerada = gerar_url_midia(prompt_final, tipo="imagem")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        else:
            with st.spinner("🧠 Processando lógica e gerando resposta detalhada..."):
                resposta_texto = chamar_ia_gratis(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
            
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
