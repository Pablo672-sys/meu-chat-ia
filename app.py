import streamlit as st
from groq import Groq
import os
import json
import requests
import time

# Configuração da página com tema escuro/moderno nativo do Streamlit
st.set_page_config(page_title="IA Do Pablo!", page_icon="⚡", layout="centered")

st.title("⚡ IA Do Pablo! Beta")
st.markdown("---")

# 🔐 Puxa a chave da Groq dos Secrets
try:
    MINHA_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=MINHA_API_KEY)
except Exception:
    MINHA_API_KEY = ""

# --- FUNÇÃO DE SUPER PESQUISA ---
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
    st.subheader("🔑 Autenticação do Sistema")
    usuario = st.text_input("Usuário:").strip().lower()
    senha = st.text_input("Senha:", type="password")
    
    if st.button("Acessar Console", use_container_width=True):
        if (usuario == "admin" and senha == "admin123") or (usuario == "amigo" and senha == "12345"):
            st.session_state.logado = True
            st.session_state.usuario_atual = usuario
            st.session_state.messages = carregar_historico(usuario)
            st.rerun()
        else:
            st.error("Acesso negado: dados incorretos.")
            
# --- TELA DO CHAT ---
else:
    # Estatísticas avançadas na barra lateral
    st.sidebar.title("🛸 IA PABLO!")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    
    total_msg = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.sidebar.metric(label="Requisições Efetuadas", value=f"{total_msg} logs")
    
    st.sidebar.markdown("### 🛠️ Parâmetros Ativos")
    st.sidebar.code("Model: Llama-3.3-70b\nEngine: Groq Cloud\nTemp: 0.1 (Max Precision)\nSearch: Web Live")
    
    st.sidebar.markdown("---")
        
    if st.sidebar.button("🗑️ Wipe Database (Limpar Chat)", use_container_width=True):
        deletar_historico(st.session_state.usuario_atual)
        st.sidebar.warning("Banco de dados resetado!")
        st.rerun()
        
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.messages = []
        st.rerun()

    # Exibe histórico na tela
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption=message.get("prompt_user"))
            else:
                st.markdown(message["content"])

    # Sugestões rápidas estilizadas
    if len(st.session_state.messages) == 0:
        st.write("🤖 *Aguardando comandos de voz ou texto. Sugestões de inicialização:*")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💡 Fato Científico Aleatório"):
                st.session_state.comando_rapido = "Me conte um fato científico aleatório e impressionante"
        with col2:
            if st.button("🎨 Renderizar Carro Futurista"):
                st.session_state.comando_rapido = "crie uma imagem de um carro esportivo futurista Cyberpunk"

    prompt = st.chat_input("Insira uma instrução ou solicite uma imagem...")
    if "comando_rapido" in st.session_state:
        prompt = st.session_state.comando_rapido
        del st.session_state.comando_rapido

    if prompt:
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
                with st.status("🎨 Conectando ao cluster de renderização...", expanded=True) as status:
                    st.write("Processando prompt textual...")
                    url_gerada = gerar_url_imagem(prompt_para_imagem)
                    time.sleep(1)
                    st.write("Baixando buffers de imagem...")
                    status.update(label="🎨 Imagem Gerada com Sucesso!", state="complete", expanded=False)
                
                st.image(url_gerada, caption=f"Render: {prompt_para_imagem}")
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({
                    "role": "assistant", 
                    "type": "image",
                    "content": url_gerada,
                    "prompt_user": f"🎨 Render: {prompt_para_imagem}"
                })
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
                st.rerun()
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
            
            try:
                if not MINHA_API_KEY:
                    st.error("Chave API ausente no console operacional!")
                    st.stop()
                
                with st.status("🔍 Buscando dados globais na web...", expanded=True) as status:
                    st.write("Varrendo servidores indexadores...")
                    contexto_web = pesquisar_na_internet(prompt)
                    st.write("Filtrando ruídos e dados duplicados...")
                    time.sleep(0.5)
                    st.write("Injetando contexto nos neurônios da IA...")
                    status.update(label="🔍 Dados da Web Sincronizados!", state="complete", expanded=False)
                
       instrucao_sistema = (
                    "Você é o núcleo operacional de uma inteligência artificial de elite, programada para atingir perfeição absoluta e clareza máxima nas respostas.\n"
                    "Siga estas diretrizes estritas para garantir a melhor explicação possível:\n"
                    "1. DIDÁTICA DE ELITE: Explique conceitos complexos de forma extremamente simples, clara e direta. Use analogias fáceis do dia a dia sempre que possível.\n"
                    "2. ESTRUTURAÇÃO VISUAL: Organize a resposta com tópicos limpos, negritos nas palavras-chave e tabelas comparativas para facilitar a leitura rápida.\n"
                    "3. PRECISÃO DIRETIVA: Use apenas fatos provados e os dados extraídos da internet fornecidos abaixo. Nunca invente ou assuma nada.\n"
                    "4. RESUMO PRÁTICO: No final de explicações longas, adicione um pequeno resumo em um ou dois tópicos.\n\n"
                    f"Banco de dados em tempo real para consulta compulsória:\n{contexto_web}"
                )
                
                groq_history = [{"role": "system", "content": instrucao_sistema}]
                
                for m in st.session_state.messages[-6:-1]:
                    if m.get("type") != "image":
                        groq_history.append({"role": m["role"], "content": m["content"]})
                
                groq_history.append({"role": "user", "content": prompt})
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_history,
                    temperature=0.1
                )
                
                resposta_texto = completion.choices[0].message.content
                
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    texto_acumulado = ""
                    for palavra in resposta_texto.split(" "):
                        texto_acumulado += palavra + " "
                        placeholder.markdown(texto_acumulado + "▌")
                        time.sleep(0.03)
                    placeholder.markdown(resposta_texto)
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                salvar_historico(st.session_state.usuario_atual, st.session_state.messages)
                st.rerun()
                
            except Exception as e:
                st.error(f"Falha na resposta do núcleo: {e}")
