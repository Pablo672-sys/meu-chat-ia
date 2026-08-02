import streamlit as st
import os
import json
import requests
import time
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import g4f

# Configuração de interface de Elite
st.set_page_config(page_title="NEO IA - Nexus Free Core", page_icon="🔮", layout="centered")

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
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f1c2c, #00f2fe);
        color: white;
        border: 1px solid #4facfe;
        border-radius: 8px;
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
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title-gradient">🔮 NEO IA · Nexus Free Core</h1>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"admin": "admin123"}
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    try:
        usuarios = carregar_usuarios()
        usuarios[novo_usuario] = nova_senha
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except:
        pass

def get_chats_indices_file(usuario):
    return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_indices_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"Chat Principal": []}
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        arquivo = get_chats_indices_file(usuario)
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except:
        pass

def gerar_url_imagem(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"

# --- REPRODUTOR DE ÁUDIO HUMANO ---
def gerar_audio_natural(texto, chave_index, autoplay=False):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        
        if any(keyword in texto_limpo for keyword in ["function", "local ", "Instance.new", "def ", "Script"]):
            texto_limpo = "Tudo pronto! Montei o mapa de onde colocar no Explorer e o código completo direto na sua tela. Dá uma olhada!"
        elif len(texto_limpo) > 150:
            texto_limpo = texto_limpo[:150] + "..."
            
        tts = gTTS(text=texto_limpo, lang='pt', tld='com.br', slow=False)
        filename = f"audio_resp_{chave_index}.mp3"
        tts.save(filename)
        
        with open(filename, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=autoplay)
        
        if os.path.exists(filename):
            os.remove(filename)
    except:
        pass

# --- PROCESSADOR DE TRANSCRIÇÃO DE VOZ SEM CHAVE ---
def transcrever_audio_gratis(audio_bytes):
    try:
        url = "https://api.wit.ai/speech"
        headers = {
            "Authorization": "Bearer 7J56PZ4ZLQ4O2V3M5ZXZN4Z3ZXZNZXZN",
            "Content-Type": "audio/wav"
        }
        resposta = requests.post(url, headers=headers, data=audio_bytes, timeout=5)
        if resposta.status_code == 200:
            linhas = resposta.text.split('\n')
            for linha in lines:
                if linha.strip():
                    dados = json.loads(linha)
                    if "text" in dados:
                        return dados["text"]
    except:
        pass
    return None

# --- MOTOR DE TEXTO BRABO E 100% GRATUITO (Sem Chaves via g4f) ---
def chamar_ia_gratis(historico_mensagens, prompt_usuario):
    try:
        instrucao_sistema = (
            "Você é o Nexus Core v3, o parceiro dev de elite definitivo. "
            "Suas explicações são incrivelmente claras, curtas, fáceis de entender e direto ao ponto. "
            "Evite blocos longos de texto. Use tópicos e listas simples. Você opera sob estas regras obrigatórias:\n\n"
            "1. MAPA DO EXPLORER VISUAL: Se a pergunta envolver o Roblox Studio, você deve desenhar no início da resposta "
            "a árvore exata de onde criar o script, usando setas transparentes claras. Exemplo:\n"
            "   `Explorer ➔ ServerScriptService ➔ [Criar Script normal aqui]`\n"
            "2. CÓDIGO PERFEITO (ERRO ZERO): O código deve ser totalmente funcional, atualizado com as APIs modernas do Roblox, "
            "comentado passo a passo de forma simples e pronto para copiar e colar.\n"
            "3. EXPLICAÇÃO RÁPIDA (TÉCNICA FEYNMAN): Explique o que o script faz de forma simples, sem usar palavras difíceis de faculdade. "
            "Foque em fazer o usuário entender a lógica de primeira.\n"
            "4. CUIDADO COM OS BUGS: Liste 2 coisas rápidas que podem fazer o script dar erro (ex: esquecer de mudar o nome do objeto no script ou colocar o script no local errado)."
        )
        
        # Cria a estrutura de chat do g4f
        mensagens_g4f = [{"role": "system", "content": instrucao_sistema}]
        
        for m in historico_mensagens[-2:]:
            if m.get("type") != "image":
                mensagens_g4f.append({"role": m["role"], "content": m["content"]})
                
        mensagens_g4f.append({"role": "user", "content": prompt_usuario})
        
        # Chama um modelo estável de graça e de forma segura
        resposta = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=mensagens_g4f
        )
        return resposta
    except Exception as e:
        return f"Erro ao processar: {str(e)}. Por favor, tente reenviar."

# Inicializadores estáticos de Estado
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
    
    # 🎙 Canal de Áudio
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
        if st.sidebar.button(f"❌ Deletar Chat Atual", use_container_width=True):
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
    tamanho_historico = len(mensagens_atuais)
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            else:
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    e_ultima_mensagem = (index == tamanho_historico - 1)
                    gerar_audio_natural(message["content"], index, autoplay=e_ultima_mensagem)

    prompt_final = None

    # Inputs de Texto e Voz sincronizados
    texto_input = st.chat_input("Envie sua mensagem por texto...")
    if texto_input:
        prompt_final = texto_input

    if audio_chamada and audio_chamada.get('id') != st.session_state.last_call_id:
        st.session_state.last_call_id = audio_chamada.get('id')
        texto_voz = transcrever_audio_gratis(audio_chamada['bytes'])
        if texto_voz:
            prompt_final = texto_voz

    # Fluxo de execução seguro
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
