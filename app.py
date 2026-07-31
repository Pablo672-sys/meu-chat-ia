import streamlit as st
from groq import Groq
import os
import json
import requests
import time

# Configuração da página com tema moderno
st.set_page_config(page_title="IA DO PABLO! - Dashboard", page_icon="🔮", layout="centered")

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
st.markdown('<h1 class="title-gradient">🔮 NEO IA · Quantum Interface</h1>', unsafe_allow_html=True)
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
                st.session_state.messages = carregar_historico(usuario)
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
    # Sidebar Estilizada
    st.sidebar.title("🛸 SYSTEM CONTROL")
    st.sidebar.markdown(f"Operador: `<span style='color:#00f2fe;font-weight:bold;'>{st.session_state.usuario_atual.upper()}</span>`", unsafe_allow_html=True)
    
    total_msg = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.sidebar.metric(label="Requisições Efetuadas", value=f"{total_msg} logs")
    
    st.sidebar.markdown("### 🛠️ Core Parameters")
    st.sidebar.code("Model: Llama-3.3-70b\nEngine: Groq Cloud\nUI: Quantum Neo V2\nSearch: Enabled")
    st.sidebar.markdown("---")
        
    if st.sidebar.button("🗑️ Wipe Chat History", use_container_width=True):
        deletar_historico(st.session_state.usuario_atual)
        st.sidebar.warning("Memória local apagada.")
        st.rerun()
        
    if st.sidebar.button("🚪 Disconnect Session", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_atual = None
        st.session_state.messages = []
        st.rerun()

    # Chat
    for index, message in enumerate(st.session_state.messages):
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

    if len(st.session_state.messages) == 0:
        st.write("🤖 *Terminal pronto. Escolha um atalho de instrução rápida:*")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💡 Fato Científico Aleatório"):
                st.session_state.comando_rapido = "Me conte um fato científico aleatório e impressionante"
        with col2:
            if st.button("🎨 Renderizar Carro Futurista"):
                st.session_state.comando_rapido = "crie uma imagem de um carro esportivo futurista Cyberpunk"

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
                    st.error("Chave de comunicação da API inacessível.")
                    st.stop()
                
                with st.status("🔍 Buscando dados globais na rede mundial...", expanded=True) as status:
                    st.write("Indexando referências estáveis...")
                    contexto_web = pesquisar_na_internet(prompt)
                    st.write("Filtrando e validando coerência dos dados...")
                    time.sleep(0.5)
                    st.write("Sincronizando com a memória principal...")
                    status.update(label="🔍 Conexão Web Finalizada com Sucesso!", state="complete", expanded=False)
                
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
                st.error(f"Erro inesperado no sistema: {e}")
