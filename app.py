import json
import hashlib
from pathlib import Path

import requests
import streamlit as st
from bs4 import BeautifulSoup

try:
    import g4f
    from g4f.client import Client
except Exception:
    g4f, Client = None, None

st.set_page_config(page_title='AI DO PABLO', page_icon='🤖', layout='wide')

DATA = Path('data')
DATA.mkdir(exist_ok=True)
USERS_FILE = DATA / 'users.json'
CHATS_FILE = DATA / 'chats.json'


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
    except Exception:
        return default


def save_json(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception:
        return False


def password_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def create_user(username, password):
    username = username.strip().lower()
    users = load_json(USERS_FILE, {})
    if not username or not password:
        return False, 'Preencha usuário e senha.'
    if username in users:
        return False, 'Esse usuário já existe.'
    users[username] = password_hash(password)
    save_json(USERS_FILE, users)
    chats = load_json(CHATS_FILE, {})
    chats.setdefault(username, {'Chat Principal': []})
    save_json(CHATS_FILE, chats)
    return True, 'Conta criada com sucesso!'


def check_login(username, password):
    return load_json(USERS_FILE, {}).get(username.strip().lower()) == password_hash(password)


def normalize_chats(chats):
    if not isinstance(chats, dict):
        return {'Chat Principal': []}
    result = {}
    for chat_name, history in chats.items():
        if not isinstance(chat_name, str):
            continue
        result[chat_name] = []
        if not isinstance(history, list):
            continue
        for item in history:
            if isinstance(item, str):
                if item.strip():
                    result[chat_name].append({'role': 'assistant', 'content': item})
                continue
            if not isinstance(item, dict):
                continue
            role = item.get('role')
            if role in ('user', 'assistant'):
                result[chat_name].append({
                    'role': role,
                    'content': str(item.get('content', '')),
                    'mode': item.get('mode', '💬 Chat')
                })
    result.setdefault('Chat Principal', [])
    return result


def get_chats(username):
    all_chats = load_json(CHATS_FILE, {})
    return normalize_chats(all_chats.get(username, {}))


def save_chats(username, chats):
    all_chats = load_json(CHATS_FILE, {})
    all_chats[username] = chats
    return save_json(CHATS_FILE, all_chats)


@st.cache_resource
def get_g4f_client():
    """Reutiliza o cliente entre reruns do Streamlit."""
    if Client is None:
        return None
    try:
        return Client()
    except Exception:
        return None


@st.cache_data(ttl=300, max_entries=128)
def cached_web_search(query, limit=5):
    """Evita repetir a mesma pesquisa Web por 5 minutos."""
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for item in soup.select(".result")[:limit]:
            title = item.select_one(".result__title")
            snippet = item.select_one(".result__snippet")
            link = item.select_one(".result__a")

            results.append(
                f"Título: {title.get_text(' ', strip=True) if title else ''}\n"
                f"Resumo: {snippet.get_text(' ', strip=True) if snippet else ''}\n"
                f"Link: {link.get('href', '') if link else ''}"
            )

        return "\n\n".join(results)

    except Exception:
        return ""


def web_search(query, limit=5):
    return cached_web_search(query, limit)


BASE_PROMPT = '''Você é a AI DO PABLO, uma assistente amigável, inteligente e útil.
Responda em português por padrão. Ajude em estudos, programação, matemática,
escrita, tecnologia, Roblox, projetos e problemas do dia a dia.
Explique assuntos difíceis de forma simples. Não invente fatos quando não tiver certeza.
Quando gerar código, informe o nome do arquivo e mantenha a estrutura organizada.'''

MODES = {
    '💬 Chat': 'Converse normalmente e responda diretamente.',
    '💻 Código': 'Seja especialista em programação. Para projetos grandes, divida por arquivos e partes.',
    '🎮 Criar Jogo': '''Seja especialista em criação de jogos, especialmente Roblox Studio.
Mostre a árvore Explorer e os caminhos de cada script. Organize o projeto em arquivos.
Para projetos grandes, gere uma parte por vez e peça CONTINUAR para a próxima.''',
    '📚 Estudar': 'Aja como professor particular. Explique do zero com exemplos, analogias e exercícios.',
}


def build_messages(history, question, mode, web=''):
    messages = [{
        'role': 'system',
        'content': BASE_PROMPT + '\n\nMODO:\n' + MODES.get(mode, MODES['💬 Chat'])
    }]
    for item in history[-14:]:
        if isinstance(item, dict) and item.get('role') in ('user', 'assistant'):
            messages.append({'role': item['role'], 'content': str(item.get('content', ''))})
    if web:
        messages.append({'role': 'system', 'content': 'Contexto de pesquisa Web:\n\n' + web})
    messages.append({'role': 'user', 'content': question})
    return messages


def model_order(mode):
    # Model mais leve primeiro para respostas mais rápidas.
    if mode in ("💻 Código", "🎮 Criar Jogo"):
        return ("gpt-4o-mini", "gpt-4o", "deepseek-v3")
    return ("gpt-4o-mini", "gpt-4o", "deepseek-v3")


def ask_ai(history, question, mode, web=''):
    client = get_g4f_client()

    if client is None:
        return "⚠️ O motor g4f não foi carregado. Confira o requirements.txt."

    messages = build_messages(history, question, mode, web)

    # Tenta poucos modelos, em ordem de velocidade, para não ficar
    # esperando vários provedores lentos quando o primeiro já funciona.
    for model in model_order(mode):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            text = response.choices[0].message.content

            if text and str(text).strip():
                return str(text).strip()

        except Exception:
            continue

    # Compatibilidade com a API antiga do g4f.
    if g4f is not None and hasattr(g4f, "ChatCompletion"):
        for model in model_order(mode):
            try:
                text = str(
                    g4f.ChatCompletion.create(
                        model=model,
                        messages=messages,
                    )
                ).strip()

                if text:
                    return text

            except Exception:
                continue

    return (
        "⚠️ Os provedores gratuitos estão ocupados ou mudaram. "
        "Tente novamente em alguns segundos."
    )


def project_prompt(request, part):
    return f'''Crie este projeto de jogo de forma profissional:

{request}

Você está na PARTE {part}.
Não despeje milhares de linhas em uma única resposta.
Entregue somente a próxima parte necessária.
Mostre primeiro ou mantenha a árvore Explorer e informe o caminho de cada arquivo.
Não repita arquivos já concluídos.
Mantenha nomes de módulos, RemoteEvents e interfaces compatíveis entre as partes.
No final escreva: Digite CONTINUAR para a próxima parte.'''


st.session_state.setdefault('logged', False)
st.session_state.setdefault('user', '')
st.session_state.setdefault('chat', 'Chat Principal')
st.session_state.setdefault('mode', '💬 Chat')
st.session_state.setdefault('web', False)
st.session_state.setdefault('project', None)

if not st.session_state.logged:
    st.title('🤖 AI DO PABLO')
    st.caption('Uma IA feita para ajudar todo mundo. 🌎❤️')
    tab1, tab2 = st.tabs(['🔑 Entrar', '📝 Criar conta'])
    with tab1:
        username = st.text_input('Usuário', key='login_user')
        password = st.text_input('Senha', type='password', key='login_pass')
        if st.button('Entrar', use_container_width=True):
            if check_login(username, password):
                st.session_state.logged = True
                st.session_state.user = username.strip().lower()
                st.session_state.chat = 'Chat Principal'
                st.rerun()
            else:
                st.error('Usuário ou senha incorretos.')
    with tab2:
        username = st.text_input('Novo usuário', key='new_user')
        password = st.text_input('Nova senha', type='password', key='new_pass')
        confirm = st.text_input('Confirmar senha', type='password', key='new_confirm')
        if st.button('Criar conta', use_container_width=True):
            if password != confirm:
                st.error('As senhas não são iguais.')
            else:
                ok, msg = create_user(username, password)
                (st.success if ok else st.error)(msg)
    st.stop()

username = st.session_state.user

if (
    "user_chats" not in st.session_state
    or st.session_state.get("loaded_user") != username
):
    st.session_state.user_chats = get_chats(username)
    st.session_state.loaded_user = username

chats = st.session_state.user_chats

if st.session_state.chat not in chats:
    st.session_state.chat = next(iter(chats), "Chat Principal")

messages = chats[st.session_state.chat]

with st.sidebar:
    st.title('🤖 AI DO PABLO')
    st.caption(f'Usuário: {username}')
    mode = st.radio('Modo', tuple(MODES), index=tuple(MODES).index(st.session_state.mode))
    if mode != st.session_state.mode:
        st.session_state.mode = mode
    if st.button('➕ Novo chat', use_container_width=True):
        n = len(chats) + 1
        name = f'Chat {n}'
        while name in chats:
            n += 1
            name = f'Chat {n}'
        chats[name] = []
        st.session_state.chat = name
        st.session_state.project = None
        save_chats(username, chats)
        st.rerun()
    names = list(chats)
    selected = st.selectbox('Conversas', names, index=names.index(st.session_state.chat))
    if selected != st.session_state.chat:
        st.session_state.chat = selected
        st.rerun()
    st.session_state.web = st.toggle('🔎 Pesquisa Web', st.session_state.web)
    if mode == '🎮 Criar Jogo':
        st.info('Descreva o jogo. Para continuar um projeto grande, escreva CONTINUAR.')
    if st.session_state.project:
        part = st.session_state.project['part']
        st.caption(f'🎮 Projeto ativo — parte {part}')
    if st.button('🗑️ Limpar conversa', use_container_width=True):
        chats[st.session_state.chat] = []
        st.session_state.project = None
        save_chats(username, chats)
        st.rerun()
    if st.button('🚪 Sair', use_container_width=True):
        st.session_state.logged = False
        st.session_state.user = ''
        st.session_state.loaded_user = None
        st.session_state.user_chats = {}
        st.session_state.project = None
        st.rerun()

st.title('🤖 AI DO PABLO')
st.caption(f'Modo: {st.session_state.mode} • ⚡ Turbo • sem contador artificial de mensagens')

for message in messages:
    if not isinstance(message, dict):
        continue
    role = message.get('role')
    if role not in ('user', 'assistant'):
        continue
    with st.chat_message(role):
        st.markdown(str(message.get('content', '')))

if st.session_state.mode == '🎮 Criar Jogo' and st.session_state.project:
    if st.button('▶️ Continuar projeto', use_container_width=True):
        st.session_state.next_part = True
        st.rerun()

if messages:
    last = next((m for m in reversed(messages) if isinstance(m, dict) and m.get('role') == 'assistant'), None)
    if last:
        st.download_button(
            '⬇️ Baixar última resposta',
            data=str(last.get('content', '')),
            file_name='ai_do_pablo_resposta.txt',
            mime='text/plain',
        )

next_part = st.session_state.pop('next_part', False)
question = st.chat_input('Digite sua pergunta...')

if next_part and st.session_state.project:
    project = st.session_state.project
    project['part'] += 1
    prompt = project_prompt(project['request'], project['part'])
    with st.chat_message('assistant'):
        with st.spinner(f'🤖 Gerando parte {project["part"]}...'):
            answer = ask_ai(project.get('history', []), prompt, '🎮 Criar Jogo')
        st.markdown(answer)
    messages.append({'role': 'assistant', 'content': answer, 'mode': '🎮 Criar Jogo'})
    project.setdefault('history', []).append({'role': 'assistant', 'content': answer})
    save_chats(username, chats)

elif question:
    q = question.strip()
    if not q:
        st.stop()
    is_continue = q.lower() in {'continuar', 'continue', 'próxima', 'proxima'} and st.session_state.project

    if is_continue:
        project = st.session_state.project
        project['part'] += 1
        prompt = project_prompt(project['request'], project['part'])
        messages.append({'role': 'user', 'content': 'CONTINUAR', 'mode': project['mode']})
        with st.chat_message('user'):
            st.markdown(f'**Continuando projeto — parte {project["part"]}**')
        with st.chat_message('assistant'):
            with st.spinner(f'🤖 Gerando parte {project["part"]}...'):
                answer = ask_ai(project.get('history', []), prompt, project['mode'])
            st.markdown(answer)
        messages.append({'role': 'assistant', 'content': answer, 'mode': project['mode']})
        project.setdefault('history', []).append({'role': 'assistant', 'content': answer})
        save_chats(username, chats)
    else:
        messages.append({'role': 'user', 'content': q, 'mode': st.session_state.mode})
        with st.chat_message('user'):
            st.markdown(q)
        if st.session_state.mode == '🎮 Criar Jogo':
            st.session_state.project = {'request': q, 'part': 1, 'mode': st.session_state.mode, 'history': []}
            prompt = project_prompt(q, 1)
            with st.chat_message('assistant'):
                with st.spinner('🎮 Planejando o jogo...'):
                    answer = ask_ai([], prompt, '🎮 Criar Jogo')
                st.markdown(answer)
            st.session_state.project['history'].append({'role': 'assistant', 'content': answer})
        else:
            web = web_search(q) if st.session_state.web else ''
            with st.chat_message('assistant'):
                with st.spinner('🤖 Pensando...'):
                    answer = ask_ai(messages[:-1], q, st.session_state.mode, web)
                st.markdown(answer)
        messages.append({'role': 'assistant', 'content': answer, 'mode': st.session_state.mode})
        save_chats(username, chats)
