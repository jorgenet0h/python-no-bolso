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

## DISP-002: `gerar_lote` não deduplica exercícios idênticos (ABERTA)

- **Teste:** `apps/api/tests/test_req_agente.py::test_req_024_lote_respeita_minimo_de_estoque`.
- **O que ele exige:** o provedor falso devolve cinco vezes o mesmo exercício (`exercicio_exemplo()`) e
  `gerar_lote(..., minimo=2)` precisa terminar com pelo menos 2 exercícios validados de
  (`prever_saida`, `iniciante`, `variaveis`). Ou seja, o lote tem de aceitar conteúdo idêntico.
- **Problema:** com modelos reais, o mesmo enunciado e código podem voltar várias vezes (temperatura
  baixa, prompt fixo por enum). O estoque ficaria com repetidos e o usuário veria o mesmo exercício
  em sequência. Deduplicar antes de salvar quebra o teste acima; por isso o PR 9 **não** deduplica.
- **Proposta para a sessão 2 avaliar:**
  1. Calcular um hash do conteúdo canônico (`tipo`, `enunciado`, `codigo`, `opcoes`, `gabarito`, com
     espaços normalizados) **depois** da validação e guardar em coluna `hash_conteudo` (índice único
     parcial entre exercícios `validado`).
  2. Em duplicata, não salvar: a execução fica `rejeitado` com motivo `duplicado` e conta contra o
     limite de `minimo × 3` tentativas (D-21).
  3. Reescrever o teste do REQ-024 para que o provedor falso devolva conteúdos distintos, e acrescentar
     um teste de duplicata rejeitada. Isso muda um teste, então a decisão é da sessão 2.
- **Enquanto isso:** a implementação segue o teste atual (sem deduplicação). Nenhum teste foi editado.
