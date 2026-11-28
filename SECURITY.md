# Segurança

## O sandbox é defesa em camadas, não isolamento perfeito

O código gerado por modelo roda em um sandbox Python (REQ-027). Ele **reduz** o risco; **não** garante isolamento
perfeito. Um sandbox em processo Python pode ter falhas, e não devemos tratá-lo como fronteira de segurança sozinho.

Camadas atuais (D-23):
1. **Validação antes de executar:** o schema da saída do modelo é conferido antes de qualquer execução (REQ-030).
2. **Lista de permissão de imports:** só `math`, `itertools`, `collections`, `string`, `functools`, `statistics` e `time`.
3. **Limites de recurso:** timeout de 2 s, 128 MB de memória e saída de até 1 MB. Os limites de memória e de
   processos (rlimit) só funcionam em Linux; no Windows os testes correspondentes ficam pulados.
4. **Sem rede e sem acesso ao sistema de arquivos do app**, nem às variáveis de ambiente do processo da API.
5. **Execução fora do caminho do usuário:** só a CLI administrativa gera exercícios (REQ-024). Nenhum texto livre
   do usuário chega ao gerador nem a um executor (REQ-021, REQ-036, REQ-037).

O que isso **não** cobre: vulnerabilidades do interpretador Python, escape do sandbox por técnica ainda não
testada e abuso de CPU dentro do limite de tempo. Por isso, em produção o sandbox deve rodar em container
sem privilégios, sem segredos montados e com rede desabilitada; trate essa camada como obrigatória no deploy.

## Outras defesas
- Segredos fora do repositório: só `.env.example` é versionado; o gitleaks roda no CI (REQ-039).
- Rate limit por aparelho e por IP (REQ-040). Atrás de proxy, defina `TRUST_PROXY=1` (ver README).
- CORS restrito à origem do front (REQ-041).
- Erros sem stack trace, prompt ou detalhe interno para o cliente (REQ-033).

## Reportar uma vulnerabilidade
Abra uma *security advisory* privada no repositório do GitHub ou fale diretamente com a pessoa responsável pelo
projeto. Não publique detalhes de falha em issues públicas antes de ela ser corrigida.
