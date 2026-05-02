# DEPLOY_CHECKLIST.md

Antes de publicar:

- [ ] `python -m compileall .` passou.
- [ ] `pytest` passou ou falhas foram documentadas.
- [ ] `.env` nao foi commitado.
- [ ] `.env` esta no `.gitignore`.
- [ ] Secrets nao aparecem no codigo nem nos logs.
- [ ] Dashboard abre.
- [ ] Registro de ocorrencia salva.
- [ ] Historico carrega.
- [ ] Conselho abre e gera PDF.
- [ ] Prova Paulista importa planilha.
- [ ] Mapao importa planilha.
- [ ] Mapa da Sala abre separado do Mapao.
- [ ] PDF gera.
- [ ] Backup funciona.
- [ ] Rollback esta documentado.
- [ ] Tempo de inicializacao foi observado.
- [ ] Producao nao foi alterada sem validacao.
