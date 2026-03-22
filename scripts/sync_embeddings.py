"""Exemplo simples de preparação futura para embeddings.

Nesta versão, o script apenas lista participantes aprovados.
Vocês podem trocar depois pela geração real de embeddings com DeepFace.
"""

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

db_path = os.getenv("DATABASE_PATH", "database/evento.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT id, nome, foto_path, status_verificacao FROM participantes WHERE status_verificacao = 'aprovado'"
).fetchall()

for row in rows:
    print(f"[{row['id']}] {row['nome']} -> {row['foto_path']} ({row['status_verificacao']})")

conn.close()
