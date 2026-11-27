"""Rate limit em memória por aparelho e por IP (REQ-040, D-24): janela deslizante de 60 s.

Em memória de um processo só: suficiente para 1 instância (tier gratuito). Com várias instâncias,
o limite passa a valer por instância; troque por um armazenamento compartilhado se isso importar.
"""

import os
import time
from collections import deque

from starlette.requests import Request

from app.deps import HEADER_DEVICE, UUID_RE
from app.errors import LimiteExcedido

JANELA_S = 60
LIMITE_DEVICE = 120
LIMITE_IP = 300
ROTAS_SEM_LIMITE = {"/health"}
_MAX_CHAVES = 10_000

_acessos: dict[str, deque[float]] = {}


def resetar() -> None:
    _acessos.clear()


def ip_do_cliente(request: Request) -> str:
    """IP da conexão. X-Forwarded-For só é lido com TRUST_PROXY=1, e usa a ÚLTIMA entrada, a que o
    proxy confiável acrescentou; as anteriores podem ser forjadas pelo cliente."""
    if os.environ.get("TRUST_PROXY") == "1":
        encaminhado = request.headers.get("x-forwarded-for", "")
        ultimo = encaminhado.split(",")[-1].strip()
        if ultimo:
            return ultimo
    return request.client.host if request.client else "desconhecido"


def _estourou(chave: str, limite: int, agora: float) -> bool:
    fila = _acessos.setdefault(chave, deque())
    while fila and agora - fila[0] >= JANELA_S:
        fila.popleft()
    fila.append(agora)
    return len(fila) > limite


def _limpar(agora: float) -> None:
    for chave in [k for k, f in _acessos.items() if not f or agora - f[-1] >= JANELA_S]:
        del _acessos[chave]


def excedeu(request: Request) -> bool:
    if request.url.path in ROTAS_SEM_LIMITE:
        return False
    agora = time.monotonic()
    if len(_acessos) > _MAX_CHAVES:
        _limpar(agora)
    por_ip = _estourou(f"ip:{ip_do_cliente(request)}", LIMITE_IP, agora)
    device = request.headers.get(HEADER_DEVICE, "")
    por_device = False
    if UUID_RE.fullmatch(device):  # header inválido nem vira chave: não enche a memória
        por_device = _estourou(f"dev:{device.lower()}", LIMITE_DEVICE, agora)
    return por_ip or por_device


def resposta_limite():
    from fastapi.responses import JSONResponse

    e = LimiteExcedido()
    return JSONResponse(status_code=e.status_code, content={"code": e.code, "message": e.message},
                        headers={"Retry-After": str(JANELA_S)})
