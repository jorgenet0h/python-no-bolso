import os
import sys

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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """D-23: no CI em Linux nenhum teste pode ser pulado. Os de memória e fork bomb só rodam em
    Linux; se alguém os pular lá (por exemplo, por rlimit ausente), o CI tem de falhar, não passar."""
    outcome = yield
    rep = outcome.get_result()
    if rep.skipped and os.environ.get("CI") and sys.platform == "linux":
        rep.outcome = "failed"
        rep.longrepr = f"SKIP PROIBIDO NO CI (Linux): {item.nodeid}: {rep.longrepr}"
