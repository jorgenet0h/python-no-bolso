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


@pytest.fixture(autouse=True)
def _isolamento():
    """Banco vazio e rate limit zerado a cada teste (contrato: app.db.engine/Base e
    app.ratelimit.resetar, ver docs/spec-gaps.md). Sem esses módulos é no-op: o teste que
    precisa deles falha com NAO-IMPLEMENTADO, não aqui."""
    import importlib

    try:
        db = importlib.import_module("app.db")
    except ModuleNotFoundError as e:
        if e.name not in ("app.db", "app"):
            raise
        db = None
    if db is not None and hasattr(db, "engine") and hasattr(db, "Base"):
        with db.engine.begin() as con:
            for tabela in reversed(db.Base.metadata.sorted_tables):
                con.execute(tabela.delete())
    try:
        importlib.import_module("app.ratelimit").resetar()
    except (ModuleNotFoundError, AttributeError):
        pass
    yield
