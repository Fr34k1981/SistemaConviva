# 🛡️ Sistema Tratamento de Erros - Guia Completo

## Visão Geral

Sistema centralizado e profissional de tratamento de erros com:
- ✅ Exceções customizadas específicas para cada cenário
- ✅ Mensagens de erro amigáveis e informativas
- ✅ Registro automático em logs
- ✅ Decoradores para tratamento automático
- ✅ Validadores reutilizáveis
- ✅ Sistema de retry automático

---

## 1. Exceções Customizadas

### Base Class
```python
SistemaConvivaException(mensagem: str, detalhe: str = None, codigo: str = None)
```

### Tipos de Exceções

#### ErroConexaoDB
Erro ao conectar com Supabase
```python
raise ErroConexaoDB()  # Mensagem padrão
raise ErroConexaoDB("SUPABASE_URL não definido")  # Com detalhe
```

#### ErroValidacao
Erro de validação de dados
```python
raise ErroValidacao(campo="email", mensagem="Email inválido")
```

#### ErroCarregamentoDados
Erro ao carregar dados
```python
raise ErroCarregamentoDados(tipo_dado="alunos")
raise ErroCarregamentoDados(tipo_dado="professores", detalhe="Turma não existe")
```

#### ErroOperacaoDB
Erro ao salvar/atualizar dados
```python
raise ErroOperacaoDB(operacao="salvar aluno")
raise ErroOperacaoDB(operacao="atualizar ocorrência", detalhe="Campo obrigatório faltando")
```

#### ErroArquivo
Erro ao manipular arquivo
```python
raise ErroArquivo(operacao="abrir", arquivo="data/turmas/1º A.csv")
raise ErroArquivo(operacao="salvar", arquivo="backup.zip", detalhe="Sem espaço em disco")
```

#### ErroAutenticacao
Erro de autenticação/permissão
```python
raise ErroAutenticacao(recurso="página de administradores")
```

#### ErroValidacaoSenha
Senha incorreta
```python
raise ErroValidacaoSenha()
```

#### ErroDuplicado
Registro já existe
```python
raise ErroDuplicado(tipo="Aluno", valor="João Silva")
raise ErroDuplicado(tipo="Email", valor="teste@example.com")
```

#### ErroNaoEncontrado
Registro não encontrado
```python
raise ErroNaoEncontrado(tipo="Aluno", identificador="João Silva")
raise ErroNaoEncontrado(tipo="Turma", identificador="1º A")
```

#### ErroPermissao
Permissão negada
```python
raise ErroPermissao(acao="deletar ocorrências de outros usuários")
```

---

## 2. Decoradores

### `@com_tratamento_erro`
Trata automaticamente qualquer exceção na função
```python
@com_tratamento_erro
def carregar_dados():
    # Se lançar exceção, é tratada automaticamente
    return dados
```

**Comportamento:**
- Captura qualquer exceção (SistemaConvivaException ou genérica)
- Exibe mensagem no Streamlit
- Registra em log
- Retorna None
- Continua execução do app

### `@com_validacao(validador)`
Valida entrada antes de executar
```python
@com_validacao(Validadores.validar_nao_vazio)
def processar_nome(nome):
    return nome.upper()
```

### `@com_retry(tentativas=3, intervalo=1.0)`
Retry automático em caso de falha
```python
@com_retry(tentativas=3, intervalo=0.5)
def conectar_supabase():
    # Tenta 3 vezes com 0.5s entre tentativas
    return supabase.connect()
```

**Casos de uso:**
- Operações de rede instáveis
- Conexões com BD intermitentes
- Operações concorrentes

---

## 3. Validadores

### Uso Básico
```python
from src.error_handler import Validadores

# Validar nome
valido, msg = Validadores.validar_nome("João")
if not valido:
    st.error(msg)

# Validar email
valido, msg = Validadores.validar_email("teste@example.com")

# Validar data
valido, msg = Validadores.validar_data("25/12/2024")

# Validar lista
valido, msg = Validadores.validar_lista_nao_vazia(turmas_selecionadas, "turmas")

# Validar número
valido, msg = Validadores.validar_numero(idade, minimo=5, maximo=18)
```

### Validadores Disponíveis
| Validador | Descrição | Exemplo |
|-----------|-----------|---------|
| `validar_nome()` | Nome com 3-100 char | João Silva |
| `validar_email()` | Formato de email | test@example.com |
| `validar_data()` | Formato DD/MM/YYYY | 25/12/2024 |
| `validar_nao_vazio()` | Campo não vazio | Qualquer valor |
| `validar_lista_nao_vazia()` | Lista com elementos | [1, 2, 3] |
| `validar_numero()` | Número no intervalo | 42 (entre 0 e 100) |

---

## 4. Padrões de Uso

### Padrão 1: Carregar Dados
```python
from src.error_handler import com_tratamento_erro, ErroCarregamentoDados

@com_tratamento_erro
def carregar_turmas():
    try:
        response = supabase.table("turmas").select("*").execute()
        if not response.data:
            raise ErroCarregamentoDados("turmas", "Nenhuma turma cadastrada")
        return response.data
    except Exception as e:
        raise ErroCarregamentoDados("turmas", str(e))

# Uso
turmas = carregar_turmas()  # Se erro, já trata automaticamente
```

