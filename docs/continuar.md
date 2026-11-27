# Continuar

Estado curto. Atualize ao fim de cada PR ou sessão. Em outro computador: `scripts/setup` e depois `/retomar`.

## Estado atual (2026-11-26)
- Branch de trabalho: `ci/lint-testes-hooks` (ainda sem PR aberto na `main`).
- Testes escritos: 44 REQ mais o REQ-045 proposto. Já mesclados na branch atual (`tests/suite` é ancestral dela).
- Implementação em andamento por PRs; falhas de categoria A restantes são esperadas (ver `docs/reviews/estado-inicial-testes.md`).
- Decisões do contrato em `docs/decisoes-contrato.md` (vetos do usuário: D-06, D-12, D-14, D-17, D-23; D-11 e D-24 mantidas).
- PR 1 (docs, #4): SPEC, arquitetura, SECURITY.md e TRUST_PROXY. Aprovado.
- PR 2 (#5): `app.errors`, `app.db`, `app.models`, handler global e `/health`. Aprovado.
- PR 3 (#6): `GET /exercicios` e `device_id`. Aprovado.
- PR 4 (`feat/api-respostas`): `POST /respostas` (`app/correcao.py`, `app/routes/respostas.py`): validação por tipo, pares de
  indentação em `ordenar_linhas`, tentativa registrada, explicação armazenada da opção. Passam REQ-003, 007, 008, 010, 011, 032.
  Faltam: `GET /progresso` (REQ-009, 015, 016, 018, 035; PR 5) e o agente explicador (REQ-012, 013; depois). Hoje, sem explicação
  armazenada da opção, a resposta cai na explicação geral; o explicador será ligado quando existir.

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
