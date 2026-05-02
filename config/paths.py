"""Caminhos centrais do Sistema Conviva 179.

Este modulo e passivo nesta fase: ele prepara a extracao gradual de `app.py`
sem alterar o comportamento atual.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = DATA_DIR / "backups"
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
