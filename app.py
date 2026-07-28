import streamlit as st
from groq import Groq

st.set_page_config(page_title="IA Profissional", page_icon="🚀", layout="centered")
st.title("🚀 Meu Portal de IA")

# Chave para rodar direto na internet
MINHA_API_KEY = "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"

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.logado:
    st.subheader("🔑 Faça login para usar a IA")
    usuario = st.text_input("Usuário:")
    senha = st.text_input("Senha:", type="password")
    
    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin123":
            st.session_state.logado = True
            st.session_state.usuario_atual = "admin"
            st.rerun()
        elif usuario == "amigo" and senha == "12345":
            st.session_state.logado = True
            st.session_state.usuario_atual = "comum"
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")
else:
    st.sidebar.title("Painel de Controle")
    st.sidebar.write(f"Conectado como: **{st.session_state.usuario_atual.upper()}**")
    st.sidebar.success("Acesso Total: Sem limites de mensagens! ⭐")
    st.sidebar.markdown("---")
        
    if st.sidebar.button("🧹 Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
        
    if st.sidebar.button("🚪 Sair da Conta"):
        st.session_state.logado = False
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte qualquer coisa..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            client = Groq(api_key=MINHA_API_KEY)
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                messages_to_send = [{"role": "system", "content": "Você DEVE responder sempre em Português do Brasil (PT-BR)."}]
                for m in st.session_state.messages:
                    messages_to_send.append({"role": m["role"], "content": m["content"]})
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_to_send,
                    stream=True,
                )
                
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erro no servidor da IA: {e}")
