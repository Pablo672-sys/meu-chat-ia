import streamlit as st
import requests

# 1. Configuração da página e estilo
st.set_page_config(page_title="Minha IA Local", page_icon="🖥️", layout="centered")
st.title("🖥️ Meu Portal de IA Local")
st.write("Esta IA está rodando direto no meu próprio computador!")

# Inicializa o controle de login e mensagens
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "contador_mensagens" not in st.session_state:
    st.session_state.contador_mensagens = 0

# --- TELA DE LOGIN ---
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

# --- TELA DO CHAT (APÓS LOGIN) ---
else:
    # Configurações na Barra Lateral
    st.sidebar.title("Painel de Controle")
    st.sidebar.write(f"Conectado como: **{st.session_state.usuario_atual.upper()}**")
    
    if st.session_state.usuario_atual == "comum":
        st.sidebar.info(f"Mensagens: {st.session_state.contador_mensagens} / 3")
    
    st.sidebar.markdown("---")
    
    # Botão do Admin para zerar o limite do código
    if st.session_state.usuario_atual == "admin":
        if st.sidebar.button("⚡ Zerar Limites de Usuários"):
            st.session_state.contador_mensagens = 0
            st.sidebar.success("Limites zerados!")
            st.rerun()
        st.sidebar.markdown("---")
        
    if st.sidebar.button("🧹 Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
        
    if st.sidebar.button("🚪 Sair da Conta"):
        st.session_state.logado = False
        st.session_state.messages = []
        st.session_state.contador_mensagens = 0
        st.rerun()

    # Mostra o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Caixa de entrada de texto
    if prompt := st.chat_input("Pergunte qualquer coisa..."):
        
        if st.session_state.usuario_atual == "comum" and st.session_state.contador_mensagens >= 3:
            st.error("❌ Seu limite de mensagens acabou!")
        else:
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            if st.session_state.usuario_atual != "admin":
                st.session_state.contador_mensagens += 1

            # CONEXÃO COM O OLLAMA LOCAL
            try:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    
                    # Endereço padrão onde o Ollama roda no seu PC
                    url = "http://localhost:11434/api/generate"
                    
                    # Dados que enviamos para o seu Llama 3 local
                    payload = {
                        "model": "llama3.2:1b",
                        "prompt": prompt,
                        "stream": False,
                        "system": "Você DEVE responder sempre em Português do Brasil (PT-BR)."
                    }
                    
                    # Faz a requisição para o programa do Ollama
                    response = requests.post(url, json=payload)
                    resposta_ia = response.json().get("response", "Sem resposta.")
                    
                    response_placeholder.markdown(resposta_ia)
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
            
            except Exception as e:
                st.error("Erro: Certifique-se de que o Ollama está aberto no seu PC!")