    index=lista_de_chats.index(st.session_state.chat_selecionado),
)

if chat_escolhido != st.session_state.chat_selecionado:
    st.session_state.chat_selecionado = chat_escolhido
    st.rerun()

novo_nome_chat = st.sidebar.text_input(
    "Novo Chat:", key="new_chat_input", placeholder="Nome da conversa..."
).strip()
if st.sidebar.button("➕ Criar Novo Chat", use_container_width=True):
    if novo_nome_chat and novo_nome_chat not in conversas_usuario:
        conversas_usuario[novo_nome_chat] = []
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.session_state.chat_selecionado = novo_nome_chat
        st.rerun()

st.sidebar.markdown("---")

if st.session_state.chat_selecionado != "Chat Principal":
    if st.sidebar.button("❌ Apagar Chat Atual", use_container_width=True):
        del conversas_usuario[st.session_state.chat_selecionado]
        salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
        st.session_state.chat_selecionado = "Chat Principal"
        st.rerun()

if st.sidebar.button("🗑️ Limpar Mensagens", use_container_width=True):
    conversas_usuario[st.session_state.chat_selecionado] = []
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)
    st.rerun()

# ==========================================
# 7. EXIBIÇÃO DE MENSAGENS E ENTRADA
# ==========================================
if not mensagens_atuais:
    st.markdown(
        """
        <div class="welcome">
            <div class="welcome-icon">🤖</div>
            <div class="welcome-title">Como posso ajudar?</div>
            <div class="welcome-text">Pergunte, pesquise, programe ou crie.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in mensagens_atuais:
    if not isinstance(message, dict):
        continue
    role = message.get("role")
    if role not in ("user", "assistant"):
        continue
    content = str(message.get("content", ""))
    with st.chat_message(role):
        if message.get("type") == "image":
            st.image(content, caption="Imagem gerada")
        else:
            st.markdown(content)

texto_input = st.chat_input("Pergunte algo, peça scripts ou gere imagens...")

if texto_input:
    conversas_usuario[st.session_state.chat_selecionado].append(
        {"role": "user", "content": texto_input}
    )
    salvar_todos_chats(st.session_state.usuario_atual, conversas_usuario)

    with st.chat_message("user"):
        st.markdown(texto_input)

    prompt_minusculo = texto_input.lower()
    comando_imagem = any(
        cmd in prompt_minusculo
        for cmd in ["crie uma imagem", "gere uma imagem", "desenhe", "foto de"]
    )

    with st.chat_message("assistant"):
        if comando_imagem:
            with st.spinner("🎨 Gerando imagem..."):
                url_gerada = gerar_url_imagem(texto_input)
                st.image(url_gerada, caption="Imagem gerada em HD")
                conversas_usuario[st.session_state.chat_selecionado].append(
                    {"role": "assistant", "type": "image", "content": url_gerada}
                )
                salvar_todos_chats(
                    st.session_state.usuario_atual, conversas_usuario
                )
        else:
            with st.spinner("⚡ AI DO PABLO pesquisando e processando..."):
                resposta_texto = chamar_ia_suprema(
                    conversas_usuario[st.session_state.chat_selecionado],
                    texto_input,
                )
                st.markdown(resposta_texto)
                if st.session_state.youtube_na_proxima:
                    videos = pesquisar_youtube(texto_input)
                    if videos:
                        st.markdown("### 🎥 Vídeos relacionados")
                        for video in videos:
                            st.markdown(f'- [{video["title"]}]({video["url"]})')
                    else:
                        st.caption("Nenhum vídeo relacionado foi encontrado.")
                    st.session_state.youtube_na_proxima = False
                conversas_usuario[st.session_state.chat_selecionado].append(
                    {"role": "assistant", "content": resposta_texto}
                )
                salvar_todos_chats(
                    st.session_state.usuario_atual, conversas_usuario
                )
