import streamlit as st
import ast
import re
import html
import requests
from urllib.parse import quote, urlparse, parse_qs
from datetime import datetime

# =========================================================
# CONFIGURAÇÃO
# =========================================================
st.set_page_config(
    page_title="AI DO PABLO",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { font-family: Inter, system-ui, sans-serif; }
.hero-title {
    background: linear-gradient(90deg,#2563eb,#3b82f6,#00c6ff);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    font-size:clamp(28px,5vw,44px);
    font-weight:800;
    text-align:center;
}
.hero-subtitle {
    color:#64748b;
    text-align:center;
    margin-bottom:20px;
}
div[data-testid="stChatMessage"] {
    border-radius:16px;
    padding:15px;
    margin-bottom:10px;
    border:1px solid rgba(128,128,128,.14);
}
.source-box {
    padding:10px;
    border-radius:10px;
    border:1px solid rgba(128,128,128,.18);
    margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">Pesquisa Web + YouTube · Sem API de IA · Sem chave · Sem outra IA</p>',
    unsafe_allow_html=True
)

# =========================================================
# ESTADO
# =========================================================
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat Principal": []}

if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = "Chat Principal"

# =========================================================
# UTILIDADES
# =========================================================
def normalizar(texto):
    tabela = str.maketrans(
        "áàãâäéèêëíìîïóòõôöúùûüç",
        "aaaaaeeeeiiiiooooouuuuc"
    )
    return texto.lower().translate(tabela).strip()


def limpar_html(texto):
    texto = re.sub(r"<script.*?</script>", " ", texto, flags=re.I | re.S)
    texto = re.sub(r"<style.*?</style>", " ", texto, flags=re.I | re.S)
    texto = re.sub(r"<[^>]+>", " ", texto)
    return html.unescape(re.sub(r"\s+", " ", texto)).strip()


def extrair_url_youtube(texto):
    padroes = [
        r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"https?://youtu\.be/[\w-]+",
        r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
    ]

    for padrao in padroes:
        m = re.search(padrao, texto)
        if m:
            return m.group(0)

    return None


def youtube_id(url):
    try:
        p = urlparse(url)

        if p.hostname in ("youtu.be", "www.youtu.be"):
            return p.path.strip("/").split("/")[0]

        if p.hostname and "youtube.com" in p.hostname:
            if p.path == "/watch":
                return parse_qs(p.query).get("v", [None])[0]

            partes = p.path.strip("/").split("/")
            if len(partes) >= 2 and partes[0] in ("shorts", "embed"):
                return partes[1]

    except Exception:
        pass

    return None


# =========================================================
# PESQUISA WEB
# =========================================================
@st.cache_data(show_spinner=False, ttl=600)
def pesquisar_web(consulta):
    """
    Pesquisa HTML público do DuckDuckGo.
    Não usa API.
    """
    try:
        resposta = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": consulta},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resposta.raise_for_status()

        texto = resposta.text
        resultados = []

        blocos = re.findall(
            r'<div[^>]+class="result[^"]*"[^>]*>(.*?)</div>\s*</div>',
            texto,
            flags=re.I | re.S
        )

        # Fallback mais simples se o HTML mudar.
        if not blocos:
            blocos = re.findall(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                texto,
                flags=re.I | re.S
            )
            for url, titulo in blocos[:8]:
                resultados.append({
                    "titulo": limpar_html(titulo),
                    "url": html.unescape(url),
                    "texto": "",
                })
            return resultados

        for bloco in blocos[:8]:
            link = re.search(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                bloco,
                flags=re.I | re.S
            )
            snippet = re.search(
                r'class="result__snippet"[^>]*>(.*?)</(?:a|div)',
                bloco,
                flags=re.I | re.S
            )

            if link:
                resultados.append({
                    "titulo": limpar_html(link.group(2)),
                    "url": html.unescape(link.group(1)),
                    "texto": limpar_html(snippet.group(1)) if snippet else "",
                })

        return resultados

    except Exception:
        return []


# =========================================================
# LEITURA DE PÁGINAS
# =========================================================
@st.cache_data(show_spinner=False, ttl=600)
def ler_pagina(url):
    try:
        resposta = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
            allow_redirects=True,
        )
        resposta.raise_for_status()

        if "text/html" not in resposta.headers.get("content-type", ""):
            return ""

        texto = limpar_html(resposta.text)

        # Evita enviar uma página gigantesca ao mecanismo local.
        return texto[:12000]

    except Exception:
        return ""


# =========================================================
# YOUTUBE
# =========================================================
def obter_transcricao_youtube(url):
    """
    Tenta usar youtube-transcript-api se estiver instalado.
    O programa continua funcionando mesmo sem essa biblioteca.
    """
    video_id = youtube_id(url)

    if not video_id:
        return ""

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()

        # API nova
        if hasattr(api, "fetch"):
            transcript = api.fetch(
                video_id,
                languages=["pt", "pt-BR", "en", "es"]
            )

            partes = []
            for item in transcript:
                if hasattr(item, "text"):
                    partes.append(str(item.text))
                elif isinstance(item, dict):
                    partes.append(str(item.get("text", "")))

            return " ".join(partes)[:12000]

        # Compatibilidade com versões antigas
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["pt", "pt-BR", "en", "es"]
        )

        return " ".join(
            str(item.get("text", ""))
            for item in transcript
        )[:12000]

    except Exception:
        return ""


