# SPEC: Python no Bolso

Fonte da verdade do comportamento (CLAUDE.md, regra 1). Mudou comportamento, muda esta spec no mesmo PR.
Requisitos em EARS: ubíquo ("O sistema deve..."), evento ("Quando..."), estado ("Enquanto..."),
indesejado ("Se... então...").

**Pessoa e dor:** dev júnior em busca de vaga, que estuda em tempo picado (fila, ônibus), muitas vezes
só com o celular, e precisa manter a lógica afiada sem digitar muito código.

**Tipos de exercício:** `prever_saida`, `completar_lacuna`, `ordenar_linhas`, `achar_bug`.
**Níveis:** `iniciante`, `intermediario`.
**Temas:** `variaveis`, `condicionais`, `lacos`, `listas`, `funcoes`, `strings`.

## Exercícios
- **REQ-001** O sistema deve oferecer quatro tipos de exercício: `prever_saida`, `completar_lacuna`, `ordenar_linhas`, `achar_bug`.
- **REQ-002** O sistema deve classificar cada exercício em um nível e um tema dos enums acima.
- **REQ-003** Quando o usuário pedir um exercício, o sistema deve devolver um exercício validado, filtrado por tipo, nível e tema opcionais, priorizando os ainda não resolvidos por aquele aparelho.
- **REQ-004** O sistema não deve incluir o gabarito na resposta que entrega o exercício ao cliente.
- **REQ-005** O sistema deve permitir resolver todos os tipos usando apenas toques, sem digitação de código.
- **REQ-006** Se não houver exercício validado que atenda ao filtro, então o sistema deve devolver o erro `SEM_EXERCICIO` e sugerir um filtro mais amplo.

## Correção
- **REQ-007** Quando o usuário enviar uma resposta, o sistema deve compará-la ao gabarito armazenado e informar se está correta ou incorreta.
- **REQ-008** O sistema deve aceitar como resposta apenas índices numéricos, nunca texto livre.
- **REQ-009** Quando a resposta for correta, o sistema deve registrar a tentativa e mostrar a explicação do exercício.
- **REQ-010** Se a resposta for inválida (índice fora do intervalo ou formato errado), então o sistema deve rejeitá-la com `RESPOSTA_INVALIDA` sem registrar tentativa.

## Explicação de erro
- **REQ-011** Quando a resposta for incorreta, o sistema deve exibir uma explicação do erro específica da opção escolhida.
- **REQ-012** O agente explicador deve receber apenas o id do exercício e a opção escolhida, e não deve ter tool de execução.
- **REQ-013** Se o agente explicador falhar ou estourar o tempo, então o sistema deve exibir a explicação genérica armazenada no exercício.

## Progresso por aparelho anônimo
- **REQ-014** Quando um aparelho abrir o app sem `device_id` guardado, o cliente deve gerar um UUID e guardá-lo localmente.
- **REQ-015** O sistema deve associar tentativas ao `device_id` sem exigir cadastro, e-mail ou senha.
- **REQ-016** O sistema deve mostrar ao usuário total de acertos, taxa de acerto por tipo e sequência de dias com prática.
- **REQ-017** Enquanto o aparelho estiver sem conexão, o app deve exibir uma tela de erro amigável e permitir tentar de novo, sem perder a sessão.
- **REQ-018** Se o `device_id` não for um UUID válido, então o sistema deve responder `DEVICE_INVALIDO`.

## Geração por agente
- **REQ-019** O sistema deve gerar exercícios por um agente cujo loop está em `apps/api/app/agent/loop.py`, com tools, modelo e limite de passos explícitos.
- **REQ-020** O sistema deve registrar um log estruturado por passo do loop (execução, passo, tool, modelo, duração, resultado).
- **REQ-021** O gerador deve receber apenas valores de enum (tipo, nível, tema) como entrada.
- **REQ-022** Se o loop atingir o limite de passos sem produzir um exercício válido, então o sistema deve encerrar a execução como `falhou` e registrá-la.
- **REQ-023** O sistema deve permitir trocar de provedor ou modelo por configuração, sem mudar o loop.
- **REQ-024** Quando o estoque de um (tipo, nível, tema) estiver abaixo de um mínimo configurado, o sistema deve poder gerar novos exercícios em lote por comando administrativo (CLI), e nunca por requisição de usuário.

## Validação por execução
- **REQ-025** O sistema não deve salvar exercício cujo código de referência não tenha sido executado com sucesso.
- **REQ-026** O sistema deve comparar a saída real da execução com a saída afirmada pelo modelo e rejeitar o exercício se divergirem.
- **REQ-027** O sistema deve executar código gerado em sandbox com timeout, limite de memória, sem rede e sem acesso ao sistema de arquivos do app.
- **REQ-028** Quando a validação aprovar o exercício, o sistema deve salvá-lo com `status = validado`.
- **REQ-029** Quando a validação rejeitar o exercício, o sistema deve descartá-lo e registrar o motivo na execução de geração.
- **REQ-030** O sistema deve validar o schema da saída do modelo (tipo, campos, tamanhos) antes de executar qualquer código.

## Erros do back-end
- **REQ-031** O back-end deve representar falhas de domínio por exceções tipadas.
- **REQ-032** O back-end deve ter um handler global que responda `{code, message}` com o status HTTP adequado.
- **REQ-033** O sistema não deve incluir stack trace, prompt ou detalhe interno em resposta ao cliente.
- **REQ-034** Se ocorrer erro não previsto, então o sistema deve responder `ERRO_INTERNO`, registrar o stack trace só no log e devolver um id de correlação.
- **REQ-035** Se o banco estiver indisponível, então `GET /health` deve responder falha e as demais rotas devem responder `INDISPONIVEL`.

## Segurança
- **REQ-036** O sistema deve tratar todo texto vindo do usuário como dado, nunca como instrução de modelo.
- **REQ-037** Qualquer agente que receba texto livre não deve ter tool de execução.
- **REQ-038** O sistema deve ter testes de prompt injection mostrando que conteúdo hostil, em campos que cheguem a um prompt, não altera as tools chamadas nem a saída validada.
- **REQ-039** O repositório não deve conter segredos: só `.env.example` é versionado; valores reais ficam no provedor de deploy e nos secrets do GitHub.
- **REQ-040** O sistema deve limitar a taxa de requisições por aparelho e por IP.
- **REQ-041** O sistema deve restringir CORS à origem do front configurada.

## Qualidade e operação
- **REQ-042** O repositório deve ter evals que rodem o mesmo conjunto de casos em 2 ou mais modelos e comparem a ação executada (tool chamada, exercício aprovado ou rejeitado).
- **REQ-043** O CI deve rodar lint, testes e evals determinísticos a cada PR.
- **REQ-044** O sistema deve expor `GET /health` com o status da API e do banco.
