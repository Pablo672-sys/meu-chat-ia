import streamlit as st
import os
import json
import requests
import time
import tempfile
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="NEXUS AI · Absolute Core",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

/* Fundo */

.stApp{

background:
linear-gradient(
135deg,
#090714 0%,
#110c28 45%,
#05030a 100%
);

color:#f8fafc;

font-family:
Inter,
system-ui,
sans-serif;

}

/* Título */

.hero-title{

background:linear-gradient(
90deg,
#00f2fe,
#4facfe,
#7f00ff
);

-webkit-background-clip:text;

-webkit-text-fill-color:transparent;

font-size:42px;

font-weight:900;

text-align:center;

margin-bottom:5px;

}

/* Sub */

.hero-subtitle{

color:#94a3b8;

text-align:center;

margin-bottom:25px;

}

/* Chat */

div[data-testid="stChatMessage"]{

background:rgba(22,19,43,.75)!important;

border-radius:18px!important;

padding:20px!important;

border:1px solid rgba(255,255,255,.08)!important;

backdrop-filter:blur(12px);

margin-bottom:15px;

}

/* Botões */

.stButton>button{

background:
linear-gradient(
135deg,
#2563eb,
#1d4ed8
);

border:none;

border-radius:10px;

font-weight:bold;

color:white;

transition:.3s;

}

.stButton>button:hover{

transform:translateY(-2px);

box-shadow:0 0 18px rgba(37,99,235,.6);

}

/* Código */

code{

background:#0f172a!important;

color:#38bdf8!important;

padding:4px 8px;

border-radius:6px;

}

</style>
""", unsafe_allow_html=True)

st.markdown(
'<h1 class="hero-title">🔮 NEXUS AI · Absolute Core</h1>',
unsafe_allow_html=True
)

st.markdown(
'<p class="hero-subtitle">Inteligência Suprema · Respostas Detalhadas · Imagens & Voz</p>',
unsafe_allow_html=True
)

st.divider()

# =====================================================
# CONFIGURAÇÕES
# =====================================================

BANCO_USUARIOS = "usuarios_cadastrados.json"

REQUEST_TIMEOUT = 20

MAX_HISTORICO = 20
