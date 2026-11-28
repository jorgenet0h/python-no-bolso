Leia CLAUDE.md primeiro.

Sessão revisora: somente leitura, exceto a escrita do relatório em docs/reviews/.
Compare a branch atual com `main` (ou com $ARGUMENTS, se informado).

Verifique, por área:
- aderência à SPEC.md, requisito por requisito;
- tratamento de erros (exceções de domínio, handler global, `{code, message}`, sem stack trace nem prompt);
- loop do agente: limite de passos, um log por passo, e a tool de salvar recusa o que não reproduz na execução;
- sandbox;
- prompt injection: nenhum texto livre chega a agente com tool de execução;
- segredos no histórico do git;
- CORS e rate limit (`TRUST_PROXY`);
- dependências inesperadas no package-lock.json;
- duplicação e funções longas.

Saída: `docs/reviews/AAAA-MM-DD-<branch>.md`. Cada item com severidade (bloqueante, importante,
sugestão), `arquivo:linha`, evidência e como reproduzir.

Não corrija nada. Não elogie por elogiar. Não invente defeito: se uma área está boa, diga o que
verificou para concluir isso.
