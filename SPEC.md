# SPEC: Python no Bolso

Fonte da verdade do comportamento (CLAUDE.md, regra 1). Mudou comportamento, muda esta spec no mesmo PR.
Requisitos em EARS: ubíquo ("O sistema deve..."), evento ("Quando..."), estado ("Enquanto..."),
indesejado ("Se... então...").

**Pessoa e dor:** dev júnior em busca de vaga, que estuda em tempo picado (fila, ônibus), muitas vezes
só com o celular, e precisa manter a lógica afiada sem digitar muito código.

**Tipos de exercício:** `prever_saida`, `completar_lacuna`, `ordenar_linhas`, `achar_bug`.
**Níveis:** `iniciante`, `intermediario`, `avancado`.
**Temas:** `variaveis`, `condicionais`, `lacos`, `listas`, `funcoes`, `strings`, `dicionarios`, `erros`.
**Código do front:** `apps/web/app` (telas) e `apps/web/lib` (`device-id.ts`, `api.ts`); não há `apps/web/src`.

## Exercícios
- **REQ-001** O sistema deve oferecer quatro tipos de exercício: `prever_saida`, `completar_lacuna`, `ordenar_linhas`, `achar_bug`.
- **REQ-002** O sistema deve classificar cada exercício em um nível e um tema dos enums acima.
- **REQ-003** Quando o usuário pedir um exercício, o sistema deve devolver um exercício validado, filtrado por tipo, nível e tema opcionais, priorizando os ainda não resolvidos por aquele aparelho (exclui os que o aparelho já acertou; se não sobrar nenhum, repete sem erro).
- **REQ-004** O sistema não deve incluir o gabarito na resposta que entrega o exercício ao cliente: nem `gabarito`, nem `saida_esperada`, `explicacao` ou `explicacoes_por_opcao`.
- **REQ-005** O sistema deve permitir resolver todos os tipos usando apenas toques, sem digitação de código.
- **REQ-006** Se não houver exercício validado que atenda ao filtro, então o sistema deve devolver o erro `SEM_EXERCICIO` (404) e sugerir, na mensagem, um filtro mais amplo. Filtro com valor fora dos enums devolve `FILTRO_INVALIDO` (422).

## Correção
- **REQ-007** Quando o usuário enviar uma resposta, o sistema deve compará-la ao gabarito armazenado e informar se está correta ou incorreta.
- **REQ-008** O sistema deve aceitar como resposta apenas números inteiros: um índice por resposta e, em `ordenar_linhas`, uma lista de pares `[índice, nível de indentação]` (um por peça, na ordem das linhas, nível 0 a 3), nunca texto livre.
- **REQ-009** Quando o usuário enviar uma resposta válida, o sistema deve registrar a tentativa, certa ou errada. Quando a resposta for correta, deve também mostrar a explicação do exercício.
- **REQ-010** Se a resposta for inválida (corpo malformado, índice fora do intervalo ou formato errado), então o sistema deve rejeitá-la com `RESPOSTA_INVALIDA` (422) sem registrar tentativa. Se o exercício, com id bem formado, não existir, então o sistema deve responder `EXERCICIO_NAO_ENCONTRADO` (404), também sem registrar tentativa.

## Explicação de erro
- **REQ-011** Quando a resposta for incorreta, o sistema deve exibir, na hora, a explicação do erro específica da opção escolhida, lida de `explicacoes_por_opcao`. O agente explicador só é chamado nesse caminho quando a opção não tem explicação armazenada.
- **REQ-012** O agente explicador não deve ter tool de execução e só deve receber dados estruturados: o id do exercício e a opção escolhida (explicação automática) ou o exercício e a resposta numérica do usuário (REQ-045).
- **REQ-013** Se o agente explicador falhar ou estourar o tempo (5 s), então o sistema deve exibir a explicação genérica armazenada no exercício.

## Progresso por aparelho anônimo
- **REQ-014** Quando um aparelho abrir o app sem `device_id` guardado, o cliente deve gerar um UUID e guardá-lo localmente.
- **REQ-015** O sistema deve associar tentativas ao `device_id` sem exigir cadastro, e-mail ou senha.
- **REQ-016** O sistema deve mostrar ao usuário total de acertos, taxa de acerto por tipo (acertos ÷ tentativas, com os quatro tipos sempre presentes) e sequência de dias com prática. A sequência conta dias seguidos no fuso `America/Sao_Paulo`, com qualquer tentativa válida; sem prática hoje, ela continua viva se houve prática ontem, e um dia inteiro sem praticar a zera.
- **REQ-017** Enquanto o aparelho estiver sem conexão, o app deve exibir uma tela de erro amigável e permitir tentar de novo, sem perder a sessão.
- **REQ-018** Se o `device_id` (header `X-Device-Id`) estiver ausente ou não for um UUID válido, então o sistema deve responder `DEVICE_INVALIDO` (400).

