"""Métricas (a) a (d) por exercício. Nenhuma confia no que o modelo afirma: tudo é re-executado.

(a) saída afirmada = saída obtida ao executar o código
(b) JSON válido no schema do exercício
(c) achar_bug: o código com defeito realmente falha e a correção realmente funciona
(d) ordenar_linhas: existe uma única ordem válida das peças
A métrica (e), Self-BLEU, é do conjunto e está em selfbleu.py.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from pathlib import Path

from jsonschema import Draft202012Validator

from evals.execucao import Resultado, executar

SCHEMA = json.loads((Path(__file__).parent / "exercicio.schema.json").read_text(encoding="utf-8"))
_VALIDADOR = Draft202012Validator(SCHEMA)
MAX_PECAS = 6  # 6! = 720 permutações no pior caso

Executor = Callable[[str], Resultado]


def normalizar(saida: str) -> str:
    return "\n".join(linha.rstrip() for linha in saida.strip().splitlines())


def metrica_b(exercicio: object) -> tuple[bool, str | None]:
    """(b) valida o JSON contra o schema. Devolve (ok, primeiro erro)."""
    erros = sorted(_VALIDADOR.iter_errors(exercicio), key=lambda e: list(e.path))
    if erros:
        e = erros[0]
        return False, f"{'/'.join(map(str, e.path)) or 'raiz'}: {e.message[:120]}"
    return True, None


def codigo_para_executar(ex: dict) -> tuple[str | None, str | None]:
    """Monta o programa cuja saída o modelo afirma (saida_esperada). (codigo, erro)."""
    tipo = ex["tipo"]
    if tipo == "prever_saida":
        return ex["codigo"], None
    if tipo == "completar_lacuna":
        if "___" not in ex["codigo"]:
            return None, "código sem lacuna '___'"
        try:
            return ex["codigo"].replace("___", ex["opcoes"][ex["gabarito"][0]]), None
        except IndexError:
            return None, "gabarito fora das opções"
    if tipo == "ordenar_linhas":
        ordem = ex["gabarito"]
        if sorted(ordem) != list(range(len(ex["opcoes"]))):
            return None, "gabarito não é uma permutação das peças"
        return "\n".join(ex["opcoes"][i] for i in ordem), None
    return ex["codigo_corrigido"], None  # achar_bug: a saída afirmada é a da versão corrigida


def metrica_a(ex: dict, executor: Executor = executar) -> tuple[bool, str | None]:
    """(a) executa o código e compara a saída real com a afirmada."""
    codigo, erro = codigo_para_executar(ex)
    if erro:
        return False, erro
    res = executor(codigo)
    if not res.ok:
        return False, f"não executou: {res.motivo or res.stderr[-80:]}"
    if normalizar(res.stdout) != normalizar(ex["saida_esperada"]):
        return False, f"divergência: real={normalizar(res.stdout)[:40]!r} afirmada={ex['saida_esperada'][:40]!r}"
    return True, None


def metrica_c(ex: dict, executor: Executor = executar) -> tuple[bool | None, str | None]:
    """(c) só para achar_bug. O defeito falha (erro ou saída errada) e a correção funciona."""
    if ex["tipo"] != "achar_bug":
        return None, None
    if ex["codigo"].strip() == ex["codigo_corrigido"].strip():
        return False, "código com defeito idêntico à correção"
    esperado = normalizar(ex["saida_esperada"])
    defeito = executor(ex["codigo"])
    if defeito.ok and normalizar(defeito.stdout) == esperado:
        return False, "o código com defeito já produz a saída esperada (não falha)"
    correcao = executor(ex["codigo_corrigido"])
    if not (correcao.ok and normalizar(correcao.stdout) == esperado):
        return False, "a correção não produz a saída esperada"
    return True, None


def metrica_d(ex: dict, executor: Executor = executar) -> tuple[bool | None, str | None]:
    """(d) só para ordenar_linhas. Conta as ordens distintas que executam com a saída esperada."""
    if ex["tipo"] != "ordenar_linhas":
        return None, None
    pecas = ex["opcoes"]
    if len(pecas) > MAX_PECAS:
        return False, f"mais de {MAX_PECAS} peças: não dá para provar a unicidade"
    esperado = normalizar(ex["saida_esperada"])
    vistos: dict[str, bool] = {}
    for perm in itertools.permutations(range(len(pecas))):
        codigo = "\n".join(pecas[i] for i in perm)
        if codigo in vistos:
            continue
        res = executor(codigo)
        vistos[codigo] = res.ok and normalizar(res.stdout) == esperado
    validas = sum(vistos.values())
    if validas != 1:
        return False, f"{validas} ordens válidas (esperado exatamente 1)"
    return True, None
