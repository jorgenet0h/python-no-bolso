"""GET /exercicios (REQ-001 a 004, 006)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import device_id
from app.enums import NIVEIS, TEMAS, TIPOS
from app.errors import FiltroInvalido, SemExercicio
from app.models import Exercicio, Tentativa

router = APIRouter()

_PERMITIDOS = {"tipo": TIPOS, "nivel": NIVEIS, "tema": TEMAS}


def _filtros(request: Request) -> dict[str, str]:
    """Filtros opcionais; valor fora do enum, vazio ou repetido é FILTRO_INVALIDO (REQ-002)."""
    filtros = {}
    for campo, permitidos in _PERMITIDOS.items():
        valores = request.query_params.getlist(campo)
        if not valores:
            continue
        if len(valores) > 1 or valores[0] not in permitidos:
            raise FiltroInvalido(f"Filtro '{campo}' inválido. Use um dos valores permitidos.")
        filtros[campo] = valores[0]
    return filtros


def _publico(ex: Exercicio) -> dict:
    # Só estes campos saem; gabarito, saida_esperada e explicações ficam no servidor (REQ-004).
    return {"id": str(ex.id), "tipo": ex.tipo, "nivel": ex.nivel, "tema": ex.tema,
            "enunciado": ex.enunciado, "codigo": ex.codigo, "opcoes": ex.opcoes}


@router.get("/exercicios")
def obter_exercicio(request: Request, device: Annotated[str, Depends(device_id)],
                    sessao: Annotated[Session, Depends(get_session)]):
    filtros = _filtros(request)
    base = select(Exercicio).where(Exercicio.status == "validado")
    for campo, valor in filtros.items():
        base = base.where(getattr(Exercicio, campo) == valor)

    # Prioriza os que o aparelho ainda não acertou; se não sobrar nenhum, repete (D-13).
    acertados = select(Tentativa.exercicio_id).where(
        Tentativa.device_id == device, Tentativa.correta.is_(True))
    ex = sessao.scalars(
        base.where(Exercicio.id.not_in(acertados)).order_by(func.random()).limit(1)).first()
    if ex is None:
        ex = sessao.scalars(base.order_by(func.random()).limit(1)).first()
    if ex is None:
        raise SemExercicio()
    return _publico(ex)
