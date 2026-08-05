import streamlit as st
import os
import json
import requests
import time
import tempfile
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# --- CONFIGURAÇÃO DA INTERFACE VISUAL (DARK GLASSMORPHISM) ---
st.set_page_config(
    page_title="NEXUS AI · Absolute Core",
    page_icon="🔮",
    layout="centered"
)

st.markdown("""
    <style>
    /* Fundo Dark Glassmorphism */
    .stApp {
        background: linear-gradient(135deg, #090714 0%, #110c28 50%, #05030a 100%);
        color: #f1f5f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    /* ... (mantive seu CSS) ... */
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🔮 NEXUS AI · Absolute Core</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Inteligência Suprema · Respostas Detalhadas · Imagens & Mídias</p>', unsafe_allow_html=True)
st.markdown("---")

BANCO_USUARIOS = "usuarios_cadastrados.json"

# --- BANCO DE DADOS LOCAL E USUARIOS ---
def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Arquivo de usuários corrompido — recriando default.")
            return {"admin": "admin123"}
        except Exception as e:
            print("Erro ao carregar usuários:", e)
            return {"admin": "admin123"}
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    try:
        usuarios = carregar_usuarios()
        usuarios[novo_usuario] = nova_senha
        with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Erro ao salvar usuário:", e)

def get_chats_indices_file(usuario):
    safe_user = usuario.replace("/", "_")
    return f"chats_salvos_{safe_user}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_indices_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Arquivo de chats corrompido — recriando padrão.")
            return {"Chat Principal": []}
        except Exception as e:
            print("Erro ao carregar chats:", e)
            return {"Chat Principal": []}
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    try:
        arquivo = get_chats_indices_file(usuario)
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(todos_chats, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Erro ao salvar chats:", e)

# --- GERADOR DE IMAGENS E MÍDIAS ---
def gerar_url_midia(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    largura, altura = 1024, 1024
    lower = prompt_texto.lower()
    if "1920x1080" in prompt_texto or "widescreen" in lower:
        largura, altura = 1280, 720
    elif "portrait" in lower or "celular" in lower:
        largura, altura = 720, 1280
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width={largura}&height={altura}&model=flux&nologo=true"

# --- SÍNTESE E TRANSCRIÇÃO DE VOZ ---
def gerar_audio_natural(texto, chave_index, autoplay=False):
    try:
        texto_limpo = texto.replace("**", "").replace("*", "").replace("`", "")
        if any(kw in texto_limpo for kw in ["function", "local ", "Instance.new", "def ", "Script", "class "]):
            texto_limpo = "Resposta e scripts gerados com sucesso na sua tela!"
        elif len(texto_limpo) > 180:
            texto_limpo = texto_limpo[:180] + "..."

        # usar arquivo temporário para evitar colisões e problemas de permissões
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_name = tmp.name
        tts = gTTS(text=texto_limpo, lang='pt', tld='com.br', slow=False)
        tts.save(tmp_name)

        with open(tmp_name, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=autoplay)

        try:
            os.remove(tmp_name)
        except Exception:
            pass
    except Exception as e:
        print("Erro em gerar_audio_natural:", e)

def transcrever_audio_gratis(audio_bytes):
    try:
        # prefira definir token via variável de ambiente WIT_AI_TOKEN
        WIT_TOKEN = os.getenv("WIT_AI_TOKEN", "7J56PZ4ZLQ4O2V3M5ZXZN4Z3ZXZNZXZN")
        url = "https://api.wit.ai/speech"
        headers = {
            "Authorization": f"Bearer {WIT_TOKEN}",
            "Content-Type": "audio/wav"
        }
        res = requests.post(url, headers=headers, data=audio_bytes, timeout=10)
        if res.status_code == 200:
            # wit.ai normalmente responde com JSON
            try:
                data = res.json()
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
            except ValueError:
                # fallback: tentar interpretar texto cru
                text = res.text.strip()
                if text:
                    return text
        else:
            print("Wit.ai retornou status", res.status_code, res.text[:200])
    except Exception as e:
        print("Erro em transcrever_audio_gratis:", e)
    return None

# --- MOTOR DE IA RÁPIDO E LIMPO ---
def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    instrucao_sistema = (
        "Você é o Nexus Absolute Core, a Inteligência Artificial mais avançada, precisa e explicativa do mundo.\n\n"
        "REGRAS DE RESPOSTA:\n"
        "1. EXPLICABILIDADE COMPLETA: Responda com riqueza de detalhes, passo a passo, de forma super clara e didática.\n"
        "2. CÓDIGO PERFEITO (ERRO ZERO): Escreva scripts impecáveis em Luau para Roblox Studio, Python, C++, HTML, etc.\n"
        "3. MAPA DO EXPLORER: Se for sobre Roblox Studio, mostre o mapa no topo (Ex: Explorer ➔ ServerScriptService ➔ [Script]).\n"
        "4. ANALISE TEXTOS GIGANTES: Processe mensagens longas com precisão extrema."
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible)",
        "Content-Type": "application/json"
    }

    messages_payload = [{"role": "system", "content": instrucao_sistema}]
    # incluir até 4 últimas mensagens de histórico (filtrando imagens)
    for m in [mm for mm in historico_mensagens if mm.get("type") not in ["image", "video"]][-4:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        c_hist = content[:1000] if len(content) > 1000 else content
        messages_payload.append({"role": role, "content": c_hist})
    messages_payload.append({"role": "user", "content": prompt_usuario})

    # Rota 1: Envio POST Direto
    try:
        r = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": messages_payload, "model": "openai"},
            headers=headers,
            timeout=12
        )
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return r.text
        else:
            print("pollinations POST status:", r.status_code)
    except Exception as e:
        print("Erro na rota POST do pollinations:", e)

    # Rota 2: Envio GET Alternativo
    try:
        prompt_enc = requests.utils.quote(f"{instrucao_sistema}\n\nUsuário: {prompt_usuario}")
        r = requests.get(f"https://text.pollinations.ai/{prompt_enc}?model=openai", headers=headers, timeout=12)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            return r.text
        else:
            print("pollinations GET status:", r.status_code)
    except Exception as e:
        print("Erro na rota GET do pollinations:", e)

    return "Não foi possível conectar ao servidor livre neste instante. Por favor, envie a pergunta novamente."

# --- ESTADO DA SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"
if "last_call_id" not in st.session_state:
    st.session_state.last_call_id = None

# --- TELA DE LOGIN / CADASTRO ---
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

# --- PAINEL PRINCIPAL DO CHAT ---
else:
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0] if conversas_usuario else "Chat Principal"
    mensagens_atuais = conversas_usuario.get(st.session_state.chat_selecionado, [])

    # Sidebar
    st.sidebar.title("🛸 NEXUS CONTROL")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.markdown("---")

    st.sidebar.subheader("🎙️ Entrada por Voz")
    audio_chamada = mic_recorder(
        start_prompt="🔊 Falar com a IA",
        stop_prompt="⏹️ Transcrever e Enviar",
        key='gravador_chamada',
        use_container_width=True
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Gerenciamento de Chats")

    lista_de_chats = list(conversas_usuario.keys()) or ["Chat Principal"]
    # garantir índice válido
    if st.session_state.chat_selecionado in lista_de_chats:
        default_index = lista_de_chats.index(st.session_state.chat_selecionado)
    else:
        default_index = 0
        st.session_state.chat_selecionado = lista_de_chats[0]

    chat_escolhido = st.sidebar.selectbox("Selecionar Chat:", lista_de_chats, index=default_index)
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()

    if st.session_state.chat_selecionado != "Chat Principal":
        if st.sidebar.button("❌ Deletar Chat Atual", use_container_width=True):
            if st.session_state.chat_selecionado in conversas_usuario:
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

    # RENDERIZAÇÃO DAS MENSAGENS
    tamanho_historico = len(mensagens_atuais)
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message.get("role", "assistant")):
            if message.get("type") == "image":
                st.image(message.get("content"))
            else:
                st.markdown(message.get("content", ""))
                if message.get("role") == "assistant":
                    e_ultima = (index == tamanho_historico - 1)
                    gerar_audio_natural(message.get("content", ""), index, autoplay=e_ultima)

    prompt_final = None

    texto_input = st.chat_input("Pergunte qualquer coisa ou peça scripts/imagens...")
    if texto_input:
        prompt_final = texto_input

    if audio_chamada and audio_chamada.get('id') != st.session_state.last_call_id:
        st.session_state.last_call_id = audio_chamada.get('id')
        texto_voz = transcrever_audio_gratis(audio_chamada.get('bytes', b""))
        if texto_voz:
            prompt_final = texto_voz

    # EXECUÇÃO DO PROCESSAMENTO
    if prompt_final:
        conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt_final})
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

        prompt_minusculo = prompt_final.lower()
        comando_imagem = any(cmd in prompt_minusculo for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"])

        if comando_imagem:
            with st.spinner("🎨 Gerando imagem em alta resolução..."):
                url_gerada = gerar_url_midia(prompt_final)
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "type": "image", "content": url_gerada})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        else:
            with st.spinner("🧠 Processando resposta completa..."):
                resposta_texto = chamar_ia_suprema(conversas_usuario[st.session_state.chat_selecionado], prompt_final)

            conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.rerun()
