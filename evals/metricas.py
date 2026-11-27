"""Métricas (a) a (d) por exercício. Nenhuma confia no que o modelo afirma: tudo é re-executado.

(a) saída afirmada = saída obtida ao executar o código
(b) JSON válido no schema do exercício
(c) achar_bug: o código com defeito realmente falha e a correção realmente funciona
(d) ordenar_linhas: existe uma única combinação válida de ordem e indentação das peças
A métrica (e), Self-BLEU, é do conjunto e está em selfbleu.py.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Callable, Iterator
from pathlib import Path

from jsonschema import Draft202012Validator

from evals.execucao import Resultado, executar

SCHEMA = json.loads((Path(__file__).parent / "exercicio.schema.json").read_text(encoding="utf-8"))
_VALIDADOR = Draft202012Validator(SCHEMA)
MAX_PECAS = 6
MAX_NIVEL = 3  # níveis de indentação aceitos em ordenar_linhas: 0 a 3 (D-06)
MAX_EXECUCOES = 400  # teto de programas executados para provar a unicidade

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
        pares = ex["gabarito"]
        if not all(isinstance(p, list) and len(p) == 2 for p in pares):
            return None, "gabarito de ordenar_linhas deve ser lista de pares [índice, indentação]"
        if sorted(p[0] for p in pares) != list(range(len(ex["opcoes"]))):
            return None, "gabarito não é uma permutação das peças"
        return montar_programa(ex["opcoes"], pares), None
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


def montar_programa(pecas: list[str], pares: list) -> str:
    """Junta as peças na ordem dos pares [índice, nível], indentando 4 espaços por nível."""
    return "\n".join("    " * nivel + pecas[i] for i, nivel in pares)


def combinacoes(pecas: list[str]) -> Iterator[list[tuple[int, int]]]:
    """Todas as combinações ordem+indentação sintaticamente plausíveis (D-06).

    Poda pela gramática do Python, sem executar nada: a primeira linha não é indentada; depois de
    uma linha que termina em ':' o nível sobe exatamente 1; nas demais nunca sobe e pode descer.
    Sem a poda seriam n! x (MAX_NIVEL+1)^n programas."""
    n = len(pecas)

    def rec(usadas: set[int], seq: list[tuple[int, int]]):
        if len(seq) == n:
            yield list(seq)
            return
        for i in range(n):
            if i in usadas:
                continue
            if not seq:
                niveis: range | list = [0]
            else:
                anterior, nivel_ant = seq[-1]
                if pecas[anterior].rstrip().endswith(":"):
                    niveis = [nivel_ant + 1] if nivel_ant + 1 <= MAX_NIVEL else []
                else:
                    niveis = range(nivel_ant + 1)
            for nivel in niveis:
                seq.append((i, nivel))
                usadas.add(i)
                yield from rec(usadas, seq)
                seq.pop()
                usadas.discard(i)

    yield from rec(set(), [])


def metrica_d(ex: dict, executor: Executor = executar) -> tuple[bool | None, str | None]:
    """(d) só para ordenar_linhas. Conta as combinações ordem+indentação que executam e dão a
    saída esperada: o exercício só vale se existir exatamente UMA (D-06)."""
    if ex["tipo"] != "ordenar_linhas":
        return None, None
    pecas = ex["opcoes"]
    if len(pecas) > MAX_PECAS:
        return False, f"mais de {MAX_PECAS} peças: não dá para provar a unicidade"
    esperado = normalizar(ex["saida_esperada"])
    vistos: dict[str, bool] = {}
    for combo in combinacoes(pecas):
        codigo = montar_programa(pecas, combo)
        if codigo in vistos:
            continue
        try:
            ast.parse(codigo)
        except SyntaxError:
            continue  # não é programa; não precisa executar
        if len(vistos) >= MAX_EXECUCOES:
            return False, f"mais de {MAX_EXECUCOES} combinações executáveis: ambíguo demais"
        res = executor(codigo)
        vistos[codigo] = res.ok and normalizar(res.stdout) == esperado
    validas = sum(vistos.values())
    if validas != 1:
        return False, f"{validas} combinações de ordem e indentação válidas (esperado exatamente 1)"
    return True, None
