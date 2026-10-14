"""Carrega os dados do rascunho de novembro/2026. Só roda se o banco estiver vazio."""
import uuid

from sqlalchemy import select

from app.db import Compra, Config, Fixo, SessionLocal, init_db

COMPRAS = [  # nome, categoria, forma, valor da parcela, nº parcelas, mês da 1ª cobrança
    ("Fone Jéssica", "Presentes", "cartao", 56.58, 5, "2026-11"),
    ("Uber Gabriel niver Larisa", "Transporte", "cartao", 39.94, 1, "2026-11"),
    ("Mantiqueira", "Outros", "cartao", 84.54, 1, "2026-11"),
    ("Daiso presentes Gabriel", "Presentes", "cartao", 40.96, 1, "2026-11"),
    ("Presente Larisa", "Presentes", "cartao", 34.97, 2, "2026-11"),
    ("Zé Delivery 10/10", "Alimentação", "cartao", 34.34, 1, "2026-11"),
    ("Daiso cinema", "Lazer", "cartao", 15.00, 1, "2026-11"),
    ("Cinema Resident Evil", "Lazer", "cartao", 74.00, 1, "2026-11"),
    ("Feira asiática Carrefour", "Alimentação", "cartao", 62.00, 1, "2026-11"),
    ("FF VI remake", "Lazer", "cartao", 24.93, 2, "2026-10"),
    ("Faculdade que parcelei", "Educação", "cartao", 390.73, 3, "2026-10"),
    ("Shampoo", "Saúde e higiene", "cartao", 26.28, 2, "2026-10"),
    ("Chinelos SP", "Vestuário", "cartao", 64.99, 2, "2026-10"),
    ("Airbnb SP Gabriel", "Viagem", "cartao", 109.83, 6, "2026-09"),
]
FIXOS = [  # nome, categoria, forma, valor, desde, até
    ("Streamings", "Assinaturas", "cartao", 113.80, None, None),
    ("Amazon Prime", "Assinaturas", "cartao", 13.90, None, None),
    ("TIM", "Contas", "debito", 29.99, None, None),
    ("Faculdade", "Educação", "debito", 1172.21, None, "2026-12"),
]
SALARIO = 3100.00


def main() -> None:
    init_db()
    with SessionLocal() as s:
        if s.scalar(select(Compra).limit(1)) or s.scalar(select(Fixo).limit(1)):
            print("O banco já tem dados; nada foi alterado.")
            return
        s.merge(Config(id=1, salario=SALARIO))
        for nome, cat, forma, parcela, n, inicio in COMPRAS:
            s.add(Compra(id=str(uuid.uuid4()), nome=nome, cat=cat, forma=forma, parcela=parcela, n=n, inicio=inicio))
        for nome, cat, forma, valor, desde, ate in FIXOS:
            s.add(Fixo(id=str(uuid.uuid4()), nome=nome, cat=cat, forma=forma, valor=valor, desde=desde, ate=ate))
        s.commit()
    print(f"Pronto: {len(COMPRAS)} compras, {len(FIXOS)} contas fixas e salário carregados.")


if __name__ == "__main__":
    main()
