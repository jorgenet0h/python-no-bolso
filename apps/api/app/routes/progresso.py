"""GET /progresso (REQ-015, 016): derivado de `tentativas`, sem tabela de usuário."""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import device_id
from app.enums import TIPOS
from app.models import Exercicio, Tentativa

router = APIRouter()

FUSO = ZoneInfo("America/Sao_Paulo")


def _dia(momento: datetime) -> date:
    if momento.tzinfo is None:  # SQLite devolve sem fuso; o que gravamos é UTC
        momento = momento.replace(tzinfo=UTC)
    return momento.astimezone(FUSO).date()


def sequencia_de_dias(momentos: list[datetime], hoje: date) -> int:
    """Dias seguidos com prática, terminando hoje ou ontem (D-12). Um dia inteiro em branco zera."""
    dias = {_dia(m) for m in momentos}
    dia = hoje if hoje in dias else hoje - timedelta(days=1)
    total = 0
    while dia in dias:
        total += 1
        dia -= timedelta(days=1)
    return total


@router.get("/progresso")
def progresso(device: Annotated[str, Depends(device_id)],
              sessao: Annotated[Session, Depends(get_session)]):
    por_tipo = sessao.execute(
        select(Exercicio.tipo, func.count(Tentativa.id),
               func.sum(case((Tentativa.correta.is_(True), 1), else_=0)))
        .join(Exercicio, Exercicio.id == Tentativa.exercicio_id)
        .where(Tentativa.device_id == device)
        .group_by(Exercicio.tipo)).all()
    contagem = {tipo: (int(total), int(acertos or 0)) for tipo, total, acertos in por_tipo}
    momentos = list(sessao.scalars(select(Tentativa.criado_em).where(Tentativa.device_id == device)))
    return {
        "total_acertos": sum(a for _, a in contagem.values()),
        # Os quatro tipos sempre presentes; sem tentativas, taxa 0.
        "taxa_por_tipo": {t: (contagem[t][1] / contagem[t][0] if t in contagem else 0.0)
                          for t in TIPOS},
        "sequencia_dias": sequencia_de_dias(momentos, datetime.now(FUSO).date()),
    }
