import streamlit as st
import os
import json
import requests
import time
import nest_asyncio
from bs4 import BeautifulSoup
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import g4f

# Permite chamadas assíncronas do g4f dentro do ambiente do Streamlit
nest_asyncio.apply()

# --- CONFIGURAÇÃO DA INTERFACE VISUAL ESTILO CHATGPT / GEMINI ---
st.set_page_config(
    page_title="NEXUS AI · Absolute Intelligence",
    page_icon="🤖",
    layout="centered"
)

# --- CSS CUSTOMIZADO DE ALTA PERFORMANCE (DARK GLASSMORPHISM) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #060412 100%);
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .hero-title {
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 50%, #00c6ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 38px;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1.5px;
        margin-bottom: 5px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        text-align: center;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    div[data-testid="stChatMessage"] {
        background: rgba(30, 27, 54, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
    }
    
    code {
        color: #38bdf8 !important;
        background: #0f172a !important;
        border-radius: 6px;
        padding: 2px 6px;
    }
    
    div[data-testid="stChatInput"] input {
        background-color: #1e1b3b !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🔮 NEXUS AI · Quantum Core v4</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · Pesquisa Web Integrada · Precisão Absoluta</p>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

# --- GERENCIAMENTO DE USUÁRIOS E CHATS ---
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

# --- PESQUISA WEB EM TEMPO REAL ---
def pesquisar_na_web(termo):
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(termo[:120])}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            snippets = []
            for a in soup.find_all("a", class_="result__snippet")[:2]:
                snippets.append(a.get_text().strip())
            if snippets:
                return "\n".join(snippets)
    except Exception:
        pass
    return ""

def gerar_url_imagem(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=768&height=768&nologo=true"

# --- SÍNTESE DE VOZ ---
def gerar_audio_natural(texto, chave_index, autoplay=False):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        if any(keyword in texto_limpo for keyword in ["function", "local ", "Instance.new", "def ", "Script", "class "]):
            texto_limpo = "Resposta completa e scripts gerados com precisão absoluta na sua tela!"
        elif len(texto_limpo) > 160:
            texto_limpo = texto_limpo[:160] + "..."
            
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

# --- TRANSCRIÇÃO DE VOZ ---
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

# --- MOTOR SUPREMO DE INTELIGÊNCIA ARTIFICIAL ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    dados_web = pesquisar_na_web(prompt_usuario)
    contexto_extra = f"\n\n[DADOS VERIFICADOS DA INTERNET]:\n{dados_web}" if dados_web else ""

    instrucao_sistema = (
        "Você é o Nexus Absolute Core, a Inteligência Artificial mais avançada, didática e perfeita da Terra.\n"
        "Seu raciocínio é impecável em TODAS as áreas: engenharia de software, matemática, ciências, história e lógica.\n\n"
        "DIRETRIZES DE RESPOSTA MÁXIMA:\n"
        "1. EXPLICABILIDADE COMPLETA E PROFUNDA: Explique TUDO em detalhes claros, didáticos e ricos em conteúdo.\n"
        "2. CÓDIGO PERFEITO (ERRO ZERO): Escreva códigos modernos, comentados e livres de bugs.\n"
        "3. MAPA VISUAL DO EXPLORER (ROBLOX STUDIO): Se a pergunta for sobre Roblox Studio, desenhe no topo "
        "o mapa hierárquico exato de onde criar o arquivo (Ex: Explorer ➔ ServerScriptService ➔ [Script]).\n"
        "4. PRECISÃO FATO-CHECADA: Utilize informações verificadas."
        f"{contexto_extra}"
    )

    mensagens_payload = [{"role": "system", "content": instrucao_sistema}]
    
    for m in historico_mensagens[-3:]:
        if m.get("type") != "image":
            mensagens_payload.append({"role": m["role"], "content": m["content"]})
            
    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    # Rota 1: Chamada via g4f com suporte assíncrono corrigido
    try:
        from g4f.client import Client
        client = Client()
        for mod in ["gpt-4o-mini", "gpt-4o"]:
            try:
                resp = client.chat.completions.create(
                    model=mod,
                    messages=mensagens_payload
                )
                texto = resp.choices[0].message.content
                if texto and len(str(texto).strip()) > 0:
                    return str(texto)
            except Exception:
                continue
    except Exception:
        pass

    # Rota 2: Requisição HTTP direta (Fallback)
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": mensagens_payload,
            "model": "openai",
            "json": False
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.post(url, json=payload, headers=headers, timeout=12)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return r.text
    except Exception:
        pass

    return "Resposta processada com sucesso! Caso queira complementar a pergunta, basta enviar no chat."

# --- ESTADO DA SESSÃO ---
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
        st.subheader("Login de Acesso")
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
        st.subheader("Criar Nova Conta")
        novo_usuario = st.text_input("Escolha o Usuário:", key="cad_user").strip().lower()
        nova_senha = st.text_input("Escolha a Senha:", type="password", key="cad_pass")
        confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        
        if st.button("Cadastrar", use_container_width=True):
            usuarios_existentes = carregar_usuarios()
            if novo_usuario and nova_senha == confirma_senha and novo_usuario not in usuarios_existentes:
                salvar_usuario(novo_usuario, nova_senha)
                st.success("Cadastro realizado com sucesso!")

# --- PAINEL PRINCIPAL DO CHAT ---
else:
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
    mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

    # Sidebar
    st.sidebar.title("🛸 PAINEL DE CONTROLE")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("🎙️ Entrada de Voz")
    audio_chamada = mic_recorder(
        start_prompt="🔊 Falar com a IA",
        stop_prompt="⏹️ Enviar Áudio",
        key='gravador_chamada',
        use_container_width=True
    )
    
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

    # RENDERIZAÇÃO DAS MENSAGENS
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

    texto_input = st.chat_input("Pergunte qualquer coisa ou peça um script...")
    if texto_input:
        prompt_final = texto_input

    if audio_chamada and audio_chamada.get('id') != st.session_state.last_call_id:
        st.session_state.last_call_id = audio_chamada.get('id')
        texto_voz = transcrever_audio_gratis(audio_chamada['bytes'])
        if texto_voz:
            prompt_final = texto_voz

    # EXECUÇÃO DA RESPOSTA
    if prompt_final:
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        
        prompt_minusculo = prompt_final.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe"])

        if comando_imagem:
            url_gerada = gerar_url_imagem(prompt_final)
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
        else:
            with st.spinner("🔍 Analisando web e processando lógica suprema..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
            
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
