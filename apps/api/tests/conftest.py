import os

# Antes de importar a app: CORS lê a origem configurada (.env.example).
os.environ.setdefault("CORS_ORIGIN", "http://localhost:3000")

import pytest
from fastapi.testclient import TestClient

from tests.contrato import novo_device


@pytest.fixture(scope="session")
def app():
    from app.main import app as _app

    return _app


@pytest.fixture()
def client(app):
    # raise_server_exceptions=False: queremos ver a resposta 500 do handler global (REQ-034).
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def device() -> str:
    return novo_device()
