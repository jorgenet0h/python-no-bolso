"""Dependências compartilhadas das rotas."""

import re

from fastapi import Request

from app.errors import DeviceInvalido

HEADER_DEVICE = "X-Device-Id"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def device_id(request: Request) -> str:
    """UUID válido de qualquer versão no header X-Device-Id; ausente ou malformado é
    DEVICE_INVALIDO (REQ-018, D-16). Nunca ecoa o valor recebido."""
    valor = request.headers.get(HEADER_DEVICE)
    if not valor or not UUID_RE.fullmatch(valor):
        raise DeviceInvalido()
    return valor.lower()
