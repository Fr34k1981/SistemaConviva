"""
Exemplos Práticos do Sistema de Tratamento de Erros
Demonstra como usar o error_handler em cenários reais
"""

from src.error_handler import (
    com_tratamento_erro, com_retry, com_validacao,
    ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
    ErroOperacaoDB, ErroArquivo, ErroNaoEncontrado,
    ErroDuplicado, Validadores
)


# ===== EXEMPLO 1: Validar e Salvar Aluno =====

@com_tratamento_erro
def exemplo_salvar_aluno_valid(nome, email, ra, turma):
    """
    Demonstra:
    - Validação com Validadores
    - Lançamento de ErroValidacao
    - ErroOperacaoDB para operações que falham
    """
    # Validar nome
    valido, msg = Validadores.validar_nome(nome)
    if not valido:
        raise ErroValidacao("nome", msg)
    
    # Validar email
    valido, msg = Validadores.validar_email(email)
    if not valido:
        raise ErroValidacao("email", msg)
    
    # Validar turma
    valido, msg = Validadores.validar_nao_vazio(turma, "Turma")
    if not valido:
        raise ErroValidacao("turma", msg)
    
    # Simular salvamento
    print(f"✅ Aluno '{nome}' salvo com sucesso")
    return True


# ===== EXEMPLO 2: Carregar com Retry =====

@com_tratamento_erro
@com_retry(tentativas=3, intervalo=0.5)
def exemplo_carregar_dados_instavel():
    """
    Demonstra:
    - Retry automático em caso de ConnectionError
    - 3 tentativas com 0.5s entre elas
    """
    import random
    
    # Simula falha intermitente (60% de chance falha)
    if random.random() < 0.6:
        raise ConnectionError("Conexão perdida com o servidor")
    
    print("✅ Dados carregados")
    return {"dados": "sucesso"}


# ===== EXEMPLO 3: Multiples Validações =====

@com_tratamento_erro
def exemplo_registrar_ocorrencia(aluno, data, gravidade, descricao):
    """
    Demonstra:
    - Múltiplas validações encadeadas
    - Diferentes tipos de ErroValidacao
    """
    # Validar aluno
    valido, msg = Validadores.validar_nao_vazio(aluno, "Aluno")
    if not valido:
        raise ErroValidacao("aluno", msg)
    
    # Validar data
    valido, msg = Validadores.validar_data(data)
    if not valido:
        raise ErroValidacao("data", msg)
    
    # Validar gravidade
    gravidades_validas = ["Leve", "Média", "Grave", "Gravíssima"]
    if gravidade not in gravidades_validas:
        raise ErroValidacao("gravidade", f"Use: {', '.join(gravidades_validas)}")
    
    # Validar descrição
    valido, msg = Validadores.validar_nao_vazio(descricao, "Descrição")
    if not valido:
        raise ErroValidacao("descricao", msg)
    
    print(f"✅ Ocorrência registrada: {aluno} - {gravidade}")
    return True


# ===== EXEMPLO 4: Carregar Arquivo =====

@com_tratamento_erro
def exemplo_carregar_csv(caminho_arquivo):
    """
    Demonstra:
    - Tratamento de ErroArquivo
    - Tratamento específico por tipo de erro
    """
    import csv
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            dados = list(csv.DictReader(f))
        
        if not dados:
            raise ErroCarregamentoDados("CSV", "Arquivo vazio")
        
        print(f"✅ Carregado {len(dados)} registros")
        return dados
    
    except FileNotFoundError:
        raise ErroArquivo("abrir", caminho_arquivo, "Arquivo não existe")
    except PermissionError:
        raise ErroArquivo("ler", caminho_arquivo, "Sem permissão de leitura")
    except Exception as e:
        raise ErroArquivo("processar", caminho_arquivo, str(e))


# ===== EXEMPLO 5: Verificar Duplicatas =====

@com_tratamento_erro
def exemplo_validar_duplicatas(lista_alunos, novo_aluno):
    """
    Demonstra:
    - ErroDuplicado quando encontra duplicata
    - Busca em lista
    """
    # Verificar se aluno já existe
    for aluno in lista_alunos:
        if aluno.lower() == novo_aluno.lower():
            raise ErroDuplicado("Aluno", novo_aluno)
    
    print(f"✅ Aluno '{novo_aluno}' pode ser cadastrado")
    return True


# ===== EXEMPLO 6: Operação com Múltiplos Passos =====

@com_tratamento_erro
def exemplo_processar_turma_completo(turma_nome, alunos_csv):
    """
    Demonstra:
    - Pipeline com múltiplas operações
    - Validação em cada passo
    - Diferentes tipos de erro
    """
    # Passo 1: Validar turma
    valido, msg = Validadores.validar_nao_vazio(turma_nome, "Turma")
    if not valido:
        raise ErroValidacao("turma", msg)
    
    # Passo 2: Validar lista de alunos
    valido, msg = Validadores.validar_lista_nao_vazia(alunos_csv, "alunos")
    if not valido:
        raise ErroValidacao("alunos", msg)
    
    # Passo 3: Processar cada aluno
    for aluno_nome in alunos_csv:
        valido, msg = Validadores.validar_nome(aluno_nome)
        if not valido:
            raise ErroValidacao("nome_aluno", f"'{aluno_nome}': {msg}")
    
    # Passo 4: Simular salvamento
    print(f"✅ Turma '{turma_nome}' processada com {len(alunos_csv)} alunos")
    return True


# ===== TESTES =====

if __name__ == "__main__":
    import streamlit as st
    
    print("\n" + "="*60)
    print("EXEMPLOS DE TRATAMENTO DE ERROS")
    print("="*60 + "\n")
    
    # Teste 1: Validação bem-sucedida
    print("📝 Teste 1: Salvar aluno válido")
    resultado = exemplo_salvar_aluno_valid("João Silva", "joao@example.com", "12345", "1º A")
    print()
    
    # Teste 2: Validação com erro
    print("📝 Teste 2: Salvar aluno com email inválido")
    resultado = exemplo_salvar_aluno_valid("Maria", "email-invalido", "67890", "1º B")
    print()
    
    # Teste 3: Registrar ocorrência
    print("📝 Teste 3: Registrar ocorrência válida")
    resultado = exemplo_registrar_ocorrencia("João Silva", "25/01/2024", "Média", "Não fez lição")
    print()
    
    # Teste 4: Registrar ocorrência com data inválida
    print("📝 Teste 4: Registrar ocorrência com data inválida")
    resultado = exemplo_registrar_ocorrencia("João", "25-01-2024", "Leve", "Teste")
    print()
    
    # Teste 5: Verificar duplicatas
    print("📝 Teste 5: Verificar duplicatas")
    alunos = ["João", "Maria", "Pedro"]
    resultado = exemplo_validar_duplicatas(alunos, "Carlos")
    print()
    
    print("📝 Teste 6: Aluno duplicado")
    resultado = exemplo_validar_duplicatas(alunos, "João")
    print()
    
    # Teste 7: Processamento com múltiplos passos
    print("📝 Teste 7: Processar turma completa")
    resultado = exemplo_processar_turma_completo("1º A", ["João", "Maria", "Pedro"])
    print()
    
    print("="*60)
    print("✅ EXEMPLOS CONCLUÍDOS")
    print("="*60)
