# Python no Bolso

App web mobile-first para praticar lógica de Python em tempo picado. Exercícios gerados por IA e validados por execução real. Regras e comandos em [CLAUDE.md](CLAUDE.md); requisitos em [SPEC.md](SPEC.md).

## Rodando em outro computador
1. Instale Git, Node 22 e uv (Docker é opcional). `scripts/doctor` diz o que falta.
2. `git clone <repo>`, `git checkout ci/lint-testes-hooks` (ou a branch atual de trabalho).
3. Rode `scripts\setup.ps1` (Windows) ou `scripts/setup.sh` (Linux/macOS); ele cria o `.env` a partir do `.env.example`.
4. Preencha no `.env` as variáveis que o setup listar como vazias (chaves e banco; nunca commitar).
5. Para a sessão de testes: `scripts/worktree-testes`. Depois abra o Claude Code e rode `/retomar`.

## Variáveis de ambiente: `TRUST_PROXY`
O rate limit por IP (REQ-040) usa o IP da conexão. Atrás de proxy ou balanceador (Render, Fly), esse IP seria sempre o do proxy,
e todos os usuários dividiriam o mesmo limite. Nesse caso defina `TRUST_PROXY=1` para ler o IP real de `X-Forwarded-For`.
- **Padrão:** vazio (desligado). Use assim em desenvolvimento local.
- **Risco:** com `TRUST_PROXY=1` sem proxy confiável na frente, qualquer cliente forja `X-Forwarded-For` e escapa do limite por IP.
  Ligue só quando a API estiver realmente atrás de um proxy que sobrescreve esse header.
- Veja também [SECURITY.md](SECURITY.md) e o `.env.example`.
