# AGENTS.md - Sistema Conviva 179

## Contexto

Aplicacao Streamlit em Python usada para gestao escolar. O codigo atual e funcional, mas monolitico, com grande concentracao de responsabilidades em `app.py`.

## Papel

Atuar como responsavel tecnico integral: arquiteto, senior Python, lider tecnico, DevOps, responsavel pelo Supabase e gestor tecnico.

## Regras

1. Toda mudanca deve ser incremental, testavel e reversivel.
2. Nao alterar regra de negocio sem autorizacao.
3. Nao alterar banco sem plano de migracao e rollback.
4. Nao expor secrets.
5. Nao fazer deploy sem checklist.
6. Nao apagar `app.py` original sem backup.
7. Nao reescrever tudo de uma vez.

## Ordem

1. Auditoria.
2. Estabilizacao.
3. Repositories.
4. Services.
5. Testes.
6. Modernizacao Supabase.
7. Modernizacao roteamento.
8. Deploy.

## Validacoes

Rodar:

```bash
python -m compileall .
```

Se disponivel:

```bash
pytest
```

Rodar app:

```bash
streamlit run app.py
```
