import logging
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models  # noqa: F401  (registra as tabelas)
from app.db import get_session
from app.errors import ErroDominio, Indisponivel, RespostaInvalida
from app.routes import exercicios, progresso, respostas

log = logging.getLogger("app")

app = FastAPI(title="Python no Bolso API")
app.include_router(exercicios.router)
app.include_router(respostas.router)
app.include_router(progresso.router)

HEALTH_OK = {"status": "ok", "db": "ok"}
HEALTH_DEGRADADO = {"status": "degraded", "db": "erro"}


def _erro(status: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "message": message, **extra})


@app.exception_handler(ErroDominio)
async def _erro_dominio(_: Request, exc: ErroDominio):
    return _erro(exc.status_code, exc.code, exc.message)


@app.exception_handler(StarletteHTTPException)
async def _erro_http(_: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return _erro(404, "NAO_ENCONTRADO", "Rota não encontrada.")
    if exc.status_code == 405:
        return _erro(405, "METODO_NAO_PERMITIDO", "Método não permitido.")
    return _erro(exc.status_code, "ERRO_INTERNO", "Não foi possível concluir a requisição.")


@app.exception_handler(RequestValidationError)
async def _erro_validacao(_: Request, __: RequestValidationError):
    # Nunca devolve `loc`, `input` nem detalhes do pydantic (REQ-033).
    e = RespostaInvalida()
    return _erro(e.status_code, e.code, e.message)


async def _banco_fora(request: Request, _: Exception):
    # /health responde o formato do REQ-044; as demais rotas, INDISPONIVEL (REQ-035).
    if request.url.path == "/health":
        return JSONResponse(status_code=503, content=HEALTH_DEGRADADO)
    e = Indisponivel()
    return _erro(e.status_code, e.code, e.message)


app.add_exception_handler(DBAPIError, _banco_fora)  # inclui OperationalError
app.add_exception_handler(ConnectionError, _banco_fora)


@app.exception_handler(Exception)
async def _erro_imprevisto(request: Request, exc: Exception):
    correlacao_id = uuid.uuid4().hex
    # Stack trace só no log, com o mesmo id devolvido ao cliente (REQ-034, D-15).
    log.error("erro imprevisto correlacao_id=%s %s %s", correlacao_id, request.method,
              request.url.path, exc_info=exc)
    return _erro(500, "ERRO_INTERNO", "Erro interno. Informe o código ao suporte.",
                 correlacao_id=correlacao_id)


@app.get("/health")
def health(sessao: Annotated[Session, Depends(get_session)]):
    sessao.execute(text("SELECT 1"))
    return HEALTH_OK
