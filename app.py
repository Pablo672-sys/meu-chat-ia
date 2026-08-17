import json, hashlib, time, os
from pathlib import Path

import requests
import streamlit as st
from bs4 import BeautifulSoup
from gtts import gTTS

try:
    import g4f
    from g4f.client import Client
except Exception:
    g4f, Client = None, None

st.set_page_config(page_title="AI DO PABLO", page_icon="🤖", layout="centered")

DB = Path("data")
DB.mkdir(exist_ok=True)
USERS = DB / "users.json"
CHATS = DB / "chats.json"


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def new_user(name, password):
    name = name.strip().lower()
    users = load(USERS, {})
    if not name or not password:
        return False, "Preencha usuário e senha."
    if name in users:
        return False, "Esse usuário já existe."
    users[name] = sha(password)
    save(USERS, users)
    chats = load(CHATS, {})
    chats.setdefault(name, {"Chat Principal": []})
    save(CHATS, chats)
    return True, "Conta criada!"


def valid_user(name, password):
    return load(USERS, {}).get(name.strip().lower()) == sha(password)


def get_chats(name):
    chats = load(CHATS, {})
    chats.setdefault(name, {"Chat Principal": []})
    return chats


def save_chats(name, user_chats):
    chats = load(CHATS, {})
    chats[name] = user_chats
    return save(CHATS, chats)


def search_web(query):
    try:
        r = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        for item in soup.select(".result")[:5]:
            title = item.select_one(".result__title")
            text = item.select_one(".result__snippet")
            link = item.select_one(".result__a")
            out.append(
                f"Título: {title.get_text(' ', strip=True) if title else ''}\n"
                f"Resumo: {text.get_text(' ', strip=True) if text else ''}\n"
                f"Link: {link.get('href', '') if link else ''}"
            )
        return "\n\n".join(out)
    except Exception:
        return ""


SYSTEM = """Você é a AI DO PABLO, uma assistente amigável e útil.
Responda em português por padrão. Ajude em estudos, programação, Roblox,
matemática, escrita, projetos e problemas do dia a dia.
Explique coisas difíceis de forma simples e não invente fatos."""


def ask_ai(history, question, web=""):
    if Client is None:
        return "⚠️ O motor g4f não carregou. Confira o requirements.txt."

    msgs = [{"role": "system", "content": SYSTEM}]
    msgs += [
        {"role": m["role"], "content": m.get("content", "")}
        for m in history[-12:]
        if m.get("role") in ("user", "assistant")
    ]
    if web:
        msgs.append({
            "role": "system",
            "content": "Contexto encontrado na Web:\n" + web
        })
    msgs.append({"role": "user", "content": question})

    for model in ("gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"):
        try:
            result = Client().chat.completions.create(model=model, messages=msgs)
            text = result.choices[0].message.content
            if text and text.strip():
                return text.strip()
        except Exception:
            pass

    if g4f and hasattr(g4f, "ChatCompletion"):
        for model in ("gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"):
            try:
                text = str(g4f.ChatCompletion.create(model=model, messages=msgs)).strip()
                if text:
                    return text
            except Exception:
                pass

    return "⚠️ Os provedores gratuitos estão ocupados. Tente novamente."


def speak(text, number):
    try:
        text = text.replace("**", "").replace("*", "").replace("`", "")
        if len(text) > 220:
            text = text[:220] + "..."
        file = DB / f"voice_{number}_{int(time.time())}.mp3"
        gTTS(text=text, lang="pt", tld="com.br").save(file)
        st.audio(file.read_bytes(), format="audio/mp3")
        file.unlink(missing_ok=True)
    except Exception:
        pass


st.session_state.setdefault("logged", False)
st.session_state.setdefault("user", "")
st.session_state.setdefault("chat", "Chat Principal")
st.session_state.setdefault("web", False)


if not st.session_state.logged:
    st.title("🤖 AI DO PABLO")
    st.caption("Uma IA criada para ajudar. 🌎❤️")
    login, register = st.tabs(["Entrar", "Criar conta"])

    with login:
        name = st.text_input("Usuário", key="login_name")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            if valid_user(name, password):
                st.session_state.logged = True
                st.session_state.user = name.strip().lower()
                st.session_state.chat = "Chat Principal"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with register:
        name = st.text_input("Novo usuário", key="new_name")
        password = st.text_input("Nova senha", type="password", key="new_pass")
        confirm = st.text_input("Confirmar senha", type="password", key="new_confirm")
        if st.button("Criar conta", use_container_width=True):
            if password != confirm:
                st.error("As senhas não são iguais.")
            else:
                ok, msg = new_user(name, password)
                (st.success if ok else st.error)(msg)
    st.stop()


user = st.session_state.user
chats = get_chats(user)
if st.session_state.chat not in chats:
    st.session_state.chat = next(iter(chats))
messages = chats[st.session_state.chat]

with st.sidebar:
    st.title("🤖 AI DO PABLO")
    st.caption(f"Usuário: {user}")

    if st.button("➕ Novo chat", use_container_width=True):
        i, name = len(chats) + 1, ""
        while not name or name in chats:
            name = f"Chat {i}"
            i += 1
        chats[name] = []
        st.session_state.chat = name
        save_chats(user, chats)
        st.rerun()

    names = list(chats)
    selected = st.selectbox("Conversas", names, index=names.index(st.session_state.chat))
    if selected != st.session_state.chat:
        st.session_state.chat = selected
        st.rerun()

    st.session_state.web = st.toggle("🔎 Pesquisa Web", st.session_state.web)

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        chats[st.session_state.chat] = []
        save_chats(user, chats)
        st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged = False
        st.session_state.user = ""
        st.rerun()


st.title("🤖 AI DO PABLO")
st.caption("Sem contador artificial de mensagens • memória da conversa")

for i, msg in enumerate(messages):
    if msg.get("role") in ("user", "assistant"):
        with st.chat_message(msg["role"]):
            st.markdown(msg.get("content", ""))
            if msg["role"] == "assistant":
                with st.expander("🔊 Ouvir"):
                    speak(msg.get("content", ""), i)

question = st.chat_input("Digite sua pergunta...")

if question:
    messages.append({"role": "user", "content": question})
    save_chats(user, chats)

    with st.chat_message("user"):
        st.markdown(question)

    web = ""
    if st.session_state.web:
        with st.spinner("🔎 Pesquisando..."):
            web = search_web(question)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Pensando..."):
            answer = ask_ai(messages[:-1], question, web)
        st.markdown(answer)

    messages.append({"role": "assistant", "content": answer})
    save_chats(user, chats)
