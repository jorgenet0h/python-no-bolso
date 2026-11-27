"""Modelo de dados (docs/arquitetura.md)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, criar_tabelas_sqlite

Json = JSON().with_variant(JSONB(), "postgresql")


def _agora() -> datetime:
    return datetime.now(UTC)


class ExecucaoGeracao(Base):
    __tablename__ = "execucoes_geracao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(32))
    nivel: Mapped[str] = mapped_column(String(32))
    tema: Mapped[str] = mapped_column(String(32))
    modelo: Mapped[str | None] = mapped_column(String(100), default=None)
    provedor: Mapped[str | None] = mapped_column(String(50), default=None)
    status: Mapped[str] = mapped_column(String(16))  # aprovado | rejeitado | falhou
    motivo: Mapped[str | None] = mapped_column(Text, default=None)
    passos: Mapped[int] = mapped_column(Integer, default=0)
    duracao_ms: Mapped[int] = mapped_column(Integer, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class Exercicio(Base):
    __tablename__ = "exercicios"
    __table_args__ = (Index("ix_exercicios_filtro", "status", "tipo", "nivel", "tema"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(32))
    nivel: Mapped[str] = mapped_column(String(32))
    tema: Mapped[str] = mapped_column(String(32))
    enunciado: Mapped[str] = mapped_column(Text)
    codigo: Mapped[str] = mapped_column(Text, default="")
    codigo_corrigido: Mapped[str | None] = mapped_column(Text, default=None)  # só achar_bug (D-07)
    opcoes: Mapped[list] = mapped_column(Json)
    gabarito: Mapped[list] = mapped_column(Json)
    saida_esperada: Mapped[str] = mapped_column(Text)
    explicacao: Mapped[str] = mapped_column(Text)
    explicacoes_por_opcao: Mapped[dict] = mapped_column(Json, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="validado")  # validado | arquivado
    geracao_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("execucoes_geracao.id"), default=None)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class Tentativa(Base):
    __tablename__ = "tentativas"
    __table_args__ = (Index("ix_tentativas_device_criado", "device_id", "criado_em"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    exercicio_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exercicios.id"))
    # Índices; pares [índice, indentação] em ordenar_linhas.
    resposta: Mapped[list] = mapped_column(Json)
    correta: Mapped[bool] = mapped_column(Boolean)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


class PassoGeracao(Base):
    __tablename__ = "passos_geracao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execucao_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("execucoes_geracao.id"))
    n: Mapped[int] = mapped_column(Integer)
    tool: Mapped[str | None] = mapped_column(String(50), default=None)
    modelo: Mapped[str | None] = mapped_column(String(100), default=None)
    entrada_resumo: Mapped[str | None] = mapped_column(Text, default=None)
    resultado_resumo: Mapped[str | None] = mapped_column(Text, default=None)
    duracao_ms: Mapped[int] = mapped_column(Integer, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)


criar_tabelas_sqlite()