## Geração por agente
- **REQ-019** O sistema deve gerar exercícios por um agente cujo loop está em `apps/api/app/agent/loop.py`, com tools, modelo e limite de passos explícitos.
- **REQ-020** O sistema deve registrar um log estruturado por passo do loop (execução, passo, tool, modelo, duração, resultado).
- **REQ-021** O gerador deve receber apenas valores de enum (tipo, nível, tema) como entrada.
- **REQ-022** Se o loop atingir o limite de passos sem produzir um exercício válido, então o sistema deve encerrar a execução como `falhou` e registrá-la.
- **REQ-023** O sistema deve permitir trocar de provedor ou modelo por configuração, sem mudar o loop.
- **REQ-024** Quando o estoque de um (tipo, nível, tema) estiver abaixo de um mínimo configurado, o sistema deve poder gerar novos exercícios em lote por comando administrativo (CLI), e nunca por requisição de usuário.

## Validação por execução
- **REQ-025** O sistema não deve salvar exercício cujo código de referência não tenha sido executado com sucesso.
- **REQ-026** O sistema deve comparar a saída real da execução com a saída afirmada pelo modelo (ignorando espaços no fim de linha e linhas vazias no fim) e rejeitar o exercício se divergirem. Em `achar_bug`, a saída afirmada é a da versão corrigida (`codigo_corrigido`), e o código com bug deve falhar ou divergir dela. Em `ordenar_linhas`, o exercício só é aprovado se existir **exatamente uma** combinação de ordem e indentação das peças que execute e produza a saída afirmada.
- **REQ-027** O sistema deve executar código gerado em sandbox com timeout, limite de memória, sem rede e sem acesso ao sistema de arquivos do app.
- **REQ-028** Quando a validação aprovar o exercício, o sistema deve salvá-lo com `status = validado`.
- **REQ-029** Quando a validação rejeitar o exercício, o sistema deve descartá-lo e registrar o motivo na execução de geração.
- **REQ-030** O sistema deve validar o schema da saída do modelo (tipo, campos, tamanhos) antes de executar qualquer código.

## Erros do back-end
- **REQ-031** O back-end deve representar falhas de domínio por exceções tipadas.
- **REQ-032** O back-end deve ter um handler global que responda `{code, message}` com o status HTTP adequado, inclusive para os erros do framework (404 `NAO_ENCONTRADO`, 405 `METODO_NAO_PERMITIDO`). Exceção deliberada: o corpo de `GET /health` (REQ-044) não segue `{code, message}`, pois quem o consome é um monitor de saúde.
- **REQ-033** O sistema não deve incluir stack trace, prompt ou detalhe interno em resposta ao cliente.
- **REQ-034** Se ocorrer erro não previsto, então o sistema deve responder `ERRO_INTERNO` (500), registrar o stack trace só no log e devolver o id de correlação no campo `correlacao_id` do corpo, o mesmo id registrado no log.
- **REQ-035** Se o banco estiver indisponível, então as rotas de negócio devem responder `INDISPONIVEL` (503), e `GET /health` deve responder conforme o REQ-044.

## Segurança
- **REQ-036** O sistema deve tratar todo texto vindo do usuário como dado, nunca como instrução de modelo.
- **REQ-037** Qualquer agente que receba texto livre não deve ter tool de execução.
- **REQ-038** O sistema deve ter testes de prompt injection mostrando que conteúdo hostil, em campos que cheguem a um prompt, não altera as tools chamadas nem a saída validada.
- **REQ-039** O repositório não deve conter segredos: só `.env.example` é versionado; valores reais ficam no provedor de deploy e nos secrets do GitHub.
- **REQ-040** O sistema deve limitar a taxa de requisições a 120 por minuto por aparelho e 300 por minuto por IP, respondendo `LIMITE_EXCEDIDO` (429). O IP vem da conexão; `X-Forwarded-For` só é considerado com `TRUST_PROXY=1`.
- **REQ-041** O sistema deve restringir CORS à origem do front configurada.

## Qualidade e operação
- **REQ-042** O repositório deve ter evals que rodem o mesmo conjunto de casos em 2 ou mais modelos e comparem a ação executada (tool chamada, exercício aprovado ou rejeitado).
- **REQ-043** O CI deve rodar lint, testes e evals determinísticos (`--deterministico`, sem modelo real e sem cota) a cada PR. Evals com modelos reais rodam sob demanda.
- **REQ-044** O sistema deve expor `GET /health` com o status da API e do banco. Quando o banco estiver acessível, o sistema deve responder 200 com `{"status":"ok","db":"ok"}`. Se o banco estiver inacessível, então o sistema deve responder 503 com `{"status":"degraded","db":"erro"}`. A rota não tem rate limit (REQ-040).
- **REQ-045** Quando o usuário, depois de uma resposta incorreta, pedir "explicar meu erro", o sistema deve chamar o agente explicador com o exercício e a resposta do usuário, e exibir a explicação do raciocínio equivocado. A resposta é sempre numérica (índices, ou pares índice-indentação em `ordenar_linhas`), nunca texto livre. Se a resposta for correta, o sistema deve devolver a explicação geral sem chamar o agente. Se o agente falhar ou estourar o tempo, então o sistema deve exibir a explicação armazenada da opção escolhida (ou a geral, se não houver). Esse pedido não registra tentativa.
