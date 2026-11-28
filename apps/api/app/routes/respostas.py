"""POST /respostas (REQ-007 a 011)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.correcao import esta_correta, ler_corpo, validar_resposta
from app.db import get_session
from app.deps import device_id
from app.errors import ExercicioNaoEncontrado
from app.models import Exercicio, Tentativa

router = APIRouter()


async def _corpo(request: Request) -> dict:
    return ler_corpo(await request.body())


@router.post("/respostas")
def responder(corpo: Annotated[dict, Depends(_corpo)], device: Annotated[str, Depends(device_id)],
              sessao: Annotated[Session, Depends(get_session)]):
    ex = sessao.get(Exercicio, corpo["exercicio_id"])
    if ex is None or ex.status != "validado":
        raise ExercicioNaoEncontrado()
    resposta = corpo["resposta"]
    validar_resposta(ex.tipo, len(ex.opcoes), resposta)

    correta = esta_correta(ex.gabarito, resposta)
    sessao.add(Tentativa(device_id=device, exercicio_id=ex.id, resposta=resposta, correta=correta))
    sessao.commit()

    explicacao = ex.explicacao
    if not correta and ex.tipo != "ordenar_linhas":
        # Explicação armazenada da opção escolhida, na hora (REQ-011, D-17); sem ela, a geral.
        explicacao = (ex.explicacoes_por_opcao or {}).get(str(resposta[0])) or ex.explicacao
    return {"correta": correta, "explicacao": explicacao}
