"""Sidebar base para migracao gradual."""

from __future__ import annotations

import streamlit as st


def renderizar_sidebar(itens: list[dict] | None = None) -> str:
    itens = itens or [{"nome": "Dashboard", "icone": "🏠"}]
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = f"{itens[0]['icone']} {itens[0]['nome']}"
    for item in itens:
        nome = f"{item['icone']} {item['nome']}"
        if st.sidebar.button(nome, use_container_width=True):
            st.session_state.pagina_atual = nome
            st.rerun()
    return st.session_state.pagina_atual
