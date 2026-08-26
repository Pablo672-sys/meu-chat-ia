import streamlit as st
import os
import json
import requests
import time
import urllib.parse
import re

# ==========================================
# 1. DEPENDÊNCIAS E CONFIGURAÇÃO DA PÁGINA
# ==========================================
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

st.set_page_config(
    page_title="AI DO PABLO · Supreme Accuracy",
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
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Motor de Busca Real · Multi-Linguagem · Alta Precisão</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# 2. SISTEMA DE BANCO DE DADOS E LOGIN
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

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""

if not st.session_state.logado:
    st.markdown("### 🔐 Autenticação de Operador")
    tab_login, tab_cadastro = st.tabs(["Fazer Login", "Criar Nova Conta"])
    
    with tab_login:
        with st.form("form_login"):
            user_login = st.text_input("Usuário", placeholder="Seu nome de usuário").strip().lower()
            pass_login = st.text_input("Senha", type="password", placeholder="Sua senha")
            btn_entrar = st.form_submit_button("Entrar no Console", use_container_width=True)
            
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
            novo_user = st.text_input("Novo Usuário", placeholder="Escolha seu usuário").strip().lower()
            nova_pass = st.text_input("Nova Senha", type="password", placeholder="Escolha sua senha")
            btn_cadastrar = st.form_submit_button("Criar Registro", use_container_width=True)
            
            if btn_cadastrar:
                usuarios_db = carregar_usuarios()
                if novo_user in usuarios_db:
                    st.error("⚠️ Este usuário já existe.")
                elif len(novo_user) < 3 or len(nova_pass) < 3:
                    st.warning("⚠️ Mínimo de 3 caracteres.")
                else:
                    salvar_usuario(novo_user, nova_pass)
                    st.success("✅ Conta criada! Faça login na aba ao lado.")
                    
    st.stop()

# ==========================================
# 3. GERENCIADOR DE HISTÓRICO
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
# 4. FERRAMENTA DE PESQUISA EM TEMPO REAL
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
                    snippets.append(f"• {texto}")
            return "\n".join(snippets)
    except Exception:
        pass
    return ""

def gerar_url_imagem(prompt_texto):
    encoded_prompt = urllib.parse.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&model=flux&nologo=true"

# ==========================================
# 5. MOTOR DE RESPOSTA VIA POST
# ==========================================
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    p_clean = prompt_usuario.lower().strip()

    # Saudações imediatas
    saudacoes = ["oi", "olá", "ola", "tudo bem", "e ai", "fala", "salve", "boa tarde", "bom dia", "boa noite"]
    if any(p_clean == s for s in saudacoes):
        return "Fala, mano! AI DO PABLO no comando. O que precisa pesquisar, calcular ou programar hoje?"

    # Tenta buscar na web para perguntas sobre fatos ou notícias
    contexto_web = pesquisar_na_web(prompt_usuario)

    sys_prompt = (
        "Você é a AI DO PABLO, uma inteligência artificial especialista em pesquisas, matemática, lógica e programação.\n\n"
        "DIRETRIZES DE RESPOSTA:\n"
        "1. RESPOSTA DIRETA: Responda a qualquer pergunta (seja de matemática como 'quanto é 2+2', perguntas gerais, história ou códigos) com exatidão imediata.\n"
        "2. USO DE CONTEXTO: Se houver dados da web fornecidos abaixo, use-os para complementar. Se a busca web estiver vazia ou for uma conta matemática/pergunta simples, use o seu próprio conhecimento para responder diretamente.\n"
        "3. IDIOMA: Responda sempre em Português do Brasil de forma clara e amigável.\n"
        "4. OBJETIVIDADE: Seja direto ao ponto, evitando enrolação."
    )

    if contexto_web:
        sys_prompt += f"\n\n[DADOS DA WEB]:\n{contexto_web}"

    mensagens_payload = [{"role": "system", "content": sys_prompt}]
    
    for m in historico_mensagens[-4:]:
        if m.get("type") not in ["image", "video"]:
            mensagens_payload.append({"role": m["role"], "content": m["content"]})

    mensagens_payload.append({"role": "user", "content": prompt_usuario})

    try:
        payload = {
            "messages": mensagens_payload,
            "model": "openai"
        }
        res = requests.post("https://text.pollinations.ai/", json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        
        if res.status_code == 200 and res.text and len(res.text.strip()) > 0:
            if "402 Payment" not in res.text and "deprecated" not in res.text:
                return res.text.strip()
    except Exception:
        pass

    return "Não consegui processar essa pergunta agora. Tenta enviar novamente!"
    return "Tive uma oscilação na conexão ao processar essa consulta. Envie a mensagem novamente!"

# ==========================================
# 6. PAINEL LATERAL E SESSÕES DE CHAT
# ==========================================
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"

mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

st.sidebar.title("🛸 PAINEL DE CONTROLE")
st.sidebar.write(f"Operador: **{str(st.session_state.usuario_atual).upper()}**")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario_atual = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("💬 Histórico de Conversas")

lista_de_chats = list(conversas_usuario.keys())
chat_escolhido = st.sidebar.selectbox(
    "Selecionar Conversa:",
    lista_de_chats,
    index=lista_de_chats.index(st.session_state.chat_selecionado)
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input("Novo Chat:", key="new_chat_input", placeholder="Nome da conversa...").strip()
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
# 7. EXIBIÇÃO DE MENSAGENS E ENTRADA
# ==========================================
for message in mensagens_atuais:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Imagem gerada em HD")
        else:
            st.markdown(message["content"])

texto_input = st.chat_input("Pergunte algo, peça scripts ou gere imagens...")

if texto_input:
    conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": texto_input})
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    
    with st.chat_message("user"):
        st.markdown(texto_input)

    prompt_minusculo = texto_input.lower()
    comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])

    with st.chat_message("assistant"):
        if comando_imagem:
            with st.spinner("🎨 Gerando imagem..."):
                url_gerada = gerar_url_imagem(texto_input)
                st.image(url_gerada, caption="Imagem gerada em HD")
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        else:
            with st.spinner("⚡ AI DO PABLO pesquisando e processando..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], texto_input)
                st.markdown(resposta_texto)
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
