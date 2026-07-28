import streamlit as st
from groq import Groq
import os
import json
import requests
import time

# Configuração da página padrão e estável
st.set_page_config(page_title="IA Super Inteligente + Imagens", page_icon="🧠", layout="centered")

st.title("🧠 IA DO PABLO! & Imagem")

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

# --- FUNÇÃO GRATUITA PARA GERAR IMAGEM ---
def gerar_url_imagem(prompt_texto):
    # Traduz o prompt para inglês simples (melhora muito o resultado no Pollinations)
    # Como não temos tradutor aqui, pedimos para o usuário digitar em inglês
    # ou usamos o prompt direto. O Pollinations funciona melhor em inglês.
    encoded_prompt = requests.utils.quote(prompt_texto)
    # Gera um número aleatório para a imagem ser única (seed)
    seed = int(time.time())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"
    return url

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
    st.sidebar.success("Plano: Normal! Grátis 🔥")
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

    # Mostra o histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption=message.get("prompt_user"))
            else:
                st.markdown(message["content"])

    # Entrada do Chat
    if prompt := st.chat_input("Pergunte ou peça uma imagem..."):
        st.chat_message("user").markdown(prompt)
        
        # --- LÓGICA DE DETECÇÃO DE PEDIDO DE IMAGEM ---
        prompt_minusculo = prompt.lower()
        comando_imagem = False
        descricoes_imagem = ["crie uma imagem", "gere uma imagem", "faça uma foto", "desenhe", "image of"]
        
        for comando in descricoes_imagem:
            if comando in prompt_minusculo:
                comando_imagem = True
                # Tenta isolar apenas a descrição do que o usuário quer
                prompt_para_imagem = prompt_minusculo.replace(comando, "").strip()
                break

        if comando_imagem:
            # --- FLUXO DE GERAÇÃO DE IMAGEM ---
            with st.chat_message("assistant"):
                st.write(f"🎨 Gerando imagem de: *{prompt_para_imagem}*...")
                url_gerada = gerar_url_imagem(prompt_para_imagem)
                
                # Mostra a imagem na tela
                st.image(url_gerada, caption=f"Imagem gerada para: {prompt_para_imagem}")
                
                # Salva no histórico da sessão
                st.session_state.messages.append({
                    "role": "user", 
                    "content": prompt
                })
                st.session_state.messages.append({
                    "role": "assistant", 
                    "type": "image",
                    "content": url_gerada,
                    "prompt_user": f"🎨 Imagem de: {prompt_para_imagem}"
                })
                # Salva o histórico atualizado no arquivo da conta
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)

        else:
            # --- FLUXO DE TEXTO NORMAL (GROQ) ---
            st.session_state.messages.append({"role": "user", "content": prompt})
            salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
            
            try:
                client = Groq(api_key=MINHA_API_KEY)
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    messages_to_send = [{
                        "role": "system", 
                        "content": "Você é uma IA extremamente avançada e prestativa. Responda SEMPRE em Português do Brasil de forma clara."
                    }]
                    
                    # Para texto, enviamos apenas mensagens de texto do histórico
                    for m in st.session_state.messages:
                        if m.get("type") != "image":
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
