# 📋 Catálogo de Mensagens de Erro

Referência completa de mensagens de erro do sistema com exemplos de quando ocorrem.

---

## 1️⃣ Erros de Conexão

### ErroConexaoDB
**Quando ocorre:** SUPABASE_URL ou SUPABASE_KEY não configuradas

**Mensagem:**
```
❌ Erro de conexão com o banco de dados
Não foi possível conectar ao Supabase. Verifique sua conexão.

Código: CONEXAO_DB_FALHOU
```

**Exemplos de contexto:**
- Ao iniciar app (sem variáveis de ambiente)
- Ao carregar dados de alunos
- Ao salvar ocorrência

**Solução do usuário:**
1. Verifique o arquivo `.env`
2. Confirme que SUPABASE_URL e SUPABASE_KEY estão definidas
3. Reinicie o aplicativo

---

## 2️⃣ Erros de Validação

### ErroValidacao - Nome
**Quando ocorre:** Nome vazio, muito curto (<3 chars) ou muito longo (>100 chars)

**Exemplos:**

```
❌ Erro de validação em 'nome'
Nome do aluno não pode estar vazio

Código: VALIDACAO_FALHOU
```

```
❌ Erro de validação em 'nome'
Nome do aluno deve ter pelo menos 3 caracteres

Código: VALIDACAO_FALHOU
```

```
❌ Erro de validação em 'nome'
Nome do aluno deve ter no máximo 100 caracteres

Código: VALIDACAO_FALHOU
```

### ErroValidacao - Email
**Quando ocorre:** Formato de email inválido

**Mensagem:**
```
❌ Erro de validação em 'email'
Email inválido

Código: VALIDACAO_FALHOU
```

**Exemplos de entrada inválida:**
- `teste@` (sem domínio)
- `teste@.com` (sem nome de domínio)
- `teste@domínio` (sem extensão)
- `@dominio.com` (sem usuário)

### ErroValidacao - Data
**Quando ocorre:** Data em formato incorreto

**Mensagem:**
```
❌ Erro de validação em 'data'
Data inválida. Use formato DD/MM/YYYY

Código: VALIDACAO_FALHOU
```

**Exemplos de entrada inválida:**
- `25-01-2024` (formato com hífen)
- `2024-01-25` (formato ISO)
- `25/13/2024` (mês inválido)
- `32/01/2024` (dia inválido)

### ErroValidacao - Campo vazio
**Quando ocorre:** Campo obrigatório não preenchido

**Mensagens genéricas:**
```
❌ Erro de validação em 'turma'
Turma é obrigatório

Código: VALIDACAO_FALHOU
```

```
❌ Erro de validação em 'gravidade'
Selecione pelo menos uma gravidade

Código: VALIDACAO_FALHOU
```

### ErroValidacao - Lista vazia
**Quando ocorre:** Nenhum item selecionado de uma lista obrigatória

**Mensagem:**
```
❌ Erro de validação em 'turmas'
Selecione pelo menos um turmas

Código: VALIDACAO_FALHOU
```

### ErroValidacao - Número fora do intervalo
**Quando ocorre:** Número menor do que o mínimo ou maior do que o máximo

**Mensagens:**
```
❌ Erro de validação em 'idade'
Valor deve ser >= 5

Código: VALIDACAO_FALHOU
```

```
❌ Erro de validação em 'idade'
Valor deve ser <= 18

Código: VALIDACAO_FALHOU
```

---

## 3️⃣ Erros de Carregamento

### ErroCarregamentoDados - Alunos
**Quando ocorre:** Falha ao carregar lista de alunos

**Mensagem:**
```
❌ Erro ao carregar alunos
Não foi possível carregar alunos. Tente novamente.

Código: CARREGAMENTO_DADOS_FALHOU
```

**Cenários:**
- Conexão perdida durante carregamento
- Supabase fora do ar
- Timeout de rede

### ErroCarregamentoDados - Professores
**Quando ocorre:** Falha ao carregar lista de professores

**Mensagem:**
```
❌ Erro ao carregar professores
Não foi possível carregar professores. Tente novamente.

Código: CARREGAMENTO_DADOS_FALHOU
```

