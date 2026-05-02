from pathlib import Path


def test_app_exists():
    assert Path("app.py").exists()


def test_docs_exist():
    assert Path("RELATORIO_AUDITORIA.md").exists()
