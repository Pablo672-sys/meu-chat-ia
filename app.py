import streamlit as st
from groq import Groq
import os
import json
import requests
import time

# Configuração da página com tema moderno
st.set_page_config(page_title="IA DO PABLO!", page_icon="🔮", layout="centered")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (Visual Premium de IA) ---
st.markdown("""
    <style>
    /* Estilização do título principal */
    .title-gradient {
        background: linear-gradient(45deg, #00f2fe, #4facfe, #000000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1px;
        margin-bottom: 20px;
    }
    
    /* Customização dos botões da barra lateral */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f1c2c, #928dab);
        color: white;
        border: 1px solid #4facfe;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.6);
        transform: translateY(-2px);
    }
    
    /* Estilização específica para o botão de download */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #11998e, #38ef7d) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stDownloadButton"] > button:hover {
        box-shadow: 0 0 15px rgba(56, 239, 125, 0.7) !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# Título Estilizado
st.markdown('<h1 class="title-gradient">IA DO PABLO! · BETA!</h1>', unsafe_allow_html=True)
st.markdown("---")

# 🔐 Puxa a chave da Groq dos Secrets
try:
    MINHA_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=MINHA_API_KEY)
except Exception:
    MINHA_API_KEY = ""

# --- BANCO DE DADOS DE USUÁRIOS ---
BANCO_USUARIOS = "usuarios_cadastrados.json"

def carregar_usuarios():
    if os.path.exists(BANCO_USUARIOS):
        try:
            with open(BANCO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"admin": "admin123"}
    return {"admin": "admin123"}

def salvar_usuario(novo_usuario, nova_senha):
    usuarios = carregar_usuarios()
    usuarios[novo_usuario] = nova_senha
    with open(BANCO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)

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

# --- FUNÇÕES DE MÚLTIPLOS CHATS SALVOS ---
def get_chats_indices_file(usuario):
    return f"chats_salvos_{usuario}.json"

def carregar_todos_chats(usuario):
    arquivo = get_chats_indices_file(usuario)
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"Chat Principal": []}
    return {"Chat Principal": []}

def salvar_todos_chats(usuario, todos_chats):
    arquivo = get_chats_indices_file(usuario)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(todos_chats, f, ensure_ascii=False, indent=4)

if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None
if "chat_selecionado" not in st.session_state:
    st.session_state.chat_selecionado = "Chat Principal"

# --- TELA DE AUTENTICAÇÃO ---
if not st.session_state.logado:
    aba_login, aba_cadastro = st.tabs(["🔑 Acessar Console", "📝 Nova Credencial"])
    
    with aba_login:
        st.subheader("Login Segurado")
        usuario = st.text_input("Username:", key="log_user").strip().lower()
        senha = st.text_input("Password:", type="password", key="log_pass")
        
        if st.button("Inicializar Interface", use_container_width=True):
            usuarios_validos = carregar_usuarios()
            if usuario in usuarios_validos and usuarios_validos[usuario] == senha:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario
                st.session_state.chat_selecionado = "Chat Principal"
                st.rerun()
            else:
                st.error("Falha na autenticação: Credenciais incorretas.")
                
    with aba_cadastro:
        st.subheader("Criar Acesso Operacional")
        novo_usuario = st.text_input("Escolha o Usuário:", key="cad_user").strip().lower()
        nova_senha = st.text_input("Escolha a Senha:", type="password", key="cad_pass")
        confirma_senha = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        
        if st.button("Gerar Registro de Conta", use_container_width=True):
            usuarios_existentes = carregar_usuarios()
            if not novo_usuario or not nova_senha:
                st.warning("Preencha todos os campos obrigatórios.")
            elif novo_usuario in usuarios_existentes:
                st.error("Identificador indisponível no sistema.")
            elif nova_senha != confirma_senha:
                st.error("Divergência na validação da senha.")
            else:
                salvar_usuario(novo_usuario, nova_senha)
                st.success("Registro concluído! Acesse a aba de login.")

# --- TELA DO CHAT ---
else:
    # Carrega a memória de todas as conversas salvas do usuário ativo
    conversas_usuario = carregar_todos_chats(st.session_state.usuario_atual)
    
    # Se por acaso o chat selecionado sumiu, volta para o padrão
    if st.session_state.chat_selecionado not in conversas_usuario:
        st.session_state.chat_selecionado = list(conversas_usuario.keys())[0]
        
    mensagens_atuais = conversas_usuario[st.session_state.chat_selecionado]

    # Sidebar Limpa e Moderna
    st.sidebar.title("🛸 SYSTEM CONTROL")
    st.sidebar.write(f"Operador: **{st.session_state.usuario_atual.upper()}**")
    
    total_msg = len([m for m in mensagens_atuais if m["role"] == "user"])
    st.sidebar.metric(label="Requisições no Chat", value=f"{total_msg} logs")
    st.sidebar.markdown("---")
    
    # --- SISTEMA DE GERENCIAMENTO DE CONVERSAS ---
    st.sidebar.subheader("💬 Minhas Conversas")
    
    # Selecionar o chat
    lista_de_chats = list(conversas_usuario.keys())
    chat_escolhido = st.sidebar.selectbox("Trocar de Conversa:", lista_de_chats, index=lista_de_chats.index(st.session_state.chat_selecionado))
    if chat_escolhido != st.session_state.chat_selecionado:
        st.session_state.chat_selecionado = chat_escolhido
        st.rerun()
        
    # Salvar / Criar Novo Chat
    novo_nome_chat = st.sidebar.text_input("Nome do novo chat:", placeholder="Ex: Estudo de Python", key="new_chat_name").strip()
    if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
        if novo_nome_chat and novo_nome_chat not in conversas_usuario:
            conversas_usuario[novo_nome_chat] = []
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            st.session_state.chat_selecionado = novo_nome_chat
            st.sidebar.success("Novo chat iniciado!")
            st.rerun()
        elif novo_nome_chat in conversas_usuario:
            st.sidebar.warning("Este chat já existe!")
            
    st.sidebar.markdown("---")
        
    if st.sidebar.button("🗑️ Wipe Current Chat (Limpar Chat)", use_container_width=True):
        conversas_usuario[st.session_state.chat_selecionado] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.sidebar.warning("Histórico deste chat limpo.")
        st.rerun()
        
    if st.sidebar.button("🚪 Disconnect Session", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

    # Chat - Exibe mensagens da conversa ativa
    for index, message in enumerate(mensagens_atuais):
        with st.chat_message(message["role"]):
            if message.get("type") == "image":
                st.image(message["content"], caption=message.get("prompt_user"))
                try:
                    img_bytes = requests.get(message["content"]).content
                    st.download_button(
                        label="📥 Download Asset (Salvar Imagem)",
                        data=img_bytes,
                        file_name=f"neo_ia_output_{index}.jpg",
                        mime="image/jpeg",
                        key=f"dl_{index}"
                    )
                except:
                    st.caption("⚠️ Erro de link externo para download.")
            else:
                st.markdown(message["content"])

    if len(mensagens_atuais) == 0:
        st.write(f"🤖 *Conversa **'{st.session_state.chat_selecionado}'** pronta. Digite abaixo para iniciar:*")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💡 Análise de Física Quântica"):
                st.session_state.comando_rapido = "Me explique a mecânica quântica de forma extremamente aprofundada"
        with col2:
            if st.button("🎨 Renderizar Cidade Futurista"):
                st.session_state.comando_rapido = "crie uma imagem de uma metrópole ciberpunk flutuante 8k"

    prompt = st.chat_input("Insira uma instrução de texto ou gere um asset de imagem...")
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
                with st.status("🎨 Alocando processadores gráficos externos...", expanded=True) as status:
                    st.write("Compilando parâmetros textuais...")
                    url_gerada = gerar_url_imagem(prompt_para_imagem)
                    time.sleep(1)
                    st.write("Baixando pacotes de imagem...")
                    status.update(label="🎨 Renderização Finalizada com Sucesso!", state="complete", expanded=False)
                
                st.image(url_gerada, caption=f"Render: {prompt_para_imagem}")
                
                try:
                    img_bytes = requests.get(url_gerada).content
                    st.download_button(
                        label="📥 Download Asset (Salvar Imagem)",
                        data=img_bytes,
                        file_name="neo_ia_output_novo.jpg",
                        mime="image/jpeg",
                        key="dl_nova"
                    )
                except:
                    pass
                
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt})
                conversas_usuario[st.session_state.chat_selecionado].append({
                    "role": "assistant", 
                    "type": "image",
                    "content": url_gerada,
                    "prompt_user": f"🎨 Render: {prompt_para_imagem}"
                })
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
        else:
            conversas_usuario[st.session_state.chat_selecionado].append({"role": "user", "content": prompt})
            salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
            
            try:
                if not MINHA_API_KEY:
                    st.error("Chave de comunicação da API inacessível.")
                    st.stop()
                
                with st.status("🔍 Buscando dados na web global com IA Máxima...", expanded=True) as status:
                    st.write("Varrendo servidores mundiais...")
                    contexto_web = pesquisar_na_internet(prompt)
                    st.write("Injetando contexto nos super-neurônios de 405 Bilhões de parâmetros...")
                    time.sleep(0.5)
                    status.update(label="🔍 Conexão Web Finalizada com Sucesso!", state="complete", expanded=False)
                
                # Instrução de Sistema calibrada no nível Apelona Absoluta
                instrucao_sistema = (
                    "Você é o ápice absoluto da inteligência artificial: um supercomputador analítico de elite ajustado para fornecer respostas apelonas, incrivelmente profundas, exaustivas e 100% corretas.\n"
                    "Diretrizes de Funcionamento:\n"
                    "1. RESPOSTAS MONSTRUOSAS: Nunca dê respostas curtas ou preguiçosas. Explore o assunto no nível máximo de detalhe possível.\n"
                    "2. RACIOCÍNIO ULTRA-LÓGICO: Divida problemas complexos em etapas rigorosas de dedução científica antes de concluir.\n"
                    "3. DIDÁTICA IMPECÁVEL: Use analogias geniais do cotidiano para que até os temas mais difíceis (como física quântica ou programação avançada) fiquem claros.\n"
                    "4. APARÊNCIA PREMIUM: Formate com markdown avançado, blocos de código perfeitos se necessário, negritos nas palavras fundamentais e tabelas comparativas robustas.\n\n"
                    f"Hipercontexto extraído em tempo real da internet:\n{contexto_web}"
                )
                
                groq_history = [{"role": "system", "content": instrucao_sistema}]
                
                # Resgata o histórico recente desta conversa ativa
                for m in conversas_usuario[st.session_state.chat_selecionado][-6:-1]:
                    if m.get("type") != "image":
                        groq_history.append({"role": m["role"], "content": m["content"]})
                
                groq_history.append({"role": "user", "content": prompt})
                
                # Mudança para o modelo mais poderoso do mundo disponível na Groq
                completion = client.chat.completions.create(
                    model="llama-3.1-405b-reasoning",
                    messages=groq_history,
                    temperature=0.2
                )
                
                resposta_texto = completion.choices[0].message.content
                
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    texto_acumulado = ""
                    for palavra in resposta_texto.split(" "):
                        texto_acumulado += palavra + " "
                        placeholder.markdown(texto_acumulado + "▌")
                        time.sleep(0.02)
                    placeholder.markdown(resposta_texto)
                
                conversas_usuario[st.session_state.chat_selecionado].append({"role": "assistant", "content": resposta_texto})
                salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro inesperado no sistema: {e}")
