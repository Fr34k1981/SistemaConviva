"""Inicializacao central de estado.

Fase atual: modulo preparado para migracao gradual. O `app.py` ainda contem a
maior parte do estado para preservar comportamento.
"""

from __future__ import annotations

import streamlit as st


DEFAULT_STATE = {
    "pagina_atual": "🏠 Dashboard",
    "senha_exclusao_validada": False,
    "backup_manager": None,
    "backup_realizado": False,
}


def inicializar_estado(defaults: dict | None = None) -> None:
    for key, value in {**DEFAULT_STATE, **(defaults or {})}.items():
        if key not in st.session_state:
            st.session_state[key] = value
