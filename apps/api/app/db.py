"""Banco: engine, sessão e Base declarativa.

URL: TEST_DATABASE_URL (testes) > DATABASE_URL > SQLite em memória. Postgres em produção;
o esquema de produção vem do Alembic (PR de migrações); `criar_tabelas_sqlite` é só para dev/teste.
"""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or "sqlite://"
    # Neon/Render entregam "postgresql://"; o driver instalado é o psycopg 3.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _criar_engine():
    url = _url()
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        opcoes: dict = {"connect_args": {"check_same_thread": False}}
        if parsed.database in (None, "", ":memory:"):
            opcoes["poolclass"] = StaticPool  # memória compartilhada entre conexões e threads
        return create_engine(url, **opcoes)
    return create_engine(url, pool_pre_ping=True)


engine = _criar_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Dependência FastAPI. Os testes a sobrescrevem para simular banco fora do ar (REQ-035)."""
    with SessionLocal() as sessao:
        yield sessao


def criar_tabelas_sqlite() -> None:
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
