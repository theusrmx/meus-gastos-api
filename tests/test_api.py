import os
import tempfile

os.environ["FINANCAS_TOKEN"] = "teste-123"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

AUTH = {"Authorization": "Bearer teste-123"}


def test_sem_chave_da_401():
    with TestClient(app) as c:
        assert c.get("/api/estado").status_code == 401
        assert c.get("/api/estado", headers={"Authorization": "Bearer errada"}).status_code == 401


def test_pagina_e_health_sao_publicas():
    with TestClient(app) as c:
        assert c.get("/api/health").json() == {"ok": True}
        assert "Meus gastos" in c.get("/").text


def test_fluxo_completo():
    with TestClient(app) as c:
        assert c.put("/api/salario", json={"salario": 3100}, headers=AUTH).status_code == 200
        r = c.post("/api/compras", headers=AUTH, json={
            "nome": "Airbnb", "cat": "Viagem", "forma": "cartao", "parcela": 109.83, "n": 6, "inicio": "2026-09"})
        assert r.status_code == 201
        cid = r.json()["id"]
        r = c.post("/api/fixos", headers=AUTH, json={
            "nome": "Faculdade", "cat": "Educação", "forma": "debito", "valor": 1172.21, "ate": "2026-12"})
        assert r.status_code == 201 and r.json()["desde"] is None

        est = c.get("/api/estado", headers=AUTH).json()
        assert est["salario"] == 3100 and len(est["compras"]) == 1 and len(est["fixos"]) == 1

        r = c.put(f"/api/compras/{cid}", headers=AUTH, json={
            "nome": "Airbnb SP", "cat": "Viagem", "forma": "cartao", "parcela": 109.83, "n": 6, "inicio": "2026-09"})
        assert r.json()["nome"] == "Airbnb SP"
        assert c.delete(f"/api/compras/{cid}", headers=AUTH).status_code == 204
        assert c.delete(f"/api/compras/{cid}", headers=AUTH).status_code == 404


def test_validacoes():
    with TestClient(app) as c:
        base = {"nome": "X", "cat": "Lazer", "forma": "debito", "parcela": 10, "n": 3, "inicio": "2026-11"}
        assert c.post("/api/compras", headers=AUTH, json=base).status_code == 422  # débito parcelado
        assert c.post("/api/compras", headers=AUTH, json={**base, "n": 1, "inicio": "2026-13"}).status_code == 422
        assert c.post("/api/compras", headers=AUTH, json={**base, "n": 1, "parcela": -5}).status_code == 422
        fx = {"nome": "Y", "cat": "Contas", "forma": "debito", "valor": 10, "desde": "2027-01", "ate": "2026-12"}
        assert c.post("/api/fixos", headers=AUTH, json=fx).status_code == 422
