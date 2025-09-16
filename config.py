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
            indicacao TEXT,
            id_usuario TEXT
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
            observacao TEXT,
            juros TEXT,
            prestacao TEXT,
            id_usuario TEXT,
            ativo TEXT DEFAULT 'sim'
        )
    """)

    # 🔹 Tabela parcelas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parcelas (
            id TEXT PRIMARY KEY,
            id_emprestimo TEXT,
            numero TEXT,
            valor TEXT,
            vencimento TEXT,
            juros TEXT,
            desconto TEXT,
            pg_principal TEXT,
            pg_juros TEXT,
            valor_pago TEXT,
            residual TEXT,
            data_pagamento TEXT,
            id_usuario TEXT,
            data_prevista TEXT,
            comentario TEXT
        )
    """)

    # 🔹 Tabela garantias
    cur.execute("""
        CREATE TABLE IF NOT EXISTS garantias (
            id TEXT PRIMARY KEY,
            id_cliente TEXT,
            descricao TEXT,
            valor TEXT,
            id_usuario TEXT
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

    esperadas = ["clientes", "emprestimos", "parcelas", "garantias"]

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existentes = {row[0] for row in cur.fetchall()}

    faltando = [t for t in esperadas if t not in existentes]
    conn.close()

    if faltando:
        raise RuntimeError(f"⚠ Banco local inválido! Tabelas ausentes: {faltando}")
