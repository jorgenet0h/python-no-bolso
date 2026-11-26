# Lacunas e ambiguidades da SPEC

Escrito pela sessão de testes. **A SPEC.md não foi editada.** Cada item diz o que faltou para
escrever o teste, o que o teste assumiu e a mudança proposta. Você decide; quando decidir, a SPEC
muda no mesmo PR da implementação (CLAUDE.md, regra 1) e os testes seguem a decisão.

Como ler a coluna **Teste**: é o que passa a depender da decisão. Todo o "contrato proposto" está
concentrado em `apps/api/tests/contrato.py` e `apps/web/tests/contrato.ts`: se a implementação
escolher outros nomes, só esses dois arquivos mudam.

## 1. Contrato proposto (nomes que a spec não fixa)

Não existe OpenAPI exportado. Rotas e modelo de dados vêm de `docs/arquitetura.md`; o resto abaixo é
**proposta**. Enquanto o módulo não existir, o teste falha com `NAO-IMPLEMENTADO` (categoria A).

| Peça | Proposta usada pelos testes |
|---|---|
| Rotas | `GET /exercicios?tipo&nivel&tema`, `POST /respostas`, `GET /progresso`, `GET /health`; header `X-Device-Id` |
| `POST /respostas` | corpo `{exercicio_id, resposta: [int]}` → `{correta: bool, explicacao: str}` |
| `GET /exercicios` | `{id, tipo, nivel, tema, enunciado, codigo, opcoes}`, sem os campos de `CAMPOS_GABARITO` |
| `GET /progresso` | `{total_acertos: int, taxa_por_tipo: {tipo: 0..1}, sequencia_dias: int}` |
| `GET /health` | 200 `{"status":"ok","db":"ok"}`; banco fora: 503 `{"status":"degraded","db":"erro"}` (decidido em DISP-001; `contrato.py: HEALTH_OK/HEALTH_DEGRADADO`) |
| `app.errors` | `ErroDominio(Exception)` com `code` e `status_code`; subclasses para `SEM_EXERCICIO`, `RESPOSTA_INVALIDA`, `DEVICE_INVALIDO`, `INDISPONIVEL` |
| `app.db` | `SessionLocal`, `get_session` (dependência FastAPI), `Base`, `engine`; banco de teste via `TEST_DATABASE_URL` |
| `app.models` | `Exercicio`, `Tentativa`, `ExecucaoGeracao`, `PassoGeracao` com as colunas do modelo de dados |
| `app.sandbox` | `executar(codigo, *, timeout_s, memoria_mb)` → `.ok .stdout .stderr .motivo` (`motivo` contém "timeout", "memoria", ...) |
| `app.validador` | `validar(candidato: dict, *, executor)` → `.aprovado .motivo` |
| `app.agent.loop` | `TOOLS` (inclui `executar_python`), `gerar(tipo, nivel, tema, *, provedor, executor, max_passos)` → `.status` (`aprovado`/`rejeitado`/`falhou`) |
| `app.agent.explicador` | `TOOLS` (vazio), `explicar(exercicio_id, opcao, *, provedor)` |
| Provedor de modelo | objeto com `completar(mensagens, tools) -> dict`; resposta `{"tool","args"}` ou `{"final": exercicio}` |
| `app.config` | `carregar_provedor()` escolhe provedor/modelo por variável de ambiente |
| `app.cli` | `gerar_lote(tipo, nivel, tema, minimo, provedor, executor)` |
| Front | `lib/device-id.ts` → `obterDeviceId()`; `lib/api.ts` → `chamarApi(caminho, init)` que rejeita com `{code, message}` |
| `data-testid` (e2e) | `iniciar`, `enunciado`, `opcao-<i>`, `confirmar`, `resultado`, `explicacao`, `progresso-link`, `total-acertos`, `taxa-<tipo>`, `sequencia-dias`, `erro-conexao`, `tentar-de-novo` |
| Semente do e2e | banco com 1 exercício `prever_saida/iniciante/variaveis`, opção correta = índice 1; API de pé em `NEXT_PUBLIC_API_URL`. Falta um comando de semente (`python -m app.cli semear-e2e`?) |
| Isolamento | os testes assumem banco vazio por teste e rate limit reiniciável; falta definir o mecanismo (fixture de limpeza em `conftest.py` quando `app.db` existir) |

## 2. Ambiguidades por requisito

