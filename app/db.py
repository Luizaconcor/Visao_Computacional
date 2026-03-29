import os
import sqlite3
from flask import current_app, g


# Retorna a conexão SQLite da requisição atual.
# Se ainda não existir, cria uma nova conexão e a guarda em g.
def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


# Fecha a conexão com o banco ao final da requisição.
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
