Leia CLAUDE.md primeiro.

Sessão de testes. Leia SOMENTE: CLAUDE.md, SPEC.md, docs/arquitetura.md,
docs/decisoes-contrato.md e docs/requisitos-disciplina.md.
Não leia nem altere `apps/api/app` nem `apps/web/src` (o teste nasce da spec, não da implementação).

Requisitos desta sessão: $ARGUMENTS

1. Escreva testes a partir da spec para esses requisitos, com o id do REQ no nome
   (ex.: `test_req_012_...`), antes de a implementação existir.
2. Quando o requisito tocar sandbox, payloads ou prompt injection, inclua casos adversariais.
3. Atualize docs/rastreabilidade.md.
4. Ambiguidade na spec vai para docs/spec-gaps.md. Não edite o SPEC.md.
5. Rode a suíte e classifique cada falha em:
   (A) requisito não implementado, ou
   (B) erro do próprio teste. Corrija os B.
6. Termine com um resumo de 5 linhas.