| ID | REQ | Problema | Proposta | Teste |
|---|---|---|---|---|
| GAP-003 | 003 | "Priorizando os não resolvidos": e quando todos já foram resolvidos? Aleatório, o mais antigo, o menos recente? | Voltar a servir resolvidos, sem erro | `test_req_003` só cobre a priorização |
| GAP-004 | 004 | `saida_esperada` e `explicacao` também entregam a resposta? Em `prever_saida`, `saida_esperada` **é** a resposta. | Nenhum de `gabarito`, `saida_esperada`, `explicacao`, `explicacoes_por_opcao` sai no GET | `test_req_004` |
| GAP-006 | 006 | Sem status HTTP para `SEM_EXERCICIO` e sem formato para a "sugestão de filtro mais amplo" | 404; a sugestão vai em `message` (palavra "filtro") | `test_req_006` aceita qualquer 4xx |
| GAP-008 | 008, 010 | Quantos índices por tipo? `ordenar_linhas` exige permutação; os demais, 1 índice. Rejeitar `true`, `1.5`, `"1"`, negativo? Índice repetido? | Lista de inteiros (não bool); tamanho 1, exceto `ordenar_linhas` (permutação) | `test_req_008`, `test_req_010` |
| GAP-009 | 009, 016 | REQ-009 só fala em registrar tentativa **correta**, mas REQ-016 (taxa de acerto) precisa das erradas | Toda resposta **válida** registra tentativa; REQ-009 só acrescenta a explicação | `test_req_016`, `test_req_009` |
| GAP-011 | 011, 012, 013, 037 | De onde vem a "explicação específica da opção": do agente (em requisição) ou de `explicacoes_por_opcao` (já no modelo de dados)? Se já existe o campo, para que o agente? Também falta o tempo limite do REQ-013. E o explicador só recebe id e opção, logo **não recebe texto livre**: REQ-037 nem se aplicaria a ele. | Explicador gera ou escolhe a explicação; timeout configurável (ex.: 5 s); mesmo assim sem tools | `test_req_011`, `_012`, `_013`, `_037` |
| GAP-014 | 014 | Chave do `localStorage` e comportamento com storage bloqueado (modo privado) | Qualquer chave; fallback em memória com UUID válido | `req-014.test.ts` |
| GAP-016 | 016 | "Sequência de dias com prática": dias consecutivos até hoje ou até ontem? Fuso (UTC ou São Paulo)? Tentativa errada conta? | Consecutivos terminando hoje ou ontem, fuso `America/Sao_Paulo`, qualquer tentativa válida | `test_req_016` só cobre "praticou hoje = 1" |
| GAP-017 | 017 | "Sem perder a sessão" não define o que é a sessão | Exercício atual, opção marcada e `device_id` preservados | `req-017.test.ts`, `test_e2e_02` |
| GAP-018 | 018 | Header ausente é `DEVICE_INVALIDO`? Aceita UUID v1? (a arquitetura diz v4, a spec diz "UUID válido") | Ausente = inválido; só v4 | `test_req_018` (testa ausente) |
| GAP-020 | 020 | Formato do "log estruturado" | JSON por linha com `execucao, passo, tool, modelo, duracao_ms, resultado` | `test_req_020` |
| GAP-021 | 021 | Valor fora do enum no gerador: qual erro? | Subclasse de `ErroDominio`, antes de qualquer chamada ao modelo | `test_req_021`, `test_req_038` |
| GAP-022 | 022 | Qual o limite padrão de passos? Exercício final inválido é `rejeitado` e limite estourado é `falhou`? | Padrão 5; sim | `test_req_022` |
| GAP-023 | 023 | "Por configuração": quais variáveis? Só é testável que dois provedores dão o mesmo resultado e que `app.config.carregar_provedor` existe | `MODEL_PROVIDER`, `MODEL_NAME` | `test_req_023` (parcial) |
| GAP-024 | 024 | "Poder gerar" (não "dever"); granularidade do mínimo; interface da CLI | Gera até atingir `minimo` por (tipo, nivel, tema); `gerar_lote(...)` | `test_req_024` ×2 |
| GAP-025 | 025, 026 | Normalização da comparação de saída (`\n` final, espaços) | Ignorar espaços no fim de linha e linhas vazias no fim | `test_req_026` |
| GAP-026 | 026, arquitetura | O fluxo manda executar "a versão com bug e a corrigida" e "uma permutação errada", mas o **modelo de dados não tem coluna** para o código corrigido; também não diz onde ficam peças e ordem de `ordenar_linhas` | Coluna `codigo_corrigido`; peças em `opcoes`, ordem em `gabarito`; `saida_esperada` do `achar_bug` é a da versão corrigida | `test_req_026` (3 testes), `evals/exercicio.schema.json` |
| GAP-027 | 027 | A spec não manda **bloquear import**, só timeout, memória, rede e FS. Sem números, e rlimit só funciona em Linux. | Bloquear `os`, `subprocess`, `socket`, `ctypes`, `importlib` etc. por allowlist; timeout 2 s; 128 MB; saída ≤ 1 MB. Testes de memória e fork bomb só em Linux (container/CI); no Windows ficam `skipped` | `test_sandbox_adversarial` |
| GAP-030 | 030 | "Tamanhos" sem valores | `enunciado` ≤ 500, `codigo` ≤ 2000, 2 a 6 `opcoes` (ver `evals/exercicio.schema.json`); os testes usam valores muito acima, então aceitam qualquer limite razoável | `test_req_030` |
| GAP-032 | 032, 033, 034 | REQ-032 diz que o handler responde `{code, message}`, REQ-034 acrescenta um id de correlação: onde ele vai? Erros do framework (404, 405, 422) também seguem o formato? Falta o status por código. | Id em header `X-Request-Id` (ou campo extra no 500); framework também em `{code, message}`; 404/422/400/503/500 | `test_req_032..034`, `test_api_payloads_malformados` (exige chaves exatas `{code, message}` em 4xx) |
| GAP-035 | 035 | Como simular banco fora do ar? | Sobrescrever a dependência `app.db.get_session`; rotas de negócio: `INDISPONIVEL` 503; `/health`: ver seção 4 | `test_req_035` |
| GAP-038 | 038 | Quais "campos chegam a um prompt"? Hoje: enums (gerador) e id + opção (explicador). Mas o **enunciado armazenado**, escrito por modelo, é entrada do explicador (injeção indireta). | Tratar esse conteúdo como dado também | `test_prompt_injection` (último teste) |
| GAP-039 | 039 | Sem definição de "segredo" | Heurística por padrões (`AIza…`, `gsk_…`, `sk-…`, chave privada, URL de banco com senha); o `gitleaks` do CI continua sendo a barreira real | `test_req_039` |
| GAP-040 | 040 | Sem limites, janela, nem código de erro; atrás de proxy, o IP confiável é o `X-Forwarded-For`? O limitador é global e **vaza estado entre testes**. | 429 com código `LIMITE_EXCEDIDO`; ≤ 120/min por aparelho e ≤ 300/min por IP; limitador reiniciável em teste | `test_req_040` dispara 300 e 600 requisições |
| GAP-041 | 041 | Métodos e headers permitidos | Só a origem de `CORS_ORIGIN`, `GET/POST`, `X-Device-Id` | `test_req_041` |
| GAP-042 | 042 | Os evals "comparam a ação executada", mas não dizem o que é passar: qual concordância mínima entre modelos? | Relatar por caso e por métrica; sem limiar até haver dados reais | `evals/`, `test_req_042` |
| **GAP-043** | 043 | **Conflito.** A SPEC diz "CI roda evals determinísticos a cada PR". A instrução desta sessão diz que evals **não** rodam no CI (gastam cota). | Dois modos: `--deterministico` (mock, sem cota) entra no CI; modelos reais ficam sob demanda. Basta um passo `python -m evals.runner --deterministico` no `ci.yml`, ou reescrever o REQ-043 | Resolvido no `ci.yml` (job `evals`, só `--deterministico`); falta alinhar a redação do REQ-043 na SPEC |
| GAP-044 | 044 | O `test_health.py` antigo exigia `{"status": "ok"}` exato e contradizia o REQ-044. **Resolvido** em DISP-001: a spec venceu, o teste foi trocado por dois casos. Resta reescrever a SPEC (seção 4). | Ver seção 4 | `test_health.py` (2 casos), `test_req_035` |

