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

## Estrutura
apps/web, apps/api, docs/ (SPEC, arquitetura, reviews, disputas, requisitos),
.claude/commands (prompts das sessões)

## Comandos
- web dev: `npm install` na raiz, depois `npm run dev:web` (http://localhost:3000)
- web build/lint: `npm run build:web`, `npm run lint:web`
- api setup: `cd apps/api && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt`
- api dev: `cd apps/api && .venv/Scripts/python -m uvicorn app.main:app --reload`
- api test/lint: `cd apps/api && .venv/Scripts/python -m pytest` e `.venv/Scripts/python -m ruff check .`
- evals, migrate: a preencher nos PRs 13 e 5

## Pronto quando (disciplina)
front + back + Postgres em produção; loop do agente explícito; evals rodando
em 2+ modelos; defesa contra prompt injection testada; CI verde; segredos
fora do repo; spec em EARS; 2+ PRs; README; vídeo de pitch de até 3 min.