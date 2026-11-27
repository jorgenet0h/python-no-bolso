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
- PR 4 (#7): `POST /respostas`. Aprovado.
- PR 5 (#8): `GET /progresso`. Aprovado.
- PR 6 (#9): rate limit e CORS. Aprovado.
- PR 7 (#10): sandbox (REQ-027), confirmado no CI Linux. Aprovado.
- PR 8 (`feat/api-validador`): `app/validador.py` (REQ-025, 026, 030): schema (com `jsonschema`, cópia do
  `evals/exercicio.schema.json`; se um mudar, mudar o outro), execução independente por tipo, unicidade de ordem+indentação em
  `ordenar_linhas`, `achar_bug` com bug divergente da correção. Conferido com o sandbox real nos 4 tipos.
  REQ-025, 028 e 029 ainda dependem do loop (PR 9).
  Faltam: loop/CLI (REQ-019 a 024, 028, 029), explicador (REQ-012, 013, 037, 045, 038), Alembic, front.

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
