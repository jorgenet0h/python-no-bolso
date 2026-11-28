Leia CLAUDE.md primeiro.

Leia o último arquivo de docs/reviews/ (o mais recente por data no nome) e docs/disputas.md.
Rode os testes (`cd apps/api && .venv/Scripts/python -m pytest` e os do web) para ter a linha de base.

Trate primeiro os itens bloqueantes, depois importantes, depois sugestões. Para cada item:
1. reproduza o problema;
2. corrija;
3. faça um commit que cite o item (ex.: `fix(api): ... (review 2026-12-01 item B1)`).

Não edite `**/tests/**` nem `evals/**` para fazer algo passar. Se discordar de um item, explique em
docs/reviews/respostas.md (item, motivo, evidência) em vez de ignorar. Ao fim, atualize docs/continuar.md.
