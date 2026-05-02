# RELATORIO_AUDITORIA.md - Sistema Conviva 179

Data: 2026-05-02
Branch: `refatoracao-v2`

## Classificacao De Risco

- Hotfix visual e importacao Prova Paulista/Mapao: MEDIO RISCO. Impacta interface e leitura de planilhas, sem alterar schema do banco. Rollback: restaurar `app.py` pelo backup em `data/backups/app_refatoracao_v2_*.py` ou pelo controle de versao.
- Criacao de documentacao e estrutura modular: BAIXO RISCO. Apenas adiciona arquivos e pastas.
- Reducao de `app.py` com ponte `legacy_app.py`: MEDIO RISCO. Preserva o corpo legado e muda apenas o ponto de entrada. Rollback: restaurar `app.py` pelo backup ou copiar `legacy_app.py` de volta.
- Alteracoes de schema Supabase: IRREVERSIVEL sem plano. Nao executado.

## Visao Geral

O sistema e uma aplicacao Streamlit que ainda mantem o corpo principal monolitico em `legacy_app.py`. O novo `app.py` atua como ponto de entrada curto e executa o legado. A migracao real de paginas e servicos deve continuar de forma incremental, sem alterar regra de negocio.

## Mapa De Paginas

Menu identificado:

- Dashboard
- Registrar Ocorrencia
- Relatorio dos Estudantes
- Conselho
- Prova Paulista
- Historico de Ocorrencias
- Comunicado aos Pais
- Lista de Alunos
- Importar Alunos
- Gerenciar Turmas
- Cadastrar Professores
- Cadastrar Assinaturas
- Eletiva
- Tutoria
- Graficos e Indicadores
- Imprimir PDF
- Mapao
- Mapa da Sala
- Agendamento de Espacos
- Portal do Responsavel
- Backups

## Mapa De Dados

Tabelas Supabase usadas ou referenciadas:

- `alunos`
- `professores`
- `responsaveis`
- `ocorrencias`
- `turmas_config`
- `relatorios_estudantes`
- `agendamentos`
- `eletivas`
- `tutoria`
- `cadernos_tutoria`
- `usuarios`
- `perfil_tutorado`
- `rendimento_bimestral`
- `tutoria_individual`
- `tutoria_coletiva`
- `prova_paulista`, `prova_paulista_dados`, `resultados_prova_paulista` como alternativas de leitura

Arquivos locais relevantes:

- `data/alunos_cadastrados.csv`
- `data/ocorrencias.csv`
- `data/turmas/*.xlsx`
- `data/prova_paulista_online.json`
- `data/mapao_online.json`
- `data/backups/*`
- arquivos de downloads enviados pelo usuario, como `RESULTADOS DA TURMA*.xlsx` e Mapao

## Variaveis E Secrets

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SENHA_EXCLUSAO`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Observacao: secrets nao devem ser escritos em documentacao, logs ou commits.

## Cache E Estado

Uso de `st.cache_data` em carregamento de Supabase, configuracoes, relatorios e agendamentos. Uso extenso de `st.session_state` para pagina atual, eletivas, tutoria, backup, IA, formularios e editores.

Risco: estado disperso dificulta teste, rollback visual e previsibilidade em `st.rerun()`.

## PDF

Geracao de PDF com ReportLab para:

- ocorrencias
- comunicados
- relatorios de estudantes
- Conselho
- Eletiva
- Tutoria
- Mapa da Sala

Risco: funcoes grandes misturadas com dados e UI. Recomenda-se migrar para `services/pdf_service.py` em etapas.

## IA/Gemini

IA usa Gemini via `requests` e `GEMINI_API_KEY`. Prompts e aplicacao de texto ficam dentro do fluxo de UI.

Risco: lentidao, falha de rede e acoplamento com campos de tela. Recomenda-se migrar para `services/ia_service.py` sem alterar prompts.

## Pontos Criticos

- `legacy_app.py` concentra responsabilidades demais.
- CSS global sobrescreve componentes, como ocorreu com cards do Dashboard.
- Leitura `.xlsx` depende de `openpyxl`; foi adicionado fallback XML para Prova Paulista/Mapao/Conselho.
- `Mapao` e `Mapa da Sala` estavam compartilhando rota; foram separados.
- Dashboard tinha Top 10 da Prova Paulista condicionado a haver ocorrencias; foi separado.
- Sidebar recolhida tem risco visual por CSS fixo de largura.
- Supabase esta espalhado entre helper central e chamadas diretas.
- Funcionalidades pedagógicas dependem de nomes de colunas variados em planilhas.

## Plano Recomendado

1. Manter hotfix atual e validar telas principais.
2. Migrar CSS global para `components/layout.py` ou arquivo CSS, sem mudar visual.
3. Mover configuracoes para `config/settings.py` e caminhos para `config/paths.py`.
4. Centralizar inicializacao de `st.session_state` em `core/state.py`.
5. Isolar cliente Supabase em `db/supabase_client.py`, mantendo `requests`.
6. Migrar repositorios de alunos e ocorrencias.
7. Migrar services de PDF, IA e backup.
8. Migrar paginas uma por vez, reduzindo `legacy_app.py` ate que o `app.py` possa chamar apenas componentes e paginas novas.
