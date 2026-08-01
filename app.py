import streamlit as st
from groq import Groq
import os
import json
import requests
import time
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# Configuração da página com tema moderno
st.set_page_config(page_title="NEO IA - Voice Interface", page_icon="🔮", layout="centered")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .title-gradient {
        background: linear-gradient(45deg, #00f2fe, #4facfe, #000000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1px;
        margin-bottom: 20px;
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        color: white;
        border: 1px solid #4facfe;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.6);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title-gradient">🔮 NEO IA · Quantum Interface</h1>', unsafe_allow_html=True)
st.markdown("---")

# 🔐 Puxa a chave da Groq
try:
    MINHA_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=MINHA_API_KEY)
except Exception:
    MINHA_API_KEY = ""

# --- BANCO DE DADOS DE USUÁRIOS ---
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
    usuarios = carregar_usuarios()
    usuarios[novo_usuario] = nova_senha
    with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)

# --- FUNÇÃO DE SUPER PESQUISA ---
def pesquisar_na_internet(termo_busca):
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(termo_busca)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resposta = requests.get(url, headers=headers, timeout=5)
        if resposta.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resposta.text, "html.parser")
            resultados = []
            for a in soup.find_all("a", class_="result__snippet")[:3]:
                resultados.append(a.get_text().strip())
            if resultados:
                return "\n".join(resultados)
    except Exception:
        pass
    return "Nenhum resultado adicional encontrado na pesquisa em tempo real."

# --- FUNÇÕES DE MÚLTIPLOS CHATS SALVOS ---
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
    arquivo = get_chats_indices_file(usuario)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todos_chats, f, ensure_ascii=False, indent=4)

# --- FUNÇÃO DE IMAGEM ---
def gerar_url_imagem(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"

# --- GERADOR DE VOZ NATURAL (gTTS) ---
def gerar_audio_natural(texto, chave_index):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        tts = gTTS(text=texto_limpo, lang='pt', tld='com.br', slow=False)
        filename = f"audio_resp_{chave_index}.mp3"
        tts.save(filename)
        
        with open(filename, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True) # Autoplay ativa a fala na hora!
        
        if os.path.exists(filename):
            os.remove(filename)
    except Exception:
        pass

# Inicializações no session_state
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
    
    # Gravador de voz posicionado no topo da barra lateral
    st.sidebar.subheader("🎙️ Conversar por Voz")
    st.sidebar.caption("Fale e envie diretamente para a IA:")
    audio_gravado = mic_recorder(
        start_prompt="🎤 Iniciar Chamada por Voz",
        stop_prompt="⏹️ Desligar e Responder",
        key='gravador_definitivo',
        use_container_width=True
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Minhas Conversas")
    
    lista_de_chats = list(conversas_usuario.keys())
    chat_escolhido = st.sidebar.selectbox("Trocar de Conversa:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()
        
    # Exibição do botão de deletar chats personalizados
    if st.session_state.chat_selecionado != "Chat Principal":
        if st.sidebar.button(f"❌ Deletar '{st.session_state.chat_selecionado}'", use_container_width=True):
            del conversas_usuario[st.session_state.chat_selecionado]
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = "Chat Principal"
            st.rerun()
            
    novo_nome_chat = st.sidebar.text_input("Nome do novo chat:", key="new_chat_name", placeholder="Nova conversa...").strip()
    if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
        if novo_nome_chat and novo_nome_chat not in conversas_usuario:
            conversas_usuario[novo_nome_chat] = []
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = novo_nome_chat
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Limpar Conteúdo do Chat", use_container_width=True):
        conversas_usuario[st.session_state.chat_selecionado] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.rerun()
        
    if st.sidebar.button("🚪 Disconnect Session", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

    # Exibição do histórico de mensagens
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"])
            else:
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    gerar_audio_natural(message["content"], index)

    # Coleta de dados de entrada
    prompt_final = None
    
    # Se o usuário digitou no campo de texto normal
    texto_digitado = st.chat_input("Insira uma instrução de texto...")
    if texto_digitado:
        prompt_final = texto_digitado

    # Se o usuário usou o gravador de voz, transcreve imediatamente
    if audio_gravado and 'bytes' in audio_gravado:
        # Cria uma chave única no estado para evitar reprocessar o mesmo áudio
        audio_identificador = hash(audio_gravado['bytes'])
        if st.session_state.get("ultimo_audio_processado") != audio_identificador:
            st.session_state.ultimo_audio_processado = audio_identificador
            try:
                with st.spinner("🎙️ Traduzindo sua voz para texto..."):
                    transcricao = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=('audio.wav', audio_gravado['bytes']),
                    )
                    prompt_final = transcricao.text
            except Exception as e:
                st.error(f"Erro ao transcrever áudio: {e}")

    # Execução da resposta
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
            try:
                with st.status("🔍 Buscando referências atuais...", expanded=False):
                    contexto_web = pesquisar_na_internet(prompt_final)
                
                instrucao_sistema = (
                    "Você é o ápice da inteligência artificial: respostas profundas, exaustivas e explicativas.\n"
                    f"Hipercontexto internet:\n{contexto_web}"
                )
                
                groq_history = [{"role": "system", "content": instrucao_sistema}]
                for m in conversas_usuario[st.session_state.chat_selecionado][-6:-1]:
                    if m.get("type") != "image":
                        groq_history.append({"role": m["role"], "content": m["content"]})
                groq_history.append({"role": "user", "content": prompt_final})
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_history,
                    temperature=0.3
                )
                
                resposta_texto = completion.choices[0].message.content
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro na IA: {e}")
