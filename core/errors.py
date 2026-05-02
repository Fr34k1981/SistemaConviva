"""Erros comuns do sistema."""


class ConvivaError(Exception):
    """Erro base do Sistema Conviva."""


class DatabaseError(ConvivaError):
    """Erro de acesso ao banco."""


class ConfigurationError(ConvivaError):
    """Erro de configuracao."""
