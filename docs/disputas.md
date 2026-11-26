# Disputas de testes

CLAUDE.md, regra 2: nunca editar `**/tests/**` nem `evals/**` para fazer algo passar. Se um teste
parecer errado, registre aqui e siga para outra tarefa.

## DISP-001: `test_health.py` contradiz o REQ-044

- **Teste:** `apps/api/tests/test_health.py::test_health_responde_ok` (anterior à sessão de testes).
- **O que ele exige:** `GET /health` devolve exatamente `{"status": "ok"}`.
- **O que a SPEC exige (REQ-044):** `GET /health` expõe o status da API **e do banco**.
- **Efeito:** implementar o REQ-044 quebra esse teste; manter o teste impede o REQ-044. Hoje ele passa
  (o scaffold ainda não tem banco).
- **Proposta:** quando o banco entrar, trocar a asserção por `body["status"] == "ok"` e `"db" in body`,
  ou aceitar que `test_req_044_health_expoe_status_da_api_e_do_banco` o substitua. Não foi editado.
- **Decisão:** pendente (sua).