### ErroCarregamentoDados - Turmas
**Quando ocorre:** Falha ao carregar turmas

**Mensagem:**
```
❌ Erro ao carregar turmas
Nenhuma turma cadastrada

Código: CARREGAMENTO_DADOS_FALHOU
```

### ErroCarregamentoDados - Ocorrências
**Quando ocorre:** Falha ao carregar ocorrências

**Mensagem:**
```
❌ Erro ao carregar ocorrências
Não foi possível carregar ocorrências. Tente novamente.

Código: CARREGAMENTO_DADOS_FALHOU
```

### ErroCarregamentoDados - Eletivas
**Quando ocorre:** Falha ao carregar eletivas

**Mensagem:**
```
❌ Erro ao carregar eletivas
A tabela `eletivas` não existe no Supabase. Crie a tabela antes de usar.

Código: CARREGAMENTO_DADOS_FALHOU
```

---

## 4️⃣ Erros de Operação

### ErroOperacaoDB - Salvar Aluno
**Quando ocorre:** Falha ao inserir novo aluno

**Mensagem:**
```
❌ Erro ao salvar aluno
Não foi possível salvar aluno. Tente novamente.

Código: OPERACAO_DB_FALHOU
```

**Causas possíveis:**
- Ra (ID) já existe
- Dados malformados
- Limite de armazenamento atingido

### ErroOperacaoDB - Salvar Ocorrência
**Quando ocorre:** Falha ao registrar ocorrência

**Mensagem:**
```
❌ Erro ao salvar ocorrência
Não foi possível salvar ocorrência. Tente novamente.

Código: OPERACAO_DB_FALHOU
```

### ErroOperacaoDB - Atualizar Professor
**Quando ocorre:** Falha ao atualizar dados de professor

**Mensagem:**
```
❌ Erro ao atualizar professor
Não foi possível atualizar professor. Tente novamente.

Código: OPERACAO_DB_FALHOU
```

### ErroOperacaoDB - Excluir Turma
**Quando ocorre:** Falha ao deletar alunos de uma turma

**Mensagem:**
```
❌ Erro ao excluir turma
Não foi possível excluir turma. Tente novamente.

Código: OPERACAO_DB_FALHOU
```

### ErroOperacaoDB - Salvar Eletivas
**Quando ocorre:** Falha ao sincronizar eletivas no Supabase

**Mensagem:**
```
❌ Erro ao salvar eletivas no Supabase
Não foi possível sincronizar eletivas. Tente novamente.

Código: OPERACAO_DB_FALHOU
```

---

## 5️⃣ Erros de Arquivo

### ErroArquivo - Abrir
**Quando ocorre:** Arquivo não existe ou sem permissão de leitura

**Mensagens:**

```
❌ Erro ao abrir arquivo 'data/turmas/1º A.csv'
Arquivo não existe

Código: ARQUIVO_ERRO
```

```
❌ Erro ao abrir arquivo 'backup.zip'
Verifique se o arquivo existe e tem permissões de leitura.

Código: ARQUIVO_ERRO
```

### ErroArquivo - Salvar
**Quando ocorre:** Sem espaço em disco ou sem permissão de escrita

**Mensagem:**
```
❌ Erro ao salvar arquivo 'backup_2024_01_15.zip'
Sem espaço em disco

Código: ARQUIVO_ERRO
```

### ErroArquivo - Processar
**Quando ocorre:** Erro ao ler/processar conteúdo do arquivo

**Mensagem:**
```
❌ Erro ao processar arquivo 'alunos.csv'
Encoding inválido (não é UTF-8)

Código: ARQUIVO_ERRO
```

---

## 6️⃣ Erros de Duplicação

### ErroDuplicado - Aluno
**Quando ocorre:** Aluno já foi cadastrado

**Mensagem:**
```
❌ Aluno já existe
'João Silva' já foi cadastrado no sistema.

Código: JA_EXISTE
```

### ErroDuplicado - Email
**Quando ocorre:** Email já está em uso

**Mensagem:**
```
❌ Email já existe
'joao@example.com' já foi cadastrado no sistema.

Código: JA_EXISTE
```

### ErroDuplicado - Turma
**Quando ocorre:** Turma com mesmo nome já existe

