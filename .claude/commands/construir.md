Leia CLAUDE.md primeiro.

Depois leia: SPEC.md, docs/arquitetura.md, docs/spec-gaps.md, docs/disputas.md,
docs/decisoes-contrato.md, docs/continuar.md e docs/reviews/.

## 1. PR de documentação (primeiro, se ainda não foi feito)
Confira em SPEC.md e docs/arquitetura.md se já foi feito. Se não, faça-o antes de qualquer código:
- aplicar no SPEC.md as mudanças listadas em docs/spec-gaps.md, incluindo níveis, temas, REQ-044,
  REQ-035, REQ-032, `codigo_corrigido`, a pasta do front e o REQ-045;
- registrar as decisões de docs/decisoes-contrato.md em docs/arquitetura.md.
Abra um PR só disso e pare para aprovação.

## 2. Implementação
Implemente em PRs pequenos, um grupo de requisitos por vez, até os testes correspondentes passarem.
- Não edite `**/tests/**`, `evals/**` nem `contrato.py`/`contrato.ts`.
- Teste que parecer errado: registre em docs/disputas.md e siga para outro grupo.
- Mudou comportamento: mude a SPEC.md no mesmo PR.
- Commits pequenos (Conventional Commits); uma funcionalidade por PR.

## 3. Fim de cada PR
Pare. Corpo do PR com no máximo 5 linhas explicando o porquê. Espere minha aprovação antes do próximo.

## 4. Ao terminar
Atualize docs/continuar.md (estado, pendências, próximo passo).
