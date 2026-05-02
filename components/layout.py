"""Layout base.

Fase atual: funcoes pequenas e seguras para uso futuro.
"""

from __future__ import annotations

import streamlit as st


def aplicar_configuracao_pagina() -> None:
    st.set_page_config(
        page_title="Sistema Conviva 179",
        layout="wide",
        page_icon="🏫",
        initial_sidebar_state="expanded",
    )


def carregar_css_global() -> None:
    return None
