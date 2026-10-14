"""Conexão com o banco e modelos (SQLAlchemy 2)."""
import os
from collections.abc import Iterator

from sqlalchemy import Integer, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financas.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

# Numeric no banco (sem erro de arredondamento), float na API.
Dinheiro = Numeric(12, 2, asdecimal=False)


class Base(DeclarativeBase):
    pass


class Config(Base):
    __tablename__ = "config"

    id: Mapped[int] = mapped_column(primary_key=True)
    salario: Mapped[float] = mapped_column(Dinheiro, default=0)


class Compra(Base):
    """Compra única ou parcelada. `inicio` é o mês da 1ª cobrança (AAAA-MM)."""

    __tablename__ = "compras"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    cat: Mapped[str] = mapped_column(String(40))
    forma: Mapped[str] = mapped_column(String(10))  # "cartao" | "debito"
    parcela: Mapped[float] = mapped_column(Dinheiro)
    n: Mapped[int] = mapped_column(Integer, default=1)
    inicio: Mapped[str] = mapped_column(String(7), index=True)


class Fixo(Base):
    """Conta que se repete todo mês, com início e fim opcionais (AAAA-MM)."""

    __tablename__ = "fixos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    cat: Mapped[str] = mapped_column(String(40))
    forma: Mapped[str] = mapped_column(String(10))
    valor: Mapped[float] = mapped_column(Dinheiro)
    desde: Mapped[str | None] = mapped_column(String(7), nullable=True)
    ate: Mapped[str | None] = mapped_column(String(7), nullable=True)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
