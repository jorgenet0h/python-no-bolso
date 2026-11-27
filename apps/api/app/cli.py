"""CLI administrativa (REQ-024): a geração em lote só acontece aqui, nunca por requisição de usuário.

Uso:  python -m app.cli gerar --tipo prever_saida --nivel iniciante --tema variaveis --minimo 5
"""

import argparse
import sys

from sqlalchemy import func, select

from app import sandbox
from app.agent.loop import gerar
from app.db import SessionLocal
from app.errors import ErroDominio
from app.models import Exercicio

TENTATIVAS_POR_UNIDADE = 3  # no máximo `minimo` x 3 execuções por lote (D-21)


def _estoque(tipo: str, nivel: str, tema: str) -> int:
    with SessionLocal() as sessao:
        return sessao.scalar(
            select(func.count()).select_from(Exercicio).where(
                Exercicio.status == "validado", Exercicio.tipo == tipo,
                Exercicio.nivel == nivel, Exercicio.tema == tema)) or 0


def gerar_lote(tipo: str, nivel: str, tema: str, minimo: int, provedor, executor=None) -> dict:
    """Gera até o estoque validado de (tipo, nivel, tema) chegar a `minimo`. Estoque já no mínimo:
    não chama o modelo. Devolve um resumo {estoque, execucoes, aprovados}."""
    executor = executor or sandbox.executar
    execucoes = aprovados = 0
    limite = max(minimo, 0) * TENTATIVAS_POR_UNIDADE
    while _estoque(tipo, nivel, tema) < minimo and execucoes < limite:
        execucoes += 1
        if gerar(tipo, nivel, tema, provedor=provedor, executor=executor).status == "aprovado":
            aprovados += 1
    return {"estoque": _estoque(tipo, nivel, tema), "execucoes": execucoes, "aprovados": aprovados}


def main(argv: list[str] | None = None) -> int:
    from app.config import ConfiguracaoInvalida, carregar_provedor

    p = argparse.ArgumentParser(prog="app.cli")
    sub = p.add_subparsers(dest="comando", required=True)
    g = sub.add_parser("gerar", help="gera exercícios até o estoque mínimo")
    g.add_argument("--tipo", required=True)
    g.add_argument("--nivel", required=True)
    g.add_argument("--tema", required=True)
    g.add_argument("--minimo", type=int, required=True)
    args = p.parse_args(argv)
    try:
        provedor = carregar_provedor()
    except ConfiguracaoInvalida as e:
        print(f"configuração inválida: {e}", file=sys.stderr)
        return 2
    try:
        resumo = gerar_lote(args.tipo, args.nivel, args.tema, args.minimo, provedor)
    except ErroDominio as e:
        print(f"{e.code}: {e.message}", file=sys.stderr)
        return 2
    print(resumo)
    return 0 if resumo["estoque"] >= args.minimo else 1


if __name__ == "__main__":
    sys.exit(main())
