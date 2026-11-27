# Evals

Roda a **mesma bateria** (`casos.yaml`, só enums) em cada modelo de `models.yaml` e mede, re-executando
o código (nunca confiando no que o modelo afirma, CLAUDE.md regra 3):

| | Métrica |
|---|---|
| (a) | saída afirmada pelo modelo = saída obtida ao executar o código |
| (b) | JSON válido no schema do exercício (`exercicio.schema.json`) |
| (c) | achar-bug: o código com defeito realmente falha e a correção realmente funciona |
| (d) | montar-código: existe exatamente uma ordem válida das peças |
| (e) | variedade entre os exercícios gerados (Self-BLEU; menor = mais variedade) |

Também registra a **ação** de cada caso (`aprovado`, `rejeitado`, `falhou`) e as tools chamadas, para
comparar o comportamento entre modelos (REQ-042).

## Como rodar

Da raiz do repositório, com o venv da API (`apps/api/.venv`):

```
# modelos reais: GASTA COTA. Exige GEMINI_API_KEY e GROQ_API_KEY no ambiente (nunca em arquivo)
python -m evals.runner
python -m evals.runner --modelos groq-llama --casos 3

# mock determinístico: sem rede e sem cota. NÃO mede modelo real, só valida a bateria
python -m evals.runner --deterministico

# testes da própria bateria (executor, métricas, Self-BLEU, runner)
python -m pytest evals/tests
```

Resultados: `evals/results/<data>/` com `<modelo>.json`, `<modelo>.md` (tabela) e `resumo.md`.
**Evals com modelos reais não rodam no CI**: gastam cota e ficam sob demanda. O CI roda só o modo
`--deterministico` e os testes da bateria (job `evals` em `.github/workflows/ci.yml`, REQ-043).

## Avisos

- `models.yaml` foi criado com 2 modelos de **exemplo**; confirme nomes e cota no painel do provedor.
- `execucao.py` é uma guarda de melhor esforço (análise estática + processo isolado + timeout) para
  rodar código de modelo na máquina de quem desenvolve. **Não é o sandbox de produção** (REQ-027) e
  não tem limite de memória no Windows.
- O schema do exercício e o protocolo de tool do runner são **propostas**: a spec não os fixa.
