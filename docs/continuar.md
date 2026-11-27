# Continuar

Estado curto. Atualize ao fim de cada PR ou sessão. Em outro computador: `scripts/setup` e depois `/retomar`.

## Estado atual (2026-11-26)
- Branch de trabalho: `ci/lint-testes-hooks` (ainda sem PR aberto na `main`).
- Testes escritos: 44 REQ mais o REQ-045 proposto. Já mesclados na branch atual (`tests/suite` é ancestral dela).
- Implementação em andamento por PRs; falhas de categoria A restantes são esperadas (ver `docs/reviews/estado-inicial-testes.md`).
- Decisões do contrato em `docs/decisoes-contrato.md` (vetos do usuário: D-06, D-12, D-14, D-17, D-23; D-11 e D-24 mantidas).
- PR 1 (docs, #4): SPEC, arquitetura, SECURITY.md e TRUST_PROXY. Aprovado.
- PR 2 (#5): `app.errors`, `app.db`, `app.models`, handler global e `/health`. Aprovado.
- PR 3 (`feat/api-exercicios-device`): `GET /exercicios` (filtros por enum, priorização, sem gabarito) e dependência `device_id`
  (`app/deps.py`). Passam REQ-001, 002, 004 e 006. REQ-003, 018 e 032/035 fecham com `POST /respostas` e `GET /progresso`.
  Próximo: `POST /respostas` (REQ-007 a 011) e `GET /progresso` (REQ-015, 016, 018).

## Pendências
- Testes de memória e fork bomb rodando no CI em Linux (D-23): confirmar que não ficam `skipped`.
- Conferir o `package-lock.json` (dependências inesperadas).
- Abrir os PRs na `main`; mínimo de 2 PRs por pessoa.
- Ambiente local: o venv da API está em Python 3.13; o projeto e o CI usam 3.12 (apagar `apps/api/.venv` e rodar `scripts/setup`).

## Próximos passos
1. `/construir` (começa pelo PR de documentação do SPEC).
2. `/revisar` a cada 2 ou 3 PRs; depois `/corrigir`.
3. Sessão de testes separada: `scripts/worktree-testes` e `/testar <requisitos>` na pasta `../python-no-bolso-testes`.

## Datas
- 12/12: congelar funcionalidades.
- 17/12: entrega e apresentação.