## 3. Requisitos só parcialmente testáveis

| REQ | Limite |
|---|---|
| 005 | Só e2e, e só na tela de um tipo (`prever_saida`); falta rodar os 4 tipos (precisa de semente dos 4) |
| 012, 037 | "Recebe apenas id e opção" é verificado pela assinatura e pelo prompt enviado, não por inspeção do código |
| 023 | A parte "por configuração" só checa que `app.config.carregar_provedor` existe |
| 036 | Princípio estrutural: só se mostra que texto livre não chega ao agente pelos caminhos conhecidos |
| 027 | Memória e fork bomb exigem Linux; no Windows os dois testes ficam `skipped` |

## 4. Proposta de redação: REQ-044 (e ajuste no REQ-035)

Para a sessão 1 aplicar na SPEC.md. Formato decidido em DISP-001.

> - **REQ-044** O sistema deve expor `GET /health` com o status da API e do banco.
>   Quando o banco estiver acessível, o sistema deve responder 200 com `{"status":"ok","db":"ok"}`.
>   Se o banco estiver inacessível, então o sistema deve responder 503 com `{"status":"degraded","db":"erro"}`.

Ajuste no REQ-035, para não duplicar nem contradizer o REQ-044:

> - **REQ-035** Se o banco estiver indisponível, então as rotas de negócio devem responder `INDISPONIVEL` (503),
>   e `GET /health` deve responder conforme o REQ-044.

Observações:

- O corpo de erro do `/health` **não** segue `{code, message}` (REQ-032): é uma exceção deliberada, pois quem
  consome é monitor de saúde. Vale registrar a exceção no REQ-032.
- `status` descreve a API (`ok`/`degraded`); `db` descreve o banco (`ok`/`erro`).
