# 🚀 Quick Reference - Tratamento de Erros

Referência rápida para usar o sistema de tratamento de erros.

---

## 1️⃣ Lançar Erro

### Conexão DB
```python
raise ErroConexaoDB("Detalhe adicional")
```

### Validação
```python
raise ErroValidacao("campo", "Mensagem de erro")
```

### Carregamento de dados
```python
raise ErroCarregamentoDados("tipo_dado", "detalhe opcional")
```

### Operação DB
```python
raise ErroOperacaoDB("ação", "detalhe opcional")
```

### Arquivo
```python
raise ErroArquivo("operação", "nome_arquivo", "detalhe")
```

### Autenticação
```python
raise ErroAutenticacao("recurso")
raise ErroValidacaoSenha()
```

### Duplicata
```python
raise ErroDuplicado("tipo", "valor")
```

### Não encontrado
```python
raise ErroNaoEncontrado("tipo", "identificador")
```

### Permissão
```python
raise ErroPermissao("ação")
```

---

## 2️⃣ Validar

### Nome (3-100 caracteres)
```python
valido, msg = Validadores.validar_nome("João Silva")
if not valido:
    raise ErroValidacao("nome", msg)
```

### Email
```python
valido, msg = Validadores.validar_email("test@example.com")
if not valido:
    raise ErroValidacao("email", msg)
```

### Data (DD/MM/YYYY)
```python
valido, msg = Validadores.validar_data("25/01/2024")
if not valido:
    raise ErroValidacao("data", msg)
```

### Não vazio
```python
valido, msg = Validadores.validar_nao_vazio(valor, "Nome do campo")
if not valido:
    raise ErroValidacao("campo", msg)
```

### Lista não vazia
```python
valido, msg = Validadores.validar_lista_nao_vazia(lista, "itens")
if not valido:
    raise ErroValidacao("lista", msg)
```

### Número em intervalo
```python
valido, msg = Validadores.validar_numero(idade, minimo=5, maximo=18)
if not valido:
    raise ErroValidacao("idade", msg)
```

---

## 3️⃣ Decoradores

### Tratamento automático de erro
```python
@com_tratamento_erro
def minha_funcao():
    raise ErroValidacao("campo", "Erro")
    # Erro é capturado, exibido e registrado automaticamente
```

### Retry automático
```python
@com_retry(tentativas=3, intervalo=0.5)
def conectar_supabase():
    return supabase.connect()
```

### Validação automática
```python
@com_validacao(Validadores.validar_nao_vazio)
def processar_nome(nome):
    return nome.upper()
```

### Combinado
```python
@com_tratamento_erro
@com_retry(tentativas=2)
def carregar_dados():
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

---

## 4️⃣ Padrão Completo

```python
@com_tratamento_erro
def salvar_dados(nome, email, data):
    # 1. Validar cada campo
    valido, msg = Validadores.validar_nome(nome)
    if not valido:
        raise ErroValidacao("nome", msg)
    
    valido, msg = Validadores.validar_email(email)
    if not valido:
        raise ErroValidacao("email", msg)
    
    valido, msg = Validadores.validar_data(data)
    if not valido:
        raise ErroValidacao("data", msg)
    
    # 2. Operação que pode falhar
    try:
        response = supabase.table("tabela").insert({
            "nome": nome,
            "email": email,
            "data": data
        }).execute()
        return response
    
    except Exception as e:
        raise ErroOperacaoDB("salvar dados", str(e))
```

---

## 5️⃣ Ver Logs

### Linux/Mac
```bash
tail -f logs/app.log
```

### Windows PowerShell
```powershell
Get-Content logs/app.log -Wait
```

### Ver últimas 20 linhas
```bash
tail -20 logs/app.log
```

### Procurar por erro específico
```bash
grep "VALIDACAO_FALHOU" logs/app.log
```

---

## 6️⃣ Mensagens Comuns

| Erro | Código |
|------|--------|
| Banco de dados | CONEXAO_DB_FALHOU |
| Dados inválidos | VALIDACAO_FALHOU |
| Carregar falhou | CARREGAMENTO_DADOS_FALHOU |
| Salvar falhou | OPERACAO_DB_FALHOU |
| Arquivo | ARQUIVO_ERRO |
| Acesso negado | AUTENTICACAO_FALHOU |
| Senha errada | SENHA_INCORRETA |
| Já existe | JA_EXISTE |
| Não existe | NAO_ENCONTRADO |
| Sem permissão | PERMISSAO_NEGADA |

---

## 7️⃣ Exemplos Reais

### Salvar Aluno
```python
@com_tratamento_erro
def salvar_aluno(nome, email, ra, turma):
    # Validar
    valido, msg = Validadores.validar_nome(nome)
    if not valido:
        raise ErroValidacao("nome", msg)
    
    valido, msg = Validadores.validar_email(email)
    if not valido:
        raise ErroValidacao("email", msg)
    
    # Salvar
    aluno = {
        "nome": nome,
        "email": email,
        "ra": ra,
        "turma": turma
    }
    return _supabase_mutation("POST", "alunos", aluno, "salvar aluno")
