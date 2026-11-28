"""Validador de exercícios gerados por modelo (REQ-025, 026, 030).

Nunca confia no que o modelo afirma: confere o schema ANTES de qualquer execução e depois executa o
código por conta própria (via `executor`, injetado; em produção, `app.sandbox.executar`).
"""

import ast
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from jsonschema import Draft202012Validator

from app.enums import NIVEIS, TEMAS, TIPOS

MAX_PECAS = 6
MAX_NIVEL = 3  # níveis de indentação em ordenar_linhas (D-06)
MAX_EXECUCOES = 400  # teto de programas executados para provar a unicidade (D-08)

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["tipo", "nivel", "tema", "enunciado", "codigo", "opcoes", "gabarito",
                 "saida_esperada", "explicacao", "explicacoes_por_opcao"],
    "properties": {
        "tipo": {"enum": list(TIPOS)},
        "nivel": {"enum": list(NIVEIS)},
        "tema": {"enum": list(TEMAS)},
        "enunciado": {"type": "string", "minLength": 5, "maxLength": 500},
        "codigo": {"type": "string", "maxLength": 2000},
        "codigo_corrigido": {"type": "string", "minLength": 1, "maxLength": 2000},
        "opcoes": {"type": "array", "minItems": 2, "maxItems": 6,
                   "items": {"type": "string", "minLength": 1, "maxLength": 200}},
        "gabarito": {"type": "array", "minItems": 1, "maxItems": 6},
        "saida_esperada": {"type": "string", "maxLength": 500},
        "explicacao": {"type": "string", "minLength": 5, "maxLength": 1000},
        "explicacoes_por_opcao": {"type": "object",
                                  "additionalProperties": {"type": "string", "maxLength": 500}},
    },
    "allOf": [
        {"if": {"properties": {"tipo": {"const": "achar_bug"}}},
         "then": {"required": ["codigo_corrigido"]}},
        {"if": {"properties": {"tipo": {"const": "ordenar_linhas"}}},
         "then": {"properties": {"gabarito": {"minItems": 2, "items": {
             "type": "array", "minItems": 2, "maxItems": 2,
             "prefixItems": [{"type": "integer", "minimum": 0, "maximum": 5},
                             {"type": "integer", "minimum": 0, "maximum": MAX_NIVEL}]}}}},
         "else": {"properties": {"gabarito": {"items": {"type": "integer", "minimum": 0,
                                                         "maximum": 5}}}}},
    ],
}
_VALIDADOR = Draft202012Validator(SCHEMA)

Executor = Callable[..., object]  # executor(codigo) -> objeto com ok, stdout, stderr, motivo


@dataclass
class Resultado:
    aprovado: bool
    motivo: str | None = None


def _reprovar(motivo: str) -> Resultado:
    return Resultado(False, motivo)


def normalizar(saida: str) -> str:
    """Ignora espaço no fim de linha e linhas vazias no fim (D-22)."""
    return "\n".join(linha.rstrip() for linha in saida.splitlines()).rstrip("\n")


def montar_programa(pecas: list[str], pares: list) -> str:
    return "\n".join("    " * nivel + pecas[i] for i, nivel in pares)


def checar_schema(candidato: object) -> str | None:
    """Motivo da reprovação, ou None. Inclui as checagens que o JSON Schema não expressa."""
    if not isinstance(candidato, dict):
        return "schema: o candidato não é um objeto"
    try:
        erros = sorted(_VALIDADOR.iter_errors(candidato), key=lambda e: list(e.path))
    except Exception:  # noqa: BLE001 - candidato hostil nunca derruba o validador
        return "schema: candidato ilegível"
    if erros:
        erro = erros[0]
        return f"schema: {'/'.join(map(str, erro.path)) or 'raiz'}: {erro.message[:100]}"
    n, gab, tipo = len(candidato["opcoes"]), candidato["gabarito"], candidato["tipo"]
    if tipo == "ordenar_linhas":
        if sorted(p[0] for p in gab) != list(range(n)):
            return "schema: gabarito de ordenar_linhas não é uma permutação das peças"
    else:
        if len(gab) != 1 or not 0 <= gab[0] < n:
            return "schema: gabarito fora do intervalo das opções"
        if tipo == "completar_lacuna" and "___" not in candidato["codigo"]:
            return "schema: completar_lacuna sem a lacuna no código"
    return None


def _combinacoes(pecas: list[str]) -> Iterator[list[tuple[int, int]]]:
    """Combinações ordem+indentação plausíveis, podadas pela gramática do Python (D-08): 1ª linha
    sem indentar; depois de linha terminada em dois pontos o nível sobe 1; nas demais nunca sobe."""
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


def _rodar(executor: Executor, codigo: str):
    try:
        return executor(codigo)
    except Exception:  # noqa: BLE001 - falha do executor reprova, não derruba o chamador
        return None


def _confere(res, esperado: str) -> bool:
    return bool(res is not None and res.ok and normalizar(res.stdout) == esperado)


def _validar_ordenar(ex: dict, executor: Executor, esperado: str) -> Resultado:
    pecas = ex["opcoes"]
    if len(pecas) > MAX_PECAS:
        return _reprovar(f"mais de {MAX_PECAS} peças: não dá para provar a unicidade")
    vistos: dict[str, bool] = {}
    gab = montar_programa(pecas, ex["gabarito"])
    vistos[gab] = _confere(_rodar(executor, gab), esperado)
    if not vistos[gab]:
        return _reprovar("divergência: o gabarito não produz a saída afirmada")
    for combo in _combinacoes(pecas):
        codigo = montar_programa(pecas, combo)
        if codigo in vistos:
            continue
        try:
            ast.parse(codigo)
        except (SyntaxError, ValueError):
            continue  # não é programa; não precisa executar
        if len(vistos) >= MAX_EXECUCOES:
            return _reprovar(f"mais de {MAX_EXECUCOES} combinações executáveis: ambíguo demais")
        vistos[codigo] = _confere(_rodar(executor, codigo), esperado)
    validas = sum(vistos.values())
    if validas != 1:
        return _reprovar(
            f"{validas} combinações de ordem e indentação válidas (esperado exatamente 1)")
    return Resultado(True)


def validar(candidato: object, *, executor: Executor) -> Resultado:
    motivo = checar_schema(candidato)
    if motivo:
        return _reprovar(motivo)
    esperado = normalizar(candidato["saida_esperada"])
    tipo = candidato["tipo"]

    if tipo == "ordenar_linhas":
        return _validar_ordenar(candidato, executor, esperado)

    if tipo == "achar_bug":
        if candidato["codigo"].strip() == candidato["codigo_corrigido"].strip():
            return _reprovar("o código com defeito é idêntico à correção")
        corrigido = _rodar(executor, candidato["codigo_corrigido"])
        if not _confere(corrigido, esperado):
            return _reprovar("divergência: a versão corrigida não produz a saída afirmada")
        defeito = _rodar(executor, candidato["codigo"])
        if _confere(defeito, esperado):
            return _reprovar("o código com defeito já produz a saída esperada (não há bug)")
        return Resultado(True)

    codigo = candidato["codigo"]
    if tipo == "completar_lacuna":
        codigo = codigo.replace("___", candidato["opcoes"][candidato["gabarito"][0]])
    res = _rodar(executor, codigo)
    if res is None or not res.ok:
        return _reprovar("o código de referência não executou com sucesso")
    if normalizar(res.stdout) != esperado:
        return _reprovar("divergência entre a saída real e a afirmada pelo modelo")
    return Resultado(True)
