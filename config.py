import os
import sqlite3


def get_local_db_path():
    return os.path.join(os.path.dirname(__file__), "dados.db")


def criar_tabelas_local():
    """
    Usado apenas no desenvolvimento, para criar as tabelas locais
    caso o banco ainda não exista.
    """
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()

    # 🔹 Tabela clientes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente TEXT PRIMARY KEY,
            nome TEXT,
            cpf TEXT,
            telefone TEXT,
            endereco TEXT,
            cidade TEXT,
            indicacao TEXT
        )
    """)

    # 🔹 Tabela emprestimos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emprestimos (
            id TEXT PRIMARY KEY,
            id_cliente TEXT,
            valor TEXT,
            data_inicio TEXT,
            parcelas TEXT,
            observacao TEXT
        )
    """)

    # 🔹 Tabela parcelas
        # 🔹 Tabela parcelas (atualizada com novos campos)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parcelas (
            id TEXT PRIMARY KEY,
            id_emprestimo TEXT,
            numero TEXT,
            valor TEXT,
            vencimento TEXT,
            juros TEXT,
            desconto TEXT,
            parcela_atualizada TEXT,
            valor_pago TEXT,
            residual TEXT,
            pago TEXT,
            data_pagamento TEXT
        )
    """)


    # 🔹 Tabela movimentacoes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id TEXT PRIMARY KEY,
            tipo TEXT,
            valor TEXT,
            data TEXT,
            descricao TEXT,
            id_relacionado TEXT,
            origem TEXT
        )
    """)

    conn.commit()
    conn.close()


def verificar_tabelas():
    """
    Usado no dia a dia: apenas checa se as tabelas mínimas existem.
    Se faltar alguma, gera erro e o programa não continua.
    """
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()

    esperadas = ["clientes", "emprestimos", "parcelas", "movimentacoes"]

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existentes = {row[0] for row in cur.fetchall()}

    faltando = [t for t in esperadas if t not in existentes]
    conn.close()

    if faltando:
        raise RuntimeError(f"⚠ Banco local inválido! Tabelas ausentes: {faltando}")
    else:
        print("✅ Banco local OK, todas as tabelas estão presentes.")
