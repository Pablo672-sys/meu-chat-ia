import streamlit as st
from groq import Groq
import os
import json
import requests
import time

# Configuração da página
st.set_page_config(page_title="Minha IA Exclusiva", page_icon="🧠", layout="centered")

st.title("🧠 IA Do Pablo! & Imagens")

# 🔐 Puxa a chave da Groq dos Secrets
try:
    MINHA_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=MINHA_API_KEY)
except Exception:
    MINHA_API_KEY = ""

# --- FUNÇÃO DE SUPER PESQUISA (DuckDuckGo API alternativa via DuckDuckGo Lite) ---
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

# --- FUNÇÕES DE HISTÓRICO ---
def get_historico_file(usuario):
    return f"historico_{usuario}.json"

def carregar_historico(usuario):
    arquivo = get_historico_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(usuario, mensagens):
    arquivo = get_historico_file(usuario)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(mensagens, f, ensure_ascii=False, indent=4)

def deletar_historico(usuario):
    arquivo = get_historico_file(usuario)
    if os.path.exists(arquivo):
        os.remove(arquivo)
    st.session_state.messages = []

# --- FUNÇÃO DE IMAGEM ---
def gerar_url_imagem(prompt_texto):
    encoded_prompt = requests.utils.quote(prompt_texto)
    seed = int(time.time())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"
    return url

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.subheader("🔑 Faça login na sua Conta")
    usuario = st.text_input("Usuário:").strip().lower()
    senha = st.text_input("Senha:", type="password")
    
    if st.button("Entrar", use_container_width=True):
        if (usuario == "admin" and senha == "admin123") or (usuario == "amigo" and senha == "12345"):
            st.session_state.logado = True
            st.session_state.usuario_atual = usuario
            st.session_state.messages = carregar_historico(usuario)
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
            
# --- TELA DO CHAT ---
else:
    st.sidebar.title("Minha Conta")
    st.sidebar.write(f"Usuário: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.success("Plano: Normal 🚀")
    st.sidebar.info("📷 Para criar imagem, use: 'crie uma imagem de [descrição]'")
    st.sidebar.markdown("---")
        
    if st.sidebar.button("🗑️ Deletar Todo o Histórico", use_container_width=True):
        deletar_historico(st.session_state.usuario_atual)
        st.sidebar.warning("Histórico apagado!")
        st.rerun()
        
    if st.sidebar.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption=message.get("prompt_user"))
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte algo ou peça uma imagem..."):
        st.chat_message("user").markdown(prompt)
        
        prompt_minusculo = prompt.lower()
        comando_imagem = False
        descricoes_imagem = ["crie uma imagem", "gere uma imagem", "faça uma foto", "desenhe", "image of"]
        
        for comando in descricoes_imagem:
            if comando in prompt_minusculo:
                comando_imagem = True
                prompt_para_imagem = prompt_minusculo.replace(comando, "").strip()
                break

        if comando_imagem:
            with st.chat_message("assistant"):
                st.write(f"🎨 Gerando imagem de: *{prompt_para_imagem}*...")
                url_gerada = gerar_url_imagem(prompt_para_imagem)
                st.image(url_gerada, caption=f"Imagem gerada para: {prompt_para_imagem}")
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({
                    "role": "assistant", 
                    "type": "image",
                    "content": url_gerada,
                    "prompt_user": f"🎨 Imagem de: {prompt_para_imagem}"
                })
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
            
            try:
                if not MINHA_API_KEY:
                    st.error("Chave API da Groq não configurada no Streamlit Cloud!")
                    st.stop()
                
                # Executa a busca em tempo real para dar superpoderes à resposta
                with st.spinner("🔍 Pesquisando dados atualizados na web..."):
                    contexto_web = pesquisar_na_internet(prompt)
                
                # Prepara o histórico e instrução do sistema
                instrucao_sistema = (
                    "Você é uma inteligência artificial extremamente inteligente, lógica e precisa. "
                    "Use os fatos trazidos da internet para responder com total exatidão. "
                    "Nunca invente informações falsas e organize sua resposta de forma clara e profissional.\n\n"
                    f"Resultados da pesquisa na internet para ajudar:\n{contexto_web}"
                )
                
                groq_history = [{"role": "system", "content": instrucao_sistema}]
                
                for m in st.session_state.messages[-6:-1]:
                    if m.get("type") != "image":
                        groq_history.append({"role": m["role"], "content": m["content"]})
                
                groq_history.append({"role": "user", "content": prompt})
                
                # Chamada na Groq com temperatura ultra focada
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_history,
                    temperature=0.1
                )
                
                resposta_texto = completion.choices[0].message.content
                
                with st.chat_message("assistant"):
                    st.markdown(resposta_texto)
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
                
            except Exception as e:
                st.error(f"Erro na IA (Groq): {e}")
