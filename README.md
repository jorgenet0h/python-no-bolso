# Python no Bolso

App web mobile-first para praticar lógica de Python em tempo picado. Exercícios gerados por IA e validados por execução real. Regras e comandos em [CLAUDE.md](CLAUDE.md); requisitos em [SPEC.md](SPEC.md).

## Rodando em outro computador
1. Instale Git, Node 22 e uv (Docker é opcional). `scripts/doctor` diz o que falta.
2. `git clone <repo>`, `git checkout ci/lint-testes-hooks` (ou a branch atual de trabalho).
3. Rode `scripts\setup.ps1` (Windows) ou `scripts/setup.sh` (Linux/macOS); ele cria o `.env` a partir do `.env.example`.
4. Preencha no `.env` as variáveis que o setup listar como vazias (chaves e banco; nunca commitar).
5. Para a sessão de testes: `scripts/worktree-testes`. Depois abra o Claude Code e rode `/retomar`.
