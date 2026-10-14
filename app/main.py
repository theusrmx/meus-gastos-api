"""API do app Meus gastos. Serve também a página em /."""
import os
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Compra, Config, Fixo, get_session, init_db

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

Mes = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-11"])]
Forma = Literal["cartao", "debito"]
Valor = Annotated[float, Field(gt=0, le=10_000_000)]


# ---------- autenticação: uma chave só, definida em FINANCAS_TOKEN ----------
_bearer = HTTPBearer(auto_error=False)


def autenticar(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    esperado = os.environ["FINANCAS_TOKEN"].encode()
    if cred is None or not secrets.compare_digest(cred.credentials.encode(), esperado):
        raise HTTPException(401, "Chave de acesso inválida", headers={"WWW-Authenticate": "Bearer"})


# ---------- esquemas ----------
class CompraIn(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    cat: str = Field(min_length=1, max_length=40)
    forma: Forma
    parcela: Valor
    n: int = Field(default=1, ge=1, le=48)
    inicio: Mes

    @model_validator(mode="after")
    def _debito_sem_parcelas(self):
        if self.forma == "debito" and self.n != 1:
            raise ValueError("Compras no débito/Pix têm uma parcela só")
        return self


class FixoIn(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    cat: str = Field(min_length=1, max_length=40)
    forma: Forma
    valor: Valor
    desde: Mes | None = None
    ate: Mes | None = None

    @model_validator(mode="after")
    def _periodo_valido(self):
        if self.desde and self.ate and self.desde > self.ate:
            raise ValueError("'desde' precisa ser antes de 'ate'")
        return self


class CompraOut(CompraIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class FixoOut(FixoIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class SalarioIn(BaseModel):
    salario: float = Field(ge=0, le=10_000_000)


class Estado(BaseModel):
    salario: float
    compras: list[CompraOut]
    fixos: list[FixoOut]


# ---------- app ----------
@asynccontextmanager
async def lifespan(_: FastAPI):
    if not os.getenv("FINANCAS_TOKEN"):
        raise RuntimeError("Defina a variável de ambiente FINANCAS_TOKEN antes de subir a API.")
    init_db()
    yield


app = FastAPI(title="Meus gastos", lifespan=lifespan)
api = APIRouter(prefix="/api", dependencies=[Depends(autenticar)])
SessionDep = Annotated[Session, Depends(get_session)]


def _config(s: Session) -> Config:
    cfg = s.get(Config, 1)
    if cfg is None:
        cfg = Config(id=1, salario=0)
        s.add(cfg)
        s.flush()
    return cfg


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@api.get("/estado", response_model=Estado)
def estado(s: SessionDep):
    return Estado(
        salario=_config(s).salario,
        compras=s.scalars(select(Compra).order_by(Compra.inicio, Compra.nome)).all(),
        fixos=s.scalars(select(Fixo).order_by(Fixo.nome)).all(),
    )


@api.put("/salario", response_model=SalarioIn)
def definir_salario(dados: SalarioIn, s: SessionDep):
    _config(s).salario = dados.salario
    s.commit()
    return dados


def _crud(prefixo: str, Modelo, Entrada, Saida) -> APIRouter:
    r = APIRouter(prefix=prefixo)

    @r.post("", response_model=Saida, status_code=201)
    def criar(dados: Entrada, s: SessionDep):
        obj = Modelo(id=str(uuid.uuid4()), **dados.model_dump())
        s.add(obj)
        s.commit()
        return obj

    @r.put("/{item_id}", response_model=Saida)
    def atualizar(item_id: str, dados: Entrada, s: SessionDep):
        obj = s.get(Modelo, item_id)
        if obj is None:
            raise HTTPException(404, "Item não encontrado")
        for campo, valor in dados.model_dump().items():
            setattr(obj, campo, valor)
        s.commit()
        return obj

    @r.delete("/{item_id}", status_code=204)
    def excluir(item_id: str, s: SessionDep):
        obj = s.get(Modelo, item_id)
        if obj is None:
            raise HTTPException(404, "Item não encontrado")
        s.delete(obj)
        s.commit()
        return Response(status_code=204)

    return r


api.include_router(_crud("/compras", Compra, CompraIn, CompraOut))
api.include_router(_crud("/fixos", Fixo, FixoIn, FixoOut))
app.include_router(api)

# A página fica na raiz; precisa vir depois das rotas da API.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