```

### Carregar com Retry
```python
@com_tratamento_erro
@com_retry(tentativas=3, intervalo=1.0)
def carregar_alunos_turma(turma):
    return _supabase_get_dataframe(
        f"alunos?turma=eq.{turma}&select=*",
        "carregar alunos da turma"
    )
```

### Registrar Ocorrência
```python
@com_tratamento_erro
def registrar_ocorrencia(aluno, data, gravidade, descricao):
    # Validações
    valido, msg = Validadores.validar_data(data)
    if not valido:
        raise ErroValidacao("data", msg)
    
    if gravidade not in ["Leve", "Média", "Grave", "Gravíssima"]:
        raise ErroValidacao("gravidade", "Gravidade inválida")
    
    # Salvar
    ocorrencia = {
        "aluno_nome": aluno,
        "data": data,
        "gravidade": gravidade,
        "descricao": descricao
    }
    return salvar_ocorrencia(ocorrencia)
```

---

## 8️⃣ Troubleshooting

### Erro não aparece
**Problema:** Função retorna None mas nenhuma mensagem de erro
**Solução:** Adicionar @com_tratamento_erro decorator

### Erro se repete
**Problema:** Mesmo erro ocorre várias vezes
**Solução:** Ver logs/app.log e identificar a causa raiz

### Decorador não funciona
**Problema:** Erro não é tratado
**Solução:** Verifique se os imports estão corretos

### Mensagem em inglês
**Problema:** Erro mostra em inglês
**Solução:** Você está lançando exceção do Python, use as do error_handler

---

## 9️⃣ Importações Rápidas

```python
# Tudo de uma vez
from src.error_handler import (
    com_tratamento_erro, com_retry, com_validacao,
    ErroConexaoDB, ErroValidacao, ErroCarregamentoDados,
    ErroOperacaoDB, ErroArquivo, ErroAutenticacao,
    ErroDuplicado, ErroNaoEncontrado, ErroPermissao,
    Validadores, logger
)
```

---

## 🔟 Checklist de Função Bem-Escrita

- [ ] Importa error_handler
- [ ] Tem @com_tratamento_erro
- [ ] Valida todos os inputs
- [ ] Lança ErroValidacao se inválido
- [ ] Trata exceções específicas
- [ ] Lança ErroOperacaoDB se operação falha
- [ ] Tem @com_retry se rede instável
- [ ] Retorna resultado ou False
- [ ] Sem st.error() direto (usa decorador)
- [ ] Sem try/except genérico

---

## 📞 Ajuda

| Pergunta | Resposta |
|----------|----------|
| Qual erro usar? | ERROR_HANDLER_GUIDE.md |
| Qual mensagem mostra? | ERRO_MENSAGENS.md |
| Como integrar? | INTEGRACAO_TRATAMENTO_ERROS.md |
| Exemplos de código? | examples_error_handler.py |
| Visão geral? | RESUMO_TRATAMENTO_ERROS.md |

---

## ⚡ One-Liner Reference

```python
# Importar tudo
from src.error_handler import *

# Decorar função
@com_tratamento_erro
@com_retry()
def funcao(): pass

# Validar
valido, msg = Validadores.validar_nome(x) or raise ErroValidacao("name", msg)

# Lançar
raise ErroValidacao("campo", "mensagem")

# Ver logs
# cat logs/app.log

# Resultado: Erros específicos, claros e rastreáveis ✅
```

---

**Mais informações? Veja a documentação completa nos arquivos .md**
