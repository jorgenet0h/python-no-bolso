# Progresso

Estado da suíte rodada de verdade em 2026-11-27, na branch `feat/api-loop-agente` (PR #12, topo da
cadeia de PRs #3 a #12, ainda não mesclada na `main`). `docs/continuar.md` segue sendo o estado curto
da sessão; esta página guarda os números.

## Suíte

| Camada | Resultado | Observação |
|---|---|---|
| API (pytest) | 166 passam, 25 falham, 2 pulados | os 2 pulados (memória e fork bomb) passam no CI Linux |
| Evals (pytest) | 50 passam | `pytest evals/tests` |
| Web (Vitest) | 0 passam, 8 falham | `apps/web/lib` não existe (REQ-014, 015, 017) |
| e2e (Playwright) | não rodado | exige API, banco semeado e front de pé |

## As 25 falhas da API (todas do agente explicador, que ainda não existe)

| REQ | Falhas |
|---|---|
| REQ-012 | 1 |
| REQ-013 | 1 |
| REQ-037 | 1 |
| REQ-038 | 8 (7 com texto hostil na resposta do usuário, 1 com instrução no enunciado armazenado) |
| REQ-045 | 14 |

## PRs

| PR | O que entrega | Status |
|---|---|---|
| #1 | scaffold | mesclado na `main` |
| #2 | SPEC e arquitetura | mesclado em `chore/scaffold-monorepo` (não está na `main`) |
| #3 | lint, testes, hooks e CI | aberto |
| #4 | docs: SPEC, arquitetura, SECURITY.md | aberto |
| #5 | erros tipados, banco, `/health` | aberto |
| #6 | `GET /exercicios`, `device_id` | aberto |
| #7 | `POST /respostas` | aberto |
| #8 | `GET /progresso` | aberto |
| #9 | rate limit e CORS | aberto |
| #10 | sandbox | aberto |
| #11 | validador | aberto |
| #12 | loop do agente, provedores, config, CLI | aberto |

## Pendências para os testes passarem
1. Explicador e `POST /explicacoes` (REQ-012, 013, 037, 038, 045).
2. Front: `apps/web/lib` e as telas (REQ-005, 014, 015, 017) e `semear-e2e` na CLI.

## Pendências para a disciplina
Alembic, deploy (Postgres, API, front), evals com 2 modelos reais, README, vídeo de pitch.

## Disputas e lacunas abertas
- DISP-002: `gerar_lote` não deduplica (docs/disputas.md).
- Rejeição de exercício com tipo, nível ou tema diferente do pedido, sem teste (docs/spec-gaps.md, seção 6).
