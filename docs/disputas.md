# Disputas de testes

CLAUDE.md, regra 2: nunca editar `**/tests/**` nem `evals/**` para fazer algo passar. Se um teste
parecer errado, registre aqui e siga para outra tarefa.

## DISP-001: `test_health.py` contradiz o REQ-044 (RESOLVIDA)

- **Teste:** `apps/api/tests/test_health.py::test_health_responde_ok` (anterior à sessão de testes).
- **O que ele exige:** `GET /health` devolve exatamente `{"status": "ok"}`.
- **O que a SPEC exige (REQ-044):** `GET /health` expõe o status da API **e do banco**.
- **Efeito:** implementar o REQ-044 quebra esse teste; manter o teste impede o REQ-044. Hoje ele passa
  (o scaffold ainda não tem banco).
- **Proposta original:** trocar a asserção para incluir o banco. Aplicada, ver decisão abaixo.
- **Decisão (resolvida):** a spec vence. Edição de `test_health.py` autorizada pela pessoa responsável
  no projeto. O teste foi substituído por dois casos (`test_req_044_health_banco_acessivel_responde_200_ok`
  e `test_req_044_health_banco_inacessivel_responde_503_degraded`) com o formato
  `{"status":"ok","db":"ok"}` (200) e `{"status":"degraded","db":"erro"}` (503). Redação proposta do
  REQ-044 em `docs/spec-gaps.md`, seção 4; a SPEC.md é alterada pela sessão 1.
