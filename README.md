# Meus gastos

Página de acompanhamento de gastos + API em FastAPI. A API serve a própria página em `/`,
então é um serviço só, sem CORS.

## Rodar local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export FINANCAS_TOKEN=uma-chave-qualquer
python seed.py            # opcional: carrega os dados de nov/2026 (só se o banco estiver vazio)
uvicorn app.main:app --reload
```

Abra http://localhost:8000 e entre com o valor de `FINANCAS_TOKEN`.
Documentação da API: http://localhost:8000/docs · Testes: `pytest`

## Hospedar (Docker)

```bash
cp .env.example .env      # e troque a chave
docker compose up -d --build
docker compose exec financas python seed.py   # opcional
```

O compose publica só em `127.0.0.1:8000`. Coloque um proxy com HTTPS na frente
(Caddy, Nginx ou o do seu provedor). **Não exponha sem HTTPS**: a chave vai em todo request.

Exemplo de `Caddyfile`:

```
gastos.seudominio.com.br {
    reverse_proxy 127.0.0.1:8000
}
```

O banco SQLite fica no volume `dados`. Para backup: `docker compose cp financas:/data/financas.db .`

## Endpoints

Todos em `/api` exigem `Authorization: Bearer <FINANCAS_TOKEN>`, exceto `/api/health`.

| Método | Rota | O que faz |
|---|---|---|
| GET | `/api/estado` | salário, compras e contas fixas |
| PUT | `/api/salario` | `{"salario": 3100}` |
| POST · PUT · DELETE | `/api/compras[/{id}]` | `nome, cat, forma (cartao/debito), parcela, n, inicio (AAAA-MM)` |
| POST · PUT · DELETE | `/api/fixos[/{id}]` | `nome, cat, forma, valor, desde?, ate?` |

As parcelas não são guardadas uma a uma: cada compra guarda o mês da 1ª cobrança e o nº de
parcelas, e a página calcula em qual parcela você está em cada mês.
