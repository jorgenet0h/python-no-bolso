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
- PR 8 (#11): validador. Aprovado.
- PR 9 (`feat/api-loop-agente`): `app/agent/loop.py` (REQ-019 a 023, 025, 028, 029), `app/agent/provedores.py` (Gemini e Groq
  reais, ainda não exercitados com chave), `app/config.py` (`carregar_provedor`) e `app/cli.py` (`gerar_lote`; comando
  `python -m app.cli gerar ...`). `gerar_lote` não deduplica exercícios idênticos. Falta `semear-e2e` na CLI (junto do front).
  PR 10 (`feat/cli-listar-modelos`): `python -m app.cli modelos` lista modelos do provedor (chave só no header, erro só com tipo e
  HTTP); `GeminiProvider` remove o prefixo `models/` do `MODEL_NAME`; motivo de falha do provedor inclui o status HTTP.
  Geração real validada (3/3 aprovados) com `gemini-3.1-flash-lite`. `gemini-2.5-flash` e `-flash-lite` dão 404 com a chave atual;
  `gemini-flash-latest` deu 503. O `.env` do usuário deve usar um modelo que responda 200.
  Faltam: explicador (REQ-012, 013, 037, 045, 038), Alembic, front, evals com modelos reais, deploy.

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