# =========================================================
# MOTOR LOCAL DE RESPOSTAS
# =========================================================
def pontuar_relevancia(pergunta, texto):
    """
    Mede de forma simples quais frases encontradas têm mais
    palavras em comum com a pergunta.
    """
    palavras_pergunta = {
        p for p in re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", normalizar(pergunta))
        if p not in {
            "como", "qual", "quais", "quem", "onde", "quando",
            "para", "sobre", "isso", "essa", "esse", "uma", "que",
            "com", "dos", "das", "por", "tem", "ser", "foi"
        }
    }

    frases = re.split(r"(?<=[.!?])\s+", texto)
    avaliadas = []

    for frase in frases:
        palavras = set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", normalizar(frase)))
        pontos = len(palavras_pergunta & palavras)

        if pontos > 0:
            avaliadas.append((pontos, frase.strip()))

    avaliadas.sort(key=lambda x: x[0], reverse=True)

    return [frase for _, frase in avaliadas[:6]]


def responder_com_fontes(pergunta, fontes, transcricao=""):
    """
    Monta uma resposta sem usar modelo de IA.
    A resposta é uma seleção e organização de informações
    encontradas nas fontes.
    """
    textos = []

    if transcricao:
        textos.append(("YouTube", transcricao))

    for fonte in fontes:
        if fonte.get("texto"):
            textos.append((fonte.get("titulo", "Web"), fonte["texto"]))

    if not textos:
        return (
            "Não encontrei informação suficiente para responder com segurança. "
            "Tente reformular a pergunta ou fornecer um link."
        )

    trechos = []

    for nome, texto in textos:
        relevantes = pontuar_relevancia(pergunta, texto)

        if relevantes:
            trechos.append((nome, relevantes))

    if not trechos:
        # Ainda mostra informações das fontes, mas deixa claro que
        # não houve correspondência forte.
        primeiro = textos[0][1][:700]
        return (
            "🔎 Encontrei fontes relacionadas, mas não achei um trecho "
            "suficientemente relevante para afirmar uma resposta com segurança.\n\n"
            f"**Informação encontrada:**\n{primeiro}"
        )

    resposta = "🔎 **Resposta baseada nas fontes encontradas:**\n\n"

    usados = 0

    for nome, frases in trechos:
        for frase in frases[:3]:
            if len(frase) > 40:
                resposta += f"- {frase}\n"
                usados += 1

            if usados >= 7:
                break

        if usados >= 7:
            break

    resposta += (
        "\n> ⚠️ Esta resposta foi montada pelo próprio programa a partir "
        "dos textos encontrados. Ela não usa outra IA para interpretar as fontes."
    )

    return resposta


# =========================================================
# CÁLCULO SEGURO
# =========================================================
def calcular(expressao):
    try:
        arvore = ast.parse(expressao, mode="eval")

        ops = {
            ast.Add: lambda a,b: a+b,
            ast.Sub: lambda a,b: a-b,
            ast.Mult: lambda a,b: a*b,
            ast.Div: lambda a,b: a/b,
            ast.FloorDiv: lambda a,b: a//b,
            ast.Mod: lambda a,b: a%b,
            ast.Pow: lambda a,b: a**b,
        }

        unarios = {
            ast.UAdd: lambda a: +a,
            ast.USub: lambda a: -a,
        }

        def visitar(no):
            if isinstance(no, ast.Expression):
                return visitar(no.body)

            if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
                return no.value

            if isinstance(no, ast.BinOp) and type(no.op) in ops:
                a = visitar(no.left)
                b = visitar(no.right)
                if isinstance(no.op, ast.Pow) and abs(b) > 100:
                    raise ValueError
                return ops[type(no.op)](a, b)

            if isinstance(no, ast.UnaryOp) and type(no.op) in unarios:
                return unarios[type(no.op)](visitar(no.operand))

            raise ValueError

        resultado = visitar(arvore)

        if isinstance(resultado, float) and resultado.is_integer():
            resultado = int(resultado)

        return str(resultado)

    except Exception:
        return None


