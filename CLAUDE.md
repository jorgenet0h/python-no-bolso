# Python no Bolso

App web mobile-first para praticar lógica de Python. Exercícios são gerados
por IA e só entram no banco depois de validados por execução real.

Pessoa e dor: dev júnior em busca de vaga que estuda em tempo picado
(fila, ônibus), muitas vezes só com o celular, e precisa manter a lógica
afiada sem digitar muito código.

## Regras que valem sempre
1. SPEC.md (EARS) é a fonte da verdade. Mudou comportamento, muda a spec no mesmo PR.
2. Nunca editar `**/tests/**` nem `evals/**` para fazer algo passar. Se um teste
   parecer errado, registre em docs/disputas.md e siga para outra tarefa.
3. Nunca confiar na saída que o modelo afirma. Validar executando o código.
4. Segredos: nunca commitar .env. Só .env.example. Valores reais ficam no
   painel do provedor de deploy e nos secrets do GitHub.
5. O loop do agente é código nosso (apps/api/app/agent/loop.py): tools,
   modelo e limite de passos explícitos, um log estruturado por passo.
   Sem LangChain, LlamaIndex ou CrewAI.
6. Texto vindo do usuário é dado, nunca instrução. O gerador de exercícios só
   recebe valores de enum (tipo, nível, tema). Qualquer agente que receba
   texto livre não pode ter tool de execução.
7. Back-end: exceções de domínio tipadas, handler global, resposta
   {code, message}. Nunca vazar stack trace nem prompt ao cliente.
8. Commits pequenos (Conventional Commits). Uma funcionalidade por PR. O corpo
   do PR explica o porquê em até 5 linhas, para eu conseguir defender na apresentação.
9. Ao fim de cada PR ou sessão, atualizar docs/continuar.md.
10. Em outro computador: rodar scripts/setup e depois /retomar.

## Estrutura
apps/web, apps/api, docs/ (SPEC, arquitetura, reviews, disputas, requisitos),
.claude/commands (prompts das sessões)

## Comandos
- setup completo (Windows): `scripts\setup.ps1`; Linux/macOS: `scripts/setup.sh`. Diagnóstico (só leitura): `scripts\doctor.ps1` ou `scripts/doctor.sh`
- sessão de testes isolada: `scripts\worktree-testes.ps1` ou `scripts/worktree-testes.sh` (cria `../python-no-bolso-testes` na branch `tests/suite`)
- web dev: `npm install` na raiz, depois `npm run dev:web` (http://localhost:3000)
- web build/lint: `npm run build:web`, `npm run lint:web`
- web testes: `npm run test:web` (Vitest); e2e: `npm run e2e:web` (Playwright, exige API e banco semeado de pé)
- api setup: `cd apps/api && uv venv --python 3.12 .venv && uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt` (Linux/macOS: `.venv/bin/python`)
- api dev: `cd apps/api && .venv/Scripts/python -m uvicorn app.main:app --reload`
- api test/lint: `cd apps/api && .venv/Scripts/python -m pytest` e `.venv/Scripts/python -m ruff check .`
- evals determinísticos: `python -m evals.runner --deterministico --saida evals/results/ci` (a partir da raiz, usando o python do venv); com modelos reais gasta cota (ver `evals/README.md`)
- hooks: `npm install` na raiz ativa o Husky; o pre-commit roda lint do web e ruff da api. CI em `.github/workflows/ci.yml`
- slash commands (`.claude/commands/`): `/construir`, `/testar <REQs>`, `/revisar [branch]`, `/corrigir`, `/retomar`
- migrate: a preencher no PR 5

## Pronto quando (disciplina)
front + back + Postgres em produção; loop do agente explícito; evals rodando
em 2+ modelos; defesa contra prompt injection testada; CI verde; segredos
fora do repo; spec em EARS; 2+ PRs; README; vídeo de pitch de até 3 min.