### Padrão 2: Salvar com Validação
```python
from src.error_handler import com_tratamento_erro, ErroValidacao, ErroOperacaoDB, Validadores

@com_tratamento_erro
def salvar_aluno(nome, email, ra):
    # Validar
    valido, msg = Validadores.validar_nome(nome)
    if not valido:
        raise ErroValidacao("nome", msg)
    
    valido, msg = Validadores.validar_email(email)
    if not valido:
        raise ErroValidacao("email", msg)
    
    # Salvar
    try:
        supabase.table("alunos").insert({
            "nome": nome,
            "email": email,
            "ra": ra
        }).execute()
        return True
    except Exception as e:
        raise ErroOperacaoDB("salvar aluno", str(e))
```

### Padrão 3: Operação com Retry
```python
from src.error_handler import com_retry, ErroConexaoDB

@com_retry(tentativas=3, intervalo=1.0)
def sincronizar_com_supabase():
    # Se falhar na conexão, tenta 3 vezes
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### Padrão 4: Arquivo com Tratamento
```python
from src.error_handler import com_tratamento_erro, ErroArquivo
import csv

@com_tratamento_erro
def carregar_csv(caminho):
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        raise ErroArquivo("abrir", caminho, "Arquivo não existe")
    except PermissionError:
        raise ErroArquivo("abrir", caminho, "Sem permissão de leitura")
    except Exception as e:
        raise ErroArquivo("ler", caminho, str(e))
```

---

## 5. Configuração em app.py

### Importar
```python
from src.error_handler import (
    com_tratamento_erro, com_retry, com_validacao,
    ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
    ErroOperacaoDB, ErroArquivo, ErroAutenticacao,
    ErroDuplicado, ErroNaoEncontrado, ErroPermissao,
    Validadores, tratar_erro, exibir_erro
)
```

### Substituir `_supabase_error()`
```python
# ANTES
def _supabase_error(acao):
    if not SUPABASE_VALID:
        st.error(f"SUPABASE_URL ou SUPABASE_KEY não configuradas.")
        return True
    return False

# DEPOIS
def _supabase_error(acao):
    if not SUPABASE_VALID:
        raise ErroConexaoDB(f"Não foi possível {acao}")
    return False
```

### Envolver Funções
```python
# ANTES
def carregar_alunos():
    return _supabase_get_dataframe("alunos?select=*", "carregar alunos")

# DEPOIS
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_alunos():
    response = _supabase_request("GET", "alunos?select=*")
    if response.status_code != 200:
        raise ErroCarregamentoDados("alunos")
    return pd.DataFrame(response.json())
```

---

## 6. Logs

### Arquivo de Log
Erro automático em: `logs/app.log`

```
2024-01-15 14:32:10,123 - root - ERROR - ❌ Erro de validação em 'email' | Email inválido | VALIDACAO_FALHOU
2024-01-15 14:33:25,456 - root - ERROR - ❌ Erro ao carregar alunos | Timeout de conexão | CARREGAMENTO_DADOS_FALHOU
```

### Ler Logs
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Iniciando importação de arquivos")
logger.warning("Arquivo não encontrado, usando padrão")
logger.error("Falha ao conectar com BD")
```

---

## 7. Mensagens de Erro

### Estrutura
```
[Titulo curto e descritivo]
[Detalhe com orientação do que fazer]
[Código do erro (opcional)]
```

### Exemplos
```
❌ Erro de validação em 'email'
Email inválido. Use o formato: usuario@exemplo.com

Código: VALIDACAO_FALHOU
```

```
❌ Erro ao carregar alunos
Não foi possível conectar ao servidor. Verifique sua internet
e tente novamente em alguns segundos.

Código: CONEXAO_DB_FALHOU
```

```
❌ Aluno já existe
'João Silva' já foi cadastrado no sistema.

Código: JA_EXISTE
```

---

## 8. Melhores Práticas

✅ **Faça:**
- Use exceções específicas (ErroValidacao, não ValueError)
- Forneça contexto nos detalhes ("Email inválido: teste@.com")
- Use decoradores para evitar repetição
- Registre erros críticos
- Valide entrada antes de processar

❌ **Evite:**
- Capturar `Exception` genérica
- Mensagens genéricas ("Erro")
- Expor detalhes técnicos ao usuário
- Perder informação de erro
- Ignorar falhas silenciosamente

---

## 9. Troubleshooting

### "AttributeError: 'NoneType' object"
Função com erro está retornando None
```python
# Sempre tratar antes
resultado = carregar_dados()
if resultado is None:
    st.error("Falha ao carregar")
else:
    processar(resultado)
```

### Logs não aparecem
Verifique:
1. Diretório `logs/` existe?
2. Permissões de escrita em disco?
3. Nível de log configurado corretamente?

### Retry não funciona
```python
# ✅ Correto - decorador na função
@com_retry()
def conectar():
    return supabase.connect()

# ❌ Errado - retry na chamada
resultado = com_retry()(conectar)
```

---

## 10. Integração com Components

O sistema se integra com `src/components.py`:
```python
from src.components import render_error_message

# Exibe erro com estilo profissional
render_error_message("Detalhes do erro aqui")
```

---

## 📄 Arquivo Criado

- `src/error_handler.py` (330+ linhas)
  - 10 exceções customizadas
  - 3 decoradores (com_tratamento_erro, com_validacao, com_retry)
  - 6 validadores
  - Sistema de logging automático

---

## 🚀 Próximos Passos

1. Importar em `app.py`
2. Substituir `try/except` genéricos por exceções específicas
3. Testar fluxos de erro
4. Revisar logs regularmente
