"""
Sistema Centralizado de Tratamento de Erros
Fornece exceções customizadas e handlers robustos
"""
import streamlit as st
from typing import Callable, Any, Optional, Type
from functools import wraps
import logging
from datetime import datetime


# --- SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ===== EXCEÇÕES CUSTOMIZADAS =====

class SistemaConvivaException(Exception):
    """Exceção base do sistema"""
    def __init__(self, mensagem: str, detalhe: str = None, codigo: str = None):
        self.mensagem = mensagem
        self.detalhe = detalhe
        self.codigo = codigo or "ERRO_GENERICO"
        super().__init__(self.mensagem)


class ErroConexaoDB(SistemaConvivaException):
    """Erro ao conectar com o banco de dados"""
    def __init__(self, detalhe: str = None):
        super().__init__(
            mensagem="❌ Erro de conexão com o banco de dados",
            detalhe=detalhe or "Não foi possível conectar ao Supabase. Verifique sua conexão.",
            codigo="CONEXAO_DB_FALHOU"
        )


class ErroValidacao(SistemaConvivaException):
    """Erro de validação de dados"""
    def __init__(self, campo: str, mensagem: str):
        super().__init__(
            mensagem=f"❌ Erro de validação em '{campo}'",
            detalhe=mensagem,
            codigo="VALIDACAO_FALHOU"
        )


class ErroCarregamentoDados(SistemaConvivaException):
    """Erro ao carregar dados"""
    def __init__(self, tipo_dado: str, detalhe: str = None):
        super().__init__(
            mensagem=f"❌ Erro ao carregar {tipo_dado}",
            detalhe=detalhe or f"Não foi possível carregar {tipo_dado}. Tente novamente.",
            codigo="CARREGAMENTO_DADOS_FALHOU"
        )


class ErroOperacaoDB(SistemaConvivaException):
    """Erro ao realizar operação no BD"""
    def __init__(self, operacao: str, detalhe: str = None):
        super().__init__(
            mensagem=f"❌ Erro ao {operacao}",
            detalhe=detalhe or f"Não foi possível {operacao}. Tente novamente.",
            codigo="OPERACAO_DB_FALHOU"
        )


class ErroArquivo(SistemaConvivaException):
    """Erro ao manipular arquivo"""
    def __init__(self, operacao: str, arquivo: str, detalhe: str = None):
        super().__init__(
            mensagem=f"❌ Erro ao {operacao} arquivo '{arquivo}'",
            detalhe=detalhe or "Verifique se o arquivo existe e tem permissões de leitura.",
            codigo="ARQUIVO_ERRO"
        )


class ErroAutenticacao(SistemaConvivaException):
    """Erro de autenticação/permissão"""
    def __init__(self, recurso: str = "recurso"):
        super().__init__(
            mensagem=f"❌ Acesso negado ao {recurso}",
            detalhe="Você não tem permissão para acessar este recurso.",
            codigo="AUTENTICACAO_FALHOU"
        )


class ErroValidacaoSenha(SistemaConvivaException):
    """Erro de validação de senha"""
    def __init__(self):
        super().__init__(
            mensagem="❌ Senha incorreta",
            detalhe="A senha digitada está incorreta. Tente novamente.",
            codigo="SENHA_INCORRETA"
        )


class ErroDuplicado(SistemaConvivaException):
    """Erro quando registro já existe"""
    def __init__(self, tipo: str, valor: str):
        super().__init__(
            mensagem=f"❌ {tipo} já existe",
            detalhe=f"'{valor}' já foi cadastrado no sistema.",
            codigo="JA_EXISTE"
        )


class ErroNaoEncontrado(SistemaConvivaException):
    """Erro quando registro não é encontrado"""
    def __init__(self, tipo: str, identificador: str):
        super().__init__(
            mensagem=f"❌ {tipo} não encontrado",
            detalhe=f"Não foi possível encontrar {tipo} com identificador '{identificador}'.",
            codigo="NAO_ENCONTRADO"
        )


class ErroPermissao(SistemaConvivaException):
    """Erro de permissão"""
    def __init__(self, acao: str):
        super().__init__(
            mensagem="❌ Permissão negada",
            detalhe=f"Você não tem permissão para {acao}.",
            codigo="PERMISSAO_NEGADA"
        )


# ===== HANDLERS DE ERRO =====

def tratar_erro(exception: Exception, contexto: str = "operação") -> tuple[bool, str, str]:
    """
    Trata exceção e retorna mensagem formatada
    
    Args:
        exception: Exceção capturada
        contexto: Contexto onde o erro ocorreu
    
    Returns:
        (sucesso, titulo, detalhes)
    """
    logger.error(f"Erro em {contexto}: {str(exception)}", exc_info=True)
    
    if isinstance(exception, SistemaConvivaException):
        return (False, exception.mensagem, exception.detalhe)
    
    elif isinstance(exception, ValueError):
        return (False, "❌ Valores inválidos", str(exception))
    
    elif isinstance(exception, KeyError):
        return (False, "❌ Campo não encontrado", f"O campo '{str(exception)}' não foi encontrado.")
    
    elif isinstance(exception, PermissionError):
        return (False, "❌ Acesso negado", "Você não tem permissão para realizar esta operação.")
    
    elif isinstance(exception, FileNotFoundError):
        return (False, "❌ Arquivo não encontrado", f"Arquivo: {str(exception)}")
    
    elif isinstance(exception, ConnectionError):
        return (False, "❌ Erro de conexão", "Verifique sua conexão com a internet.")
    
    elif isinstance(exception, TimeoutError):
        return (False, "❌ Timeout", "A operação demorou muito tempo. Tente novamente.")
    
    else:
        return (False, "❌ Erro inesperado", f"{contexto}: {str(exception)}")


