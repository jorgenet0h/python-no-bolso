"""Validação e correção determinística da resposta (REQ-007 a 010). Nenhum texto livre, nenhum modelo."""

import json
import uuid

from app.errors import RespostaInvalida

MAX_INDENT = 3  # níveis de indentação em ordenar_linhas (D-06)


def _inteiro(x) -> bool:
    return type(x) is int  # bool é subclasse de int, mas não vale como número aqui


def _rejeitar_constante(_nome):
    raise ValueError("NaN e Infinity não são JSON válido")


def ler_corpo(bruto: bytes) -> dict:
    """Corpo JSON {exercicio_id, resposta} com formato geral válido; senão RESPOSTA_INVALIDA."""
    try:
        corpo = json.loads(bruto.decode("utf-8"), parse_constant=_rejeitar_constante)
    except (ValueError, RecursionError):  # inclui UnicodeDecodeError e JSONDecodeError
        raise RespostaInvalida() from None
    if not isinstance(corpo, dict):
        raise RespostaInvalida()
    resposta = corpo.get("resposta")
    if not isinstance(resposta, list) or not resposta:
        raise RespostaInvalida()
    if all(_inteiro(i) for i in resposta):
        pass  # índices
    elif all(isinstance(p, list) and len(p) == 2 and all(_inteiro(n) for n in p) for p in resposta):
        pass  # pares [índice, indentação]
    else:
        raise RespostaInvalida()
    return {"exercicio_id": _uuid(corpo.get("exercicio_id")), "resposta": resposta}


def _uuid(valor) -> uuid.UUID:
    if not isinstance(valor, str) or len(valor) != 36:
        raise RespostaInvalida()
    try:
        return uuid.UUID(valor)
    except ValueError:
        raise RespostaInvalida() from None


def validar_resposta(tipo: str, n_opcoes: int, resposta: list) -> None:
    """Confere a resposta contra o tipo do exercício. Levanta RespostaInvalida."""
    if tipo == "ordenar_linhas":
        if len(resposta) != n_opcoes or not all(isinstance(p, list) for p in resposta):
            raise RespostaInvalida()
        indices = [p[0] for p in resposta]
        if sorted(indices) != list(range(n_opcoes)):
            raise RespostaInvalida()
        if not all(0 <= p[1] <= MAX_INDENT for p in resposta):
            raise RespostaInvalida()
        return
    if len(resposta) != 1 or not _inteiro(resposta[0]) or not 0 <= resposta[0] < n_opcoes:
        raise RespostaInvalida()


def esta_correta(gabarito: list, resposta: list) -> bool:
    return [list(x) if isinstance(x, list) else x for x in gabarito] == resposta
