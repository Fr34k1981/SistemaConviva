# 📋 CONFIGURAÇÃO DO SUPABASE

Para que o aplicativo funcione corretamente e grave as ocorrências no banco de dados, você precisa configurar as credenciais do Supabase.

## Passo 1: Criar projeto no Supabase
1. Acesse https://supabase.com
2. Crie uma conta (se ainda não tiver)
3. Clique em "New Project"
4. Preencha os dados do projeto

## Passo 2: Obter credenciais
Após criar o projeto:
1. Vá em **Settings** (ícone de engrenagem no menu lateral)
2. Clique em **API**
3. Copie as seguintes informações:
   - **Project URL** (ex: https://xxxxx.supabase.co)
   - **anon public key** (chave pública)

## Passo 3: Configurar no aplicativo

### Opção A: Rodando localmente
Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-publica-aqui
```

### Opção B: Streamlit Cloud
Se estiver usando o Streamlit Cloud:
1. Vá em **Settings** do seu app no Streamlit Cloud
2. Em **Secrets**, adicione:

```toml
SUPABASE_URL="https://seu-projeto.supabase.co"
SUPABASE_KEY="sua-chave-anon-publica-aqui"
```

## Passo 4: Criar tabelas no Supabase

Execute o seguinte SQL no Editor SQL do Supabase:

```sql
-- Tabela de alunos
CREATE TABLE alunos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    turma TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela de professores
CREATE TABLE professores (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela de ocorrências
CREATE TABLE ocorrencias (
    id SERIAL PRIMARY KEY,
    nome_aluno TEXT NOT NULL,
    nome_professor TEXT NOT NULL,
    infracoes TEXT[] NOT NULL,
    descricao TEXT NOT NULL,
    acoes_tomadas TEXT[],
    data_ocorrencia TIMESTAMP NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);

-- Inserir alguns dados de exemplo
INSERT INTO alunos (nome, turma) VALUES 
('João Silva', '9ºA'),
('Maria Santos', '8ºB'),
('Pedro Oliveira', '7ºC');

INSERT INTO professores (nome, email) VALUES 
('Ana Costa', 'ana@escola.com'),
('Carlos Pereira', 'carlos@escola.com');
```

## Verificação

Após configurar, reinicie o aplicativo:

```bash
streamlit run app.py
```

Tente registrar uma ocorrência. Se estiver configurado corretamente, você verá:
- ✅ Mensagem de sucesso ao salvar
- ✅ Dados aparecendo na tabela `ocorrencias` do Supabase

## Troubleshooting

Se ainda houver erro:
1. Verifique se as variáveis de ambiente estão carregadas corretamente
2. Confira se as tabelas foram criadas no Supabase
3. Verifique o console para mensagens de erro detalhadas
4. Certifique-se de que a chave API tem permissões de escrita