def exibir_erro(titulo: str, detalhes: str, codigo: str = None):
    """Exibe erro no Streamlit com estilo profissional"""
    from src.components import render_error_message
    
    erro_completo = detalhes
    if codigo:
        erro_completo += f"\n\n**Código:** {codigo}"
    
    render_error_message(erro_completo)


def registrar_erro_log(titulo: str, detalhes: str, codigo: str = None):
    """Registra erro no arquivo de log"""
    log_msg = f"{titulo} | {detalhes}"
    if codigo:
        log_msg += f" | {codigo}"
    logger.error(log_msg)


# ===== DECORADORES =====

def com_tratamento_erro(funcao: Callable) -> Callable:
    """
    Decorador que envolve função com tratamento de erro
    Usa st.error para exibir mensagens
    """
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        try:
            return funcao(*args, **kwargs)
        except SistemaConvivaException as e:
            exibir_erro(e.mensagem, e.detalhe, e.codigo)
            registrar_erro_log(e.mensagem, e.detalhe, e.codigo)
            return None
        except Exception as e:
            sucesso, titulo, detalhes = tratar_erro(e, funcao.__name__)
            exibir_erro(titulo, detalhes)
            registrar_erro_log(titulo, detalhes)
            return None
    
    return wrapper


def com_validacao(validador: Callable[[Any], tuple[bool, str]]) -> Callable:
    """
    Decorador que valida entrada antes de executar função
    
    validador: função que retorna (válido, mensagem_erro)
    """
    def decorador(funcao: Callable) -> Callable:
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            dados = args[0] if args else kwargs.get('dados')
            valido, mensagem = validador(dados)
            
            if not valido:
                raise ErroValidacao("dados", mensagem)
            
            return funcao(*args, **kwargs)
        
        return wrapper
    return decorador


def com_retry(tentativas: int = 3, intervalo: float = 1.0) -> Callable:
    """
    Decorador com retry automático
    
    Args:
        tentativas: Número de tentativas
        intervalo: Intervalo entre tentativas em segundos
    """
    def decorador(funcao: Callable) -> Callable:
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            import time
            
            ultima_excecao = None
            for tentativa in range(1, tentativas + 1):
                try:
                    return funcao(*args, **kwargs)
                
                except SistemaConvivaException as e:
                    ultima_excecao = e
                    if tentativa < tentativas:
                        logger.warning(f"Tentativa {tentativa}/{tentativas} falhou. Retrying em {intervalo}s...")
                        time.sleep(intervalo)
                
                except Exception as e:
                    ultima_excecao = e
                    if tentativa < tentativas:
                        logger.warning(f"Tentativa {tentativa}/{tentativas} falhou com: {str(e)}. Retrying...")
                        time.sleep(intervalo)
            
            # Todas as tentativas falharam
            sucesso, titulo, detalhes = tratar_erro(ultima_excecao, funcao.__name__)
            exibir_erro(titulo, detalhes + f"\n(Após {tentativas} tentativas)")
            registrar_erro_log(titulo, detalhes, "RETRY_FALHOU")
            return None
        
        return wrapper
    return decorador


# ===== VALIDADORES =====

class Validadores:
    """Coleção de funções de validação"""
    
    @staticmethod
    def validar_nome(nome: str, campo: str = "Nome") -> tuple[bool, str]:
        """Valida se nome não está vazio e tem tamanho adequado"""
        if not nome or not nome.strip():
            return False, f"{campo} não pode estar vazio"
        
        if len(nome) < 3:
            return False, f"{campo} deve ter pelo menos 3 caracteres"
        
        if len(nome) > 100:
            return False, f"{campo} deve ter no máximo 100 caracteres"
        
        return True, ""
    
    @staticmethod
    def validar_email(email: str) -> tuple[bool, str]:
        """Valida formato de email"""
        import re
        
        if not email:
            return True, ""  # Email é opcional
        
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(padrao, email):
            return False, "Email inválido"
        
        return True, ""
    
    @staticmethod
    def validar_data(data_str: str) -> tuple[bool, str]:
        """Valida formato de data (DD/MM/YYYY)"""
        from datetime import datetime
        
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True, ""
        except ValueError:
            return False, "Data inválida. Use formato DD/MM/YYYY"
    
    @staticmethod
    def validar_nao_vazio(valor: str, campo: str = "Campo") -> tuple[bool, str]:
        """Valida se campo não está vazio"""
        if not valor or not str(valor).strip():
            return False, f"{campo} é obrigatório"
        
        return True, ""
    
    @staticmethod
    def validar_lista_nao_vazia(lista: list, campo: str = "Lista") -> tuple[bool, str]:
        """Valida se lista não está vazia"""
        if not lista or len(lista) == 0:
            return False, f"Selecione pelo menos um {campo}"
        
        return True, ""
    
    @staticmethod
    def validar_numero(valor: Any, minimo: int = None, maximo: int = None) -> tuple[bool, str]:
        """Valida se é número dentro do intervalo"""
        try:
            num = float(valor)
            
            if minimo is not None and num < minimo:
                return False, f"Valor deve ser >= {minimo}"
            
            if maximo is not None and num > maximo:
                return False, f"Valor deve ser <= {maximo}"
            
            return True, ""
        
        except (ValueError, TypeError):
            return False, "Valor inválido. Digite um número"


# ===== HELPER PARA SUPABASE =====

def verificar_conexao_supabase(supabase_valid: bool) -> bool:
    """Verifica se Supabase está configurado"""
    if not supabase_valid:
        raise ErroConexaoDB(
            "SUPABASE_URL ou SUPABASE_KEY não configuradas. "
            "Verifique o arquivo .env"
        )
    return True


# ===== CRIAR LOGS DIRECTORY =====
import os
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
