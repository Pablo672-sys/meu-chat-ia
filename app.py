import streamlit as st
import google.generativeai as genai
import os
import json
import requests
import time

# Configuração da página
st.set_page_config(page_title="Minha IA Exclusiva", page_icon="🧠", layout="centered")

st.title("🧠 IA Do Pablo! & Imagem")

# 🔐 Puxa a chave do Gemini dos Secrets do Streamlit
try:
    MINHA_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=MINHA_API_KEY)
except Exception:
    MINHA_API_KEY = ""

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
    st.sidebar.success("Plano: Gemini Free Tier 🚀")
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

    if prompt := st.chat_input("Pergunte ou peça uma imagem..."):
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
                    st.error("Chave API do Gemini não configurada no Streamlit Cloud!")
                    st.stop()
                    
                model = genai.GenerativeModel("gemini-2.0-flash")
                gemini_history = []
                historico_texto = [m for m in st.session_state.messages if m.get("type") != "image"]
                
                for m in historico_texto[-6:-1]:
                    role = "user" if m["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [m["content"]]})
                
                chat = model.start_chat(history=gemini_history)
                
                with st.chat_message("assistant"):
                    response = chat.send_message(prompt)
                    st.markdown(response.text)
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
                
            except Exception as e:
                st.error(f"Erro na IA: {e}")
