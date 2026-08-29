import json
import os
import re
import time
import urllib.parse
import requests
import streamlit as st

try:
    import g4f
except Exception:
    g4f = None

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
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}

    .stApp {
        background: #0b0f14;
        color: #e5e7eb;
    }

    [data-testid="stHeader"] {
        background: #0b0f14;
    }

    section[data-testid="stSidebar"] {
        background: #11161d;
        border-right: 1px solid #252c35;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    .brand {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }

    .subbrand {
        color: #9ca3af;
        font-size: 13px;
        margin-bottom: 18px;
    }

    .welcome {
        max-width: 780px;
        margin: 0 auto;
        padding: 10vh 16px 6vh;
        text-align: center;
    }

    .welcome-logo {
        width: 64px;
        height: 64px;
        margin: 0 auto 16px;
        border-radius: 18px;
        background: #1b222c;
        border: 1px solid #303844;
        display: grid;
        place-items: center;
        font-size: 30px;
    }

    .welcome-title {
        color: #ffffff;
        font-size: 32px;
        font-weight: 800;
    }

    .welcome-text {
        color: #9ca3af;
        font-size: 15px;
        margin-top: 8px;
    }

    div[data-testid="stChatMessage"] {
        max-width: 900px;
        margin: 0 auto;
        padding: 12px 4px;
        background: transparent;
        border: 0;
        box-shadow: none;
    }

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #e5e7eb;
        line-height: 1.65;
    }

    div[data-testid="stChatInput"] {
        max-width: 900px;
        margin: 0 auto;
        background: #171c23;
        border: 1px solid #343c47;
        border-radius: 18px;
    }

    div[data-testid="stChatInput"] textarea {
        color: #ffffff;
    }

    .stButton > button {
        border-radius: 10px;
    }

    @media (max-width: 700px) {
        .welcome {
            padding-top: 6vh;
        }
        .welcome-title {
            font-size: 27px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="brand">🤖 AI DO PABLO</div>
    <div class="subbrand">Seu assistente inteligente</div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

st.markdown(
    """
    <div>
        <div class="brand">🤖 AI DO PABLO</div>
        <div class="subbrand">Seu assistente inteligente</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

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
            user_login = (
                st.text_input("Usuário", placeholder="Seu nome de usuário")
                .strip()
                .lower()
            )
            pass_login = st.text_input(
                "Senha", type="password", placeholder="Sua senha"
            )
            btn_entrar = st.form_submit_button(
                "Entrar no Console", use_container_width=True
            )

            if btn_entrar:
                usuarios_db = carregar_usuarios()
                if (
                    user_login in usuarios_db
                    and usuarios_db[user_login] == pass_login
                ):
                    st.session_state.logado = True
                    st.session_state.usuario_atual = user_login
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")

    with tab_cadastro:
        with st.form("form_cadastro"):
            novo_user = (
                st.text_input("Novo Usuário", placeholder="Escolha seu usuário")
                .strip()
                .lower()
            )
            nova_pass = st.text_input(
                "Nova Senha", type="password", placeholder="Escolha sua senha"
            )
            btn_cadastrar = st.form_submit_button(
                "Criar Registro", use_container_width=True
            )

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
@st.cache_data(show_spinner=False, ttl=900, max_entries=128)
def pesquisar_na_web(termo):
    """Busca snippets na Web e prioriza fontes úteis sem exigir chave do usuário."""
    if not HAS_BS4 or len(termo.strip()) < 2:
        return ""

    try:
        res = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": termo},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=7,
        )
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        resultados = []

        for item in soup.select(".result")[:6]:
            title = item.select_one(".result__title")
            snippet = item.select_one(".result__snippet")
            link = item.select_one(".result__a")

            t = title.get_text(" ", strip=True) if title else ""
            s = snippet.get_text(" ", strip=True) if snippet else ""
            u = link.get("href", "") if link else ""

            if t or s:
                resultados.append(
                    f"Título: {t}\nResumo: {s}\nFonte: {u}"
                )

        return "\n\n".join(resultados)

    except Exception:
        return ""


@st.cache_data(show_spinner=False, ttl=900, max_entries=128)
def pesquisar_youtube(termo):
    """Encontra vídeos relacionados por pesquisa pública, sem fingir que assistiu ao vídeo."""
    if len(termo.strip()) < 2:
        return []

    try:
        res = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": f"site:youtube.com/watch {termo}"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=7,
        )
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        videos = []

        for item in soup.select(".result")[:4]:
            title = item.select_one(".result__title")
            snippet = item.select_one(".result__snippet")
            link = item.select_one(".result__a")

            url = link.get("href", "") if link else ""
            if "youtube.com" in url or "youtu.be" in url:
                videos.append({
                    "title": title.get_text(" ", strip=True) if title else "",
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                    "url": url,
                })

        return videos
    except Exception:
        return []


def gerar_url_imagem(prompt_texto):
    encoded_prompt = urllib.parse.quote(prompt_texto)
    seed = int(time.time())
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1024&height=1024&model=flux&nologo=true"


# ==========================================
# 5. MOTOR DE RESPOSTA VIA POST
# ==========================================
def _g4f_answer(messages):
    """Fallback sem chave usando G4F."""
    try:
        from g4f.client import Client
    except Exception as exc:
        return None, f"g4f indisponível: {exc}"

    models = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1",
        "deepseek-v3",
        "gpt-3.5-turbo",
    ]

    errors = []

    try:
        client = Client()

        for model in models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                text = response.choices[0].message.content

                if text and str(text).strip():
                    return str(text).strip(), None
            except Exception as exc:
                errors.append(f"{model}: {type(exc).__name__}")

    except Exception as exc:
        errors.append(f"Client: {type(exc).__name__}")

    if g4f is not None and hasattr(g4f, "ChatCompletion"):
        for model in models:
            try:
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=messages,
                )
                text = str(response).strip()

                if text:
                    return text, None
            except Exception as exc:
                errors.append(f"legacy-{model}: {type(exc).__name__}")

    return None, "; ".join(errors[-4:])


def chamar_ia_suprema(historico_mensagens, prompt_usuario):
    p_clean = prompt_usuario.lower().strip()

    saudacoes = {
        "oi", "olá", "ola", "tudo bem", "e ai", "fala",
        "salve", "boa tarde", "bom dia", "boa noite",
    }

    if p_clean in saudacoes:
        return (
            "Fala! 😎 Eu sou a AI DO PABLO. "
            "Pode perguntar, pesquisar, programar ou criar alguma coisa."
        )

    contexto_web = pesquisar_na_web(prompt_usuario)

    sys_prompt = """
Você é a AI DO PABLO, uma inteligência artificial especialista
em pesquisa, matemática, lógica, programação, tecnologia, Roblox,
estudos e criação de projetos.

REGRAS:
1. Responda em Português do Brasil, salvo pedido diferente.
2. Seja precisa e direta.
3. Não invente fatos, comandos, APIs, funções ou resultados.
4. Se houver contexto da Web, use-o como evidência auxiliar.
5. Se fontes discordarem, explique a divergência.
6. Para código, entregue código completo, consistente e organizado.
7. Para Roblox/Luau, informe onde cada script deve ficar no Explorer.
8. Para projetos grandes, divida por arquivos e partes.
9. Não diga que assistiu a um vídeo se recebeu apenas o título ou resumo.
10. Quando não puder confirmar algo, diga claramente que não conseguiu confirmar.
"""

    if contexto_web:
        sys_prompt += (
            "\n\nCONTEXTO DA WEB:\n"
            + contexto_web
        )

    mensagens_payload = [
        {"role": "system", "content": sys_prompt}
    ]

    for item in historico_mensagens[-12:]:
        if not isinstance(item, dict):
            continue
        if item.get("type") in ("image", "video"):
            continue
        if item.get("role") not in ("user", "assistant"):
            continue

        mensagens_payload.append({
            "role": item["role"],
            "content": str(item.get("content", "")),
        })

    mensagens_payload.append({
        "role": "user",
        "content": prompt_usuario,
    })

    # 1) Preserva o método original do seu código.
    pollinations_error = None

    try:
        payload = {
            "messages": mensagens_payload,
            "model": "openai",
        }

        res = requests.post(
            "https://text.pollinations.ai/",
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )

        if res.status_code == 200:
            text = res.text.strip()

            if text and "deprecated" not in text.lower():
                return text

        pollinations_error = (
            f"Pollinations HTTP {res.status_code}"
            + (f": {res.text[:180]}" if res.text else "")
        )

    except Exception as exc:
        pollinations_error = (
            f"Pollinations {type(exc).__name__}: {exc}"
        )

    # 2) Fallback sem chave.
    fallback, g4f_error = _g4f_answer(mensagens_payload)

    if fallback:
        return fallback

    details = " | ".join(
        x for x in (pollinations_error, g4f_error) if x
    )

    return (
        "⚠️ Não consegui obter uma resposta do motor agora.\n\n"
        "Isso não significa necessariamente que os servidores estejam "
        "fora do ar. O método de conexão pode ter mudado.\n\n"
        f"**Diagnóstico técnico:** `{details[:500]}`"
    )


# ==========================================
# 6. PAINEL LATERAL E SESSÕES DE CHAT
# ==========================================
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)

if st.session_state.chat_selecionado not in conversas_usuario:
    st.session_state.chat_selecionado = (
        list(conversas_usuario.keys())[0]
        if conversas_usuario
        else "Chat Principal"
    )

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
    index=lista_de_chats.index(st.session_state.chat_selecionado),
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input(
    "Novo Chat:", key="new_chat_input", placeholder="Nome da conversa..."
).strip()
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


if not mensagens_atuais:
    st.markdown(
        """
        <div class="welcome">
            <div class="welcome-logo">🤖</div>
            <div class="welcome-title">Como posso ajudar?</div>
            <div class="welcome-text">
                Pergunte, pesquise, programe, estude ou crie um projeto.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# 7. EXIBIÇÃO DE MENSAGENS E ENTRADA
# ==========================================
for message in mensagens_atuais:
    if not isinstance(message, dict):
        continue

    role = message.get("role")
    if role not in ("user", "assistant"):
        continue

    with st.chat_message(role):
        if message.get("type") == "image":
            st.image(message.get("content", ""), caption="Imagem gerada em HD")
        else:
            st.markdown(str(message.get("content", "")))

texto_input = st.chat_input("Pergunte algo, peça scripts ou gere imagens...")

if texto_input:
    conversas_usuario[st.session_state.chat_selecionado].append(
        {"role": "user", "content": texto_input}
    )
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

    with st.chat_message("user"):
        st.markdown(texto_input)

    prompt_minusculo = texto_input.lower()
    comando_imagem = any(
        cmd in prompt_minusculo
        for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"]
    )

    with st.chat_message("assistant"):
        if comando_imagem:
            with st.spinner("🎨 Gerando imagem..."):
                url_gerada = gerar_url_imagem(texto_input)
                st.image(url_gerada, caption="Imagem gerada em HD")
                conversas_usuario[st.session_state.chat_selecionado].append(
                    {"role": "assistant", "type": "image", "content": url_gerada}
                )
                salvar_todos_chats(
                    st.session_state.usuario_atual, conversas_usuario
                )
        else:
            with st.spinner("⚡ AI DO PABLO pesquisando e processando..."):
                resposta_texto = chamar_ia_suprema(
                    conversas_usuario[st.session_state.chat_selecionado],
                    texto_input,
                )
                st.markdown(resposta_texto)

                # YouTube é apenas complemento: mostramos recomendações,
                # sem afirmar que a IA assistiu ao conteúdo.
                if st.checkbox(
                    "🎥 Mostrar vídeos relacionados",
                    key=f"yt_{len(mensagens_atuais)}",
                ):
                    videos = pesquisar_youtube(texto_input)
                    if videos:
                        st.markdown("**🎥 Dicas do YouTube**")
                        for video in videos:
                            st.markdown(
                                f"- [{video['title']}]({video['url']})"
                                + (f" — {video['snippet']}" if video['snippet'] else "")
                            )
                    else:
                        st.caption("Nenhum vídeo relacionado encontrado.")

                conversas_usuario[st.session_state.chat_selecionado].append(
                    {"role": "assistant", "content": resposta_texto}
                )
                salvar_todos_chats(
                    st.session_state.usuario_atual, conversas_usuario
                )