**Mensagem:**
```
❌ Turma já existe
'1º A' já foi cadastrada no sistema.

Código: JA_EXISTE
```

---

## 7️⃣ Erros de Não Encontrado

### ErroNaoEncontrado - Aluno
**Quando ocorre:** Aluno não existe no sistema

**Mensagem:**
```
❌ Aluno não encontrado
Não foi possível encontrar Aluno com identificador 'João Silva'.

Código: NAO_ENCONTRADO
```

### ErroNaoEncontrado - Turma
**Quando ocorre:** Turma não existe

**Mensagem:**
```
❌ Turma não encontrado
Não foi possível encontrar Turma com identificador '1º A'.

Código: NAO_ENCONTRADO
```

### ErroNaoEncontrado - Professor
**Quando ocorre:** Professor não existe

**Mensagem:**
```
❌ Professor não encontrado
Não foi possível encontrar Professor com identificador 'Maria'.

Código: NAO_ENCONTRADO
```

---

## 8️⃣ Erros de Autenticação/Permissão

### ErroAutenticacao
**Quando ocorre:** Usuário não autenticado

**Mensagem:**
```
❌ Acesso negado ao recurso
Você não tem permissão para acessar este recurso.

Código: AUTENTICACAO_FALHOU
```

### ErroValidacaoSenha
**Quando ocorre:** Senha incorreta

**Mensagem:**
```
❌ Senha incorreta
A senha digitada está incorreta. Tente novamente.

Código: SENHA_INCORRETA
```

### ErroPermissao
**Quando ocorre:** Usuário sem permissão para ação

**Mensagem:**
```
❌ Permissão negada
Você não tem permissão para deletar ocorrências de outros usuários.

Código: PERMISSAO_NEGADA
```

---

## 🔄 Erros de Retry

**Quando ocorre:** Após falha em todas as tentativas

**Mensagem adicional:**
```
(Após 3 tentativas)
```

**Exemplo:**
```
❌ Erro ao carregar alunos
Timeout de conexão

Código: CARREGAMENTO_DADOS_FALHOU
(Após 3 tentativas)
```

---

## 📊 Tabela de Referência Rápida

| Código | Exceção | Causa |
|--------|---------|-------|
| CONEXAO_DB_FALHOU | ErroConexaoDB | Supabase não configurado |
| VALIDACAO_FALHOU | ErroValidacao | Dados inválidos |
| CARREGAMENTO_DADOS_FALHOU | ErroCarregamentoDados | Falha ao ler dados |
| OPERACAO_DB_FALHOU | ErroOperacaoDB | Falha ao salvar/atualizar |
| ARQUIVO_ERRO | ErroArquivo | Problema com arquivo |
| AUTENTICACAO_FALHOU | ErroAutenticacao | Acesso não autorizado |
| SENHA_INCORRETA | ErroValidacaoSenha | Senha errada |
| JA_EXISTE | ErroDuplicado | Registro duplicado |
| NAO_ENCONTRADO | ErroNaoEncontrado | Registro não existe |
| PERMISSAO_NEGADA | ErroPermissao | Sem permissão |

---

## 🛠️ Como Aparece no Streamlit

Cada erro aparece com estilo visual profissional:

```
┌─────────────────────────────────────────┐
│ ❌ Erro de validação em 'email'         │
├─────────────────────────────────────────┤
│ Email inválido                          │
│                                         │
│ Código: VALIDACAO_FALHOU                │
└─────────────────────────────────────────┘
```

---

## 📝 Notas para Desenvolvedores

1. **Sempre forneça contexto:** Mensagem + detalhe + código
2. **Seja específico:** "Campo 'email'" é melhor que "Campo"
3. **Oriente o usuário:** Como resolver o problema
4. **Use códigos:** Para debugging e logging
5. **Tradução:** Todas as mensagens em português

---

## 🔗 Integração com Components

Mensagens de erro integram com `src/components.py`:

```python
from src.components import render_error_message

render_error_message(
    "Email inválido\n\nCódigo: VALIDACAO_FALHOU"
)
```

Resultado: Erro exibido com estilo profissional e cor vermelha.
