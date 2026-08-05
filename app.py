import streamlit as st
import requests
import json
import os
import time
import uuid
import tempfile
from pathlib import Path
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================

st.set_page_config(
    page_title="🔮 NEXUS AI Absolute Core",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTADO DA SESSÃO
# ==========================================

DEFAULTS = {
    "logado": False,
    "usuario_atual": None,
    "chat_selecionado": "Chat Principal",
    "last_call_id": None,
}

for chave, valor in DEFAULTS.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# ==========================================
# CSS PREMIUM
# ==========================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

html,body,.stApp{
    font-family:Inter,sans-serif;
    background:
        radial-gradient(circle at top,#2b1b63 0%,#12091f 45%,#050308 100%);
    color:white;
}

/* Scroll */

::-webkit-scrollbar{
width:10px;
}

::-webkit-scrollbar-thumb{
background:#4f46e5;
border-radius:20px;
}

/* Título */

.hero-title{

font-size:52px;

font-weight:900;

text-align:center;

background:linear-gradient(
90deg,
#00f5ff,
#7c3aed,
#38bdf8
);

-webkit-background-clip:text;

-webkit-text-fill-color:transparent;

margin-top:10px;

margin-bottom:0;

}

.hero-sub{

text-align:center;

color:#94a3b8;

font-size:18px;

margin-bottom:25px;

}

/* Cards */

div[data-testid="stChatMessage"]{

background:rgba(255,255,255,.06);

border:1px solid rgba(255,255,255,.12);

backdrop-filter:blur(18px);

border-radius:18px;

padding:20px;

margin-bottom:15px;

transition:.3s;

}

div[data-testid="stChatMessage"]:hover{

transform:translateY(-2px);

border:1px solid #4f46e5;

}

/* Sidebar */

section[data-testid="stSidebar"]{

background:#090714;

}

/* Botões */

.stButton button{

width:100%;

border:none;

border-radius:12px;

background:linear-gradient(
135deg,
#2563eb,
#4f46e5
);

font-weight:700;

color:white;

padding:12px;

transition:.3s;

}

.stButton button:hover{

transform:scale(1.03);

box-shadow:0 0 20px #4f46e5;

}

/* Inputs */

.stTextInput input{

border-radius:12px;

background:#0f172a;

color:white;

}

/* Chat */

textarea{

font-size:16px;

}

code{

background:#111827!important;

color:#22d3ee!important;

}

</style>
""", unsafe_allow_html=True)

st.markdown(
"""
<div class="hero-title">
🔮 NEXUS AI Absolute Core
</div>

<div class="hero-sub">
Inteligência Artificial • Voz • Imagens • Código • Automação
</div>
""",
unsafe_allow_html=True
)

st.divider()

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BANCO_USUARIOS = "usuarios_cadastrados.json"

TIMEOUT = 20

MAX_HISTORICO = 20

IMAGE_SIZE = (1024,1024)