# =========================================================
# RESPOSTA PRINCIPAL
# =========================================================
def responder(pergunta, historico):
    texto = pergunta.strip()
    n = normalizar(texto)

    # Conversa básica
    if n in ("oi", "ola", "opa", "e ai", "eae", "fala"):
        return "Olá! 👋 Eu sou a **AI DO PABLO**. O que você quer pesquisar?"

    if "bom dia" in n:
        return "Bom dia! ☀️ Posso pesquisar algo para você."

    if "boa tarde" in n:
        return "Boa tarde! 🌤️ Posso pesquisar algo para você."

    if "boa noite" in n:
        return "Boa noite! 🌙 Posso pesquisar algo para você."

    # Conta
    if re.fullmatch(r"[0-9\s\+\-\*\/\%\(\)\.,\^]+", texto):
        resultado = calcular(texto.replace(",", ".").replace("^", "**"))
        if resultado:
            return f"🧮 **{resultado}**"

    # Hora/data
    if "que horas" in n:
        return f"🕒 Agora são **{datetime.now().strftime('%H:%M:%S')}**."

    if "que dia" in n or n == "hoje":
        return f"📅 Hoje é **{datetime.now().strftime('%d/%m/%Y')}**."

    # YouTube
    url_youtube = extrair_url_youtube(texto)

    if url_youtube:
        with st.spinner("▶️ Lendo o conteúdo do YouTube..."):
            transcricao = obter_transcricao_youtube(url_youtube)

        if transcricao:
            resposta = responder_com_fontes(
                texto,
                [],
                transcricao=transcricao
            )

            return resposta + f"\n\n**Fonte:** {url_youtube}"

        return (
            "▶️ Encontrei o vídeo, mas não consegui obter a legenda/transcrição. "
            "Esse vídeo pode não disponibilizar transcrição pública.\n\n"
            f"**Vídeo:** {url_youtube}"
        )

    # Pesquisa Web
    with st.spinner("🔎 Pesquisando na Web..."):
        fontes = pesquisar_web(texto)

    resposta = responder_com_fontes(texto, fontes)

    # Fontes
    if fontes:
        resposta += "\n\n### 🌐 Fontes encontradas\n"

        for fonte in fontes[:5]:
            titulo = fonte.get("titulo") or "Fonte"
            url = fonte.get("url", "")
            resposta += f"- [{titulo}]({url})\n"

    return resposta


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🛸 PAINEL DE CONTROLE")
st.sidebar.caption(
    "Pesquisa feita diretamente na Web e no YouTube. "
    "Nenhuma API de IA é usada."
)

nomes = list(st.session_state.chats.keys())

selecionado = st.sidebar.selectbox(
    "Selecionar conversa",
    nomes,
    index=nomes.index(st.session_state.chat_atual)
)

if selecionado != st.session_state.chat_atual:
    st.session_state.chat_atual = selecionado
    st.rerun()

novo = st.sidebar.text_input(
    "Novo Chat",
    placeholder="Nome do chat..."
)

if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
    novo = novo.strip()

    if not novo:
        st.sidebar.warning("Digite um nome.")
    elif novo in st.session_state.chats:
        st.sidebar.warning("Esse chat já existe.")
    else:
        st.session_state.chats[novo] = []
        st.session_state.chat_atual = novo
        st.rerun()

if st.session_state.chat_atual != "Chat Principal":
    if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True):
        del st.session_state.chats[st.session_state.chat_atual]
        st.session_state.chat_atual = "Chat Principal"
        st.rerun()

if st.sidebar.button("🗑️ Limpar Mensagens", use_container_width=True):
    st.session_state.chats[st.session_state.chat_atual] = []
    st.rerun()

# =========================================================
# CHAT
# =========================================================
mensagens = st.session_state.chats[st.session_state.chat_atual]

for mensagem in mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

entrada = st.chat_input(
    "Pergunte algo ou cole um link do YouTube..."
)

if entrada:
    entrada = entrada.strip()

    if entrada:
        mensagens.append({
            "role": "user",
            "content": entrada,
        })

        with st.chat_message("user"):
            st.markdown(entrada)

        with st.chat_message("assistant"):
            resposta = responder(entrada, mensagens[:-1])
            st.markdown(resposta)

        mensagens.append({
            "role": "assistant",
            "content": resposta,
        })

        st.rerun()
