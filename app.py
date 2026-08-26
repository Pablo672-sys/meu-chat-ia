import streamlit as st
import os
import json
import requests
import time
import g4f

# Configuração de interface de Elite (Máxima performance visual)
st.set_page_config(page_title="NEO IA - Nexus Absolute Core", page_icon="🔮", layout="centered")

# --- CUSTOM ENGINE CSS ---
st.markdown("""
<style>
.title-gradient {
    background: linear-gradient(45deg, #00f2fe, #4facfe, #ffffff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 42px;
    font-weight: 800;
    text-align: center;
    letter-spacing: -1px;
    margin-bottom: 20px;
}
div.stButton > button {
    background: linear-gradient(135deg, #1f1c2c, #00f2fe);
    color: white;
    border: 1px solid #4facfe;
    border-radius: 8px;
    font-weight: bold;
    transition: all 0.3s ease;
}
div.stButton > button:first-child {
    box-shadow: 0 0 15px rgba(0, 242, 254, 0.6);
    transform: translateY(-1px);
}
code {
    color: #00f2fe !important;
    font-family: 'Courier New', Courier, monospace !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title-gradient">🔮 NEO IA · Nexus Absolute Core</h1>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

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

def gerar_url_imagem(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"

# --- MOTOR DE ALTA PRECISÃO E REVISÃO RÍGIDA ---
def chamar_ia_gratis(historico_mensagens, prompt_usuario):
    instrucao_sistema = (
        "Você é o Nexus Absolute Core, uma inteligência artificial projetada para PRECISÃO MÁXIMA E ZERO ERROS.\n\n"
        "DIRETRIZES RÍGIDAS DE QUALIDADE:\n"
        "1. IDIOMA FIXO: Responda SEMPRE em Português do Brasil de forma natural e clara.\n"
        "2. PROGRAMAÇÃO SEM ERROS: Antes de exibir qualquer script (Luau/Roblox, Python, HTML, C++, JS), revise mentalmente a sintaxe, variáveis e escopo. O código deve funcionar perfeitamente ao ser copiado e colado.\n"
        "3. ROBLOX STUDIO: Especifique exatamente o local correto no Explorer (ex: ServerScriptService, StarterPlayerScripts, ReplicatedStorage).\n"
        "4. RESPOSTAS DIRETAS E FATOS EXATOS: Se não tiver certeza absoluta de um fato, explique o conceito com lógica impecável em vez de inventar dados.\n"
        "5. ESTRUTURA LIMPA: Use tópicos, blocos de código formatados e destaque termos importantes em negrito."
    )
    mensagens_g4f = [{"role": "system", "content": instrucao_sistema}]

    for m in historico_mensagens[-5:]:
        if m.get("type") != "image":
            mensagens_g4f.append({"role": m["role"], "content": m["content"]})

    mensagens_g4f.append({"role": "user", "content": prompt_usuario})

    modelos_disponiveis = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]

    try:
        from g4f.client import Client
        client = Client()
        for mod in modelos_disponiveis:
            try:
                response = client.chat.completions.create(
                    model=mod,
                    messages=mensagens_g4f
                )
                texto = response.choices[0].message.content
                if texto and len(str(texto).strip()) > 0:
                    return str(texto)
            except Exception:
                continue
    except Exception:
        pass

    for mod in modelos_disponiveis:
        try:
            resposta = g4f.ChatCompletion.create(
                model=mod,
                messages=mensagens_g4f
            )
            if resposta and len(str(resposta).strip()) > 0:
                return str(resposta)
        except Exception:
            continue

    return "Não foi possível conectar ao servidor no momento. Por favor, envie sua mensagem novamente!"

# Inicializadores estáticos de Estado
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

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
                st.success("Registro concluído! Vá na aba de login para acessar.")
            else:
                st.error("Erro ao registrar. Verifique os dados fornecidos.")

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

    # Histórico de Mensagens renderizado na tela
    for message in mensagens_atuais:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            else:
                st.markdown(message["content"])

    # Input de Texto
    prompt_final = st.chat_input("Envie sua mensagem por texto...")

    # Fluxo de execução
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
            resposta_texto = chamar_ia_gratis(conversas_usuario[st.session_state.chat_selecionado], prompt_final)
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
