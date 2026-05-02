"""Ponto de entrada do Sistema Conviva 179.

Fase 1 da refatoracao: o corpo legado permanece preservado em
legacy_app.py para manter o comportamento atual enquanto as paginas e
servicos sao migrados de forma incremental.
"""

from pathlib import Path
import runpy


LEGACY_APP = Path(__file__).with_name("legacy_app.py")


def main() -> None:
    """Executa o aplicativo legado em cada rerun do Streamlit."""
    runpy.run_path(str(LEGACY_APP), run_name="__main__")


if __name__ == "__main__":
    main()
