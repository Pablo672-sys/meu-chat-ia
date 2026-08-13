import streamlit as st
import ast
import math
import re
import random
from datetime import datetime

st.set_page_config(
    page_title="AI DO PABLO",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =========================================================
# VISUAL
# =========================================================
st.markdown("""
<style>
.stApp {
    font-family: Inter, system-ui, sans-serif;
}
.hero-title {
    background: linear-gradient(90deg,#2563eb,#3b82f6,#00c6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: clamp(28px,5vw,44px);
    font-weight: 800;
    text-align: center;
}
.hero-subtitle {
    color: #64748b;
    text-align: center;
    margin-bottom: 20px;
}
div[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 10px;
    border: 1px solid rgba(128,128,128,.14);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="hero-title">🤖 AI DO PABLO</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">IA independente · Sem API · Sem chave · Sem outra IA</p>',
    unsafe_allow_html=True
)

# =========================================================
# MEMÓRIA DA SESSÃO
# =========================================================
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat Principal": []}

if "chat_atual" not in st.session_state:
    st.session_state.chat_atual = "Chat Principal"

# =========================================================
# CONHECIMENTO E RESPOSTAS
# =========================================================
def normalizar(texto):
    texto = texto.lower().strip()
    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    return "".join(substituicoes.get(c, c) for c in texto)


def calcular(expressao):
    """
    Calculadora segura usando apenas AST.
    Não usa eval().
    """
    try:
        arvore = ast.parse(expressao, mode="eval")

        operadores = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a ** b,
        }

        unarios = {
            ast.UAdd: lambda a: +a,
            ast.USub: lambda a: -a,
        }

        def visitar(no):
            if isinstance(no, ast.Expression):
                return visitar(no.body)

            if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
                if abs(no.value) > 10**100:
                    raise ValueError
                return no.value

            if isinstance(no, ast.BinOp) and type(no.op) in operadores:
                esquerda = visitar(no.left)
                direita = visitar(no.right)

                if isinstance(no.op, ast.Pow) and abs(direita) > 100:
                    raise ValueError

                resultado = operadores[type(no.op)](esquerda, direita)

                if isinstance(resultado, (int, float)) and abs(resultado) > 10**100:
                    raise ValueError

                return resultado

            if isinstance(no, ast.UnaryOp) and type(no.op) in unarios:
                return unarios[type(no.op)](visitar(no.operand))

            raise ValueError

        resultado = visitar(arvore)

        if isinstance(resultado, float) and resultado.is_integer():
            resultado = int(resultado)

        return str(resultado)

    except Exception:
        return None


def resposta_saudacao(texto):
    t = normalizar(texto)

    if t in ("oi", "ola", "opa", "e ai", "eae", "fala"):
        return random.choice([
            "Olá! 👋 Eu sou a AI DO PABLO. Como posso ajudar?",
            "Fala! 😎 O que você quer fazer?",
            "Oi! 🤖 Estou pronto para ajudar.",
        ])

    if "bom dia" in t:
        return "Bom dia! ☀️ Como posso ajudar você?"

    if "boa tarde" in t:
        return "Boa tarde! 🌤️ O que vamos fazer hoje?"

    if "boa noite" in t:
        return "Boa noite! 🌙 Como posso ajudar?"

    return None


def responder(texto, historico):
    t = normalizar(texto)

    # Saudações
    r = resposta_saudacao(texto)
    if r:
        return r

    # Identidade
    if "quem e voce" in t or "o que e voce" in t:
        return (
            "Eu sou a **AI DO PABLO** 🤖.\n\n"
            "Nesta versão eu funciono sem API, sem chave, sem outra IA "
            "e sem modelo local. Minhas respostas são produzidas pelo "
            "próprio código do aplicativo."
        )

    if "seu nome" in t:
        return "Meu nome é **AI DO PABLO**. 🤖"

    # Capacidades
    if any(x in t for x in [
        "o que voce consegue fazer",
        "o que voce pode fazer",
        "suas funcoes",
        "comandos",
    ]):
        return (
            "Eu consigo:\n\n"
            "- 💬 conversar usando regras e conhecimento programado\n"
            "- 🧮 fazer cálculos\n"
            "- 🧠 lembrar as mensagens enquanto o chat estiver aberto\n"
            "- 🕒 informar data e horário\n"
            "- 🎲 gerar números aleatórios\n"
            "- 📚 responder perguntas que estejam no meu conhecimento programado\n"
            "- 🛠️ ajudar com código e explicações básicas\n\n"
            "Tudo isso sem API, sem chave e sem outra IA."
        )

    # Data e hora
    if "que horas" in t or "horas sao" in t:
        return f"Agora são **{datetime.now().strftime('%H:%M:%S')}**."

    if "que dia e hoje" in t or "data de hoje" in t or t == "hoje":
        return f"Hoje é **{datetime.now().strftime('%d/%m/%Y')}**."

    # Matemática
    if t.startswith(("calcule ", "calcula ", "quanto e ", "quanto é ")):
        expr = re.sub(
            r"^(calcule|calcula|quanto e|quanto é)\s+",
            "",
            texto,
            flags=re.I
        )
        expr = expr.replace(",", ".").replace("×", "*").replace("÷", "/")
        resultado = calcular(expr)
        if resultado is not None:
            return f"🧮 Resultado: **{resultado}**"
        return "Não consegui interpretar essa conta. Exemplo: `calcule 25 * 4`."

    # Conta pura
    if re.fullmatch(r"[0-9\s\+\-\*\/\%\(\)\.,\^]+", texto):
        expr = texto.replace(",", ".").replace("^", "**")
        resultado = calcular(expr)
        if resultado is not None:
            return f"🧮 **{resultado}**"

    # Porcentagem simples
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*%\s*de\s*(\d+(?:[.,]\d+)?)",
        texto,
        flags=re.I
    )
    if m:
        porcentagem = float(m.group(1).replace(",", "."))
        valor = float(m.group(2).replace(",", "."))
        resultado = porcentagem * valor / 100
        return f"🧮 {porcentagem:g}% de {valor:g} = **{resultado:g}**"

    # Aleatório
    if "numero aleatorio" in t or "número aleatório" in texto.lower():
        return f"🎲 Seu número aleatório é **{random.randint(1, 100)}**."

    # Memória simples da conversa
    if "o que eu falei antes" in t or "minha ultima mensagem" in t:
        usuarios = [
            m["content"] for m in historico
            if m.get("role") == "user"
        ]
        if len(usuarios) >= 2:
            return f'Você disse anteriormente: **"{usuarios[-2]}"**'
        return "Ainda não tenho uma mensagem anterior suficiente para mostrar."

    # Ajuda com programação
    if any(x in t for x in [
        "python", "streamlit", "roblox", "lua", "codigo",
        "programar", "programacao"
    ]):
        return (
            "Posso ajudar com programação de forma baseada no conhecimento "
            "e nas regras que foram implementadas nesta versão. 🛠️\n\n"
            "Se você colar um código aqui, posso analisar a estrutura, "
            "explicar erros e sugerir correções."
        )

    # Respostas gerais programadas
    respostas = [
        (
            ["tudo bem", "como voce esta", "como esta voce"],
            "Estou funcionando direitinho! 🤖👍 E você?"
        ),
        (
            ["obrigado", "obrigada", "valeu"],
            "De nada! 😄"
        ),
        (
            ["voce e inteligente", "voce e bom"],
            "Estou sempre tentando melhorar! 🧠🤖"
        ),
        (
            ["piada", "conte uma piada"],
            "Por que o computador foi ao médico? Porque estava com um vírus. 😂"
        ),
    ]

    for palavras, resposta in respostas:
        if any(p in t for p in palavras):
            return resposta

    # Fallback honesto
    return (
        "🤖 Ainda não tenho uma resposta programada para essa pergunta.\n\n"
        "Tente perguntar de outra forma ou use um dos recursos que eu "
        "conheço, como cálculos, data, hora, programação ou minhas funções."
    )


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🛸 PAINEL DE CONTROLE")
st.sidebar.caption("Modo independente: sem API, sem chave e sem outra IA.")

nomes = list(st.session_state.chats.keys())

selecionado = st.sidebar.selectbox(
    "Selecionar conversa",
    nomes,
    index=nomes.index(st.session_state.chat_atual)
)

if selecionado != st.session_state.chat_atual:
    st.session_state.chat_atual = selecionado
    st.rerun()

novo = st.sidebar.text_input("Novo Chat", placeholder="Nome do chat...")

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

entrada = st.chat_input("Digite sua mensagem...")

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
            with st.spinner("🤖 Pensando..."):
                resposta = responder(entrada, mensagens[:-1])
            st.markdown(resposta)

        mensagens.append({
            "role": "assistant",
            "content": resposta,
        })

        st.rerun()
