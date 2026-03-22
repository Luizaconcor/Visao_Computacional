import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

db_path = os.getenv("DATABASE_PATH", "database/evento.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS participantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_uuid TEXT NOT NULL UNIQUE,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        cpf TEXT NOT NULL UNIQUE,
        telefone TEXT NOT NULL,
        foto_path TEXT NOT NULL,
        selfie_captura_path TEXT,
        embedding_path TEXT,
        verificado_liveness INTEGER DEFAULT 0,
        score_verificacao REAL,
        status_verificacao TEXT DEFAULT 'pendente',
        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS logs_acesso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participante_id INTEGER,
        nome_detectado TEXT,
        resultado TEXT NOT NULL,
        score_confianca REAL,
        data_hora TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (participante_id) REFERENCES participantes(id)
    )
    """
)

conn.commit()
conn.close()

print("Banco SQLite e tabelas criados com sucesso.")
