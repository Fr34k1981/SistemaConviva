"""Settings centralizados.

Nao imprime secrets. Mantem nomes atuais de variaveis para compatibilidade.
"""

from __future__ import annotations

import os


def get_env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or default).strip()


SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")
SENHA_EXCLUSAO = get_env("SENHA_EXCLUSAO", "040600")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GEMINI_MODEL = get_env("GEMINI_MODEL", "gemini-2.5-flash")

ESCOLA_NOME_EXIBICAO = "E.E. Professora Eliane Aparecida Dantas da Silva - PEI"
ESCOLA_EMAIL = "e918623@educacao.sp.gov.br"
