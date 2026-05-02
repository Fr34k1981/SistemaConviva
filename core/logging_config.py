"""Configuracao de logging."""

from __future__ import annotations

import logging


def get_logger(name: str = "conviva179") -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return logging.getLogger(name)
