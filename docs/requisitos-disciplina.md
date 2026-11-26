# Requisitos do Projeto Final: Especialização em IA (PdA)

**Fonte:** transcrição do vídeo "Apresentação projeto final", gravado pela professora para a turma (cerca de 19 minutos).
**Atenção:** a transcrição é automática e tem erros. Onde interpretei uma palavra, está marcado com *(interpretação)*. Confirme dúvidas e datas com a professora.

---

## 1. O que é o projeto

- Um **produto de ponta a ponta com IA integrada**.
- Precisa ter **front-end**, **back-end** e **dados persistidos** (banco de dados ou serviço equivalente). Ela chama o banco de "plus" no começo, mas depois diz que "precisa ter"; trate como obrigatório.
- A IA pode ser:
  - **transparente**: um chatbot, ou
  - **por trás dos panos**: o usuário não digita prompt, mas a IA gera um componente ou uma experiência diferente.
- Sugestão de estrutura: **monorepo** (Turborepo ou Nx), para ter front e back na mesma aplicação.
- **Individual ou em grupo de até 4 pessoas.** Ela recomenda grupo.
- Pode usar IA para construir o projeto, além de ter IA dentro dele.

## 2. Ponto de partida: uma pessoa e uma dor

A recomendação principal é começar por **alguém que você consiga nomear**: quem vai usar o sistema e qual problema ele resolve. Exemplos citados no vídeo:

- aluno que se perde e não consegue assistir à aula síncrona;
- pessoa com TDAH que se perde ao fazer tarefas;
- assistência técnica de um familiar que precisa informar o preço de um serviço (por exemplo, trocar uma bateria).

Ideia central: software só é útil se é feito para alguém. Não é código por código.

## 3. Exigências técnicas

- **Tratamento de erros** no back-end.
- **O loop do agente explícito no código**: o equivalente ao `while true` do Claude Code e do Codex. Deve ficar nítido quais tools são chamadas, qual código executa e qual modelo é usado.
- **Evals**: testes que garantem que, ao trocar de provedor ou modelo, o agente continua executando a mesma ação. *(Na transcrição aparece "Evol".)* Tema da próxima aula.
- **Logs e configurações.**
- **Validação contra prompt injection.** Tema da próxima aula.
- **A estrutura de contexto vista em aula no repositório**: os arquivos de instruções do agente e as **skills realmente usadas no projeto** (não vale colocar skill qualquer).
- **Linters e hooks** configurados em sala *(na transcrição aparece "Rusk"; provavelmente Husky)*.
- **CI no GitHub** ou **agente de revisão** (tema da próxima aula).
- **Specs.**
- **Testes end-to-end** são desejáveis (do front até a integração com o back). Ela prefere **EARS** a BDD, por ser mais curto.
- **Segredos:** nunca commitar o `.env`; as variáveis ficam em vault/secrets.

### Modelos de IA

- Modelos **gratuitos** são aceitos.
- Exemplo de um colega: **roteamento entre vários modelos gratuitos** (Gemini, Groq), com rodízio quando a cota acaba. Ela chamou isso de roteador de modelos *(na transcrição, "halter")*.
- Para reduzir respostas com "cara de IA", o mesmo colega pediu a um modelo para ler um artigo sobre sinais de texto gerado por IA e transformar em regras no prompt do sistema (guardrails).
- Se quiserem pagar: o mínimo é cerca de **US$ 5 (aproximadamente R$ 25)**. Em equipe, dá para dividir (R$ 5 por pessoa).

## 4. Processo e avaliação

- **Não precisa de relatório escrito.** O histórico do Git é o relatório de progresso: ela vai olhar commits, o que foi adicionado e o que foi corrigido.
- Em equipe, **no mínimo 2 pull requests por pessoa**.
- **Nada é eliminatório**; ela diz que o curso é mais sobre desenvolver algo. Esses são os critérios que ela olha na correção.
- O projeto deve demonstrar: entender o problema, transformar em código, entregar um produto de ponta a ponta, e mostrar que o aluno entende o loop e que "tudo é contexto".

## 5. Entrega e datas

| O quê | Quando |
|---|---|
| Entrega do projeto + apresentação (8 minutos por pessoa) | **17/12**, última aula |
| Correções, feedbacks e relatório individual de progresso | até **21/12** |

**Formulário de entrega** (o link só será divulgado depois; ela disse que o do vídeo estava errado):

1. Repositório do projeto (**público**)
2. **Vídeo de pitch de até 3 minutos** (usado para divulgação nas redes; compartilhar é opcional, mas incentivado)
3. Usuário de cada integrante

## 6. Próximos passos que ela citou

1. Decidir quem é a equipe (ou fazer individual).
2. Entender qual é a dor do projeto e para quem.
3. Começar a desenvolver.

A **próxima aula** (quarta-feira) cobre **Evals, prompt injection e agente de revisão**, e esses itens entram no projeto.

---

## Checklist de autoavaliação

- [ ] Consigo nomear **quem** usa o sistema e **qual dor** ele resolve.
- [ ] Tem front-end e back-end funcionando juntos.
- [ ] Tem dados persistidos (banco ou serviço equivalente).
- [ ] Tem IA integrada (transparente ou por trás dos panos).
- [ ] O loop do agente está explícito no código (tools, código executado, modelo).
- [ ] Erros do back-end são tratados.
- [ ] Existem logs e configurações.
- [ ] Existem evals que sobrevivem à troca de modelo.
- [ ] Há proteção contra prompt injection.
- [ ] A estrutura de contexto da aula está no repositório, com skills realmente usadas.
- [ ] Linters/hooks e CI (ou agente de revisão) configurados.
- [ ] `.env` fora do Git; segredos em vault/secrets.
- [ ] Histórico do Git com commits reais; em equipe, 2 PRs ou mais por pessoa.
- [ ] Repositório público.
- [ ] Vídeo de pitch de até 3 minutos gravado.
- [ ] Apresentação de 8 minutos ensaiada.

---

## Minha ideia (preencher)

**Ideia:**
**Para quem (pessoa e dor):**
**Onde entra a IA:**
**Equipe:**

## Pergunta para avaliar a viabilidade

> Avalie se a minha ideia atende aos requisitos acima (pessoa e dor nomeadas, IA integrada, front + back + dados persistidos, loop do agente explícito, evals) e se é viável até 17/12. Aponte riscos e o que cortar para caber no prazo.
