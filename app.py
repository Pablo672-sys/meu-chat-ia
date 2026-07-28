import streamlit as st
from groq import Groq
import os
import json

# Configuração da página padrão e estável
st.set_page_config(page_title="IA Super Inteligente", page_icon="🧠")

st.title("🧠 Meu Portal de IA Plus")

MINHA_API_KEY = "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"

# --- FUNÇÕES PARA SALVAR E CARREGAR HISTÓRICO EM ARQUIVO ---
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

# Inicializa estados
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
    st.sidebar.success("Plano: Plus Grátis 🔥")
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
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte qualquer coisa para a Super IA..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
        
        try:
            client = Groq(api_key=MINHA_API_KEY)
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                messages_to_send = [{
                    "role": "system", 
                    "content": "Você é uma IA extremamente avançada, muito inteligente, prestativa e precisa. Responda SEMPRE em Português do Brasil de forma clara, completa e profissional."
                }]
                
                for m in st.session_state.messages:
                    messages_to_send.append({"role": m["role"], "content": m["content"]})
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_to_send,
                    stream=True,
                    temperature=0.7
                )
                
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
            
        except Exception as e:
            st.error(f"Erro na IA: {e}")
