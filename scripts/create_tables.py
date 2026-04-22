"""Script de criação inicial do banco e das tabelas.

Pode ser executado separadamente para preparar o ambiente do projeto.
"""

import os
import sqlite3
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env quando ele existir.
load_dotenv()


# Cria o banco SQLite e as tabelas necessárias para a aplicação.
# Essa função pode ser reutilizada tanto localmente quanto em produção.
def create_tables(db_path: str | None = None):
    resolved_db_path = db_path or os.getenv("DATABASE_PATH", "database/evento.db")
    resolved_db_path = os.path.abspath(resolved_db_path)

    # Garante a existência da pasta do banco.
    os.makedirs(os.path.dirname(resolved_db_path), exist_ok=True)

    conn = sqlite3.connect(resolved_db_path)
    cursor = conn.cursor()

    # Tabela principal de participantes.
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

    # Tabela de histórico de acessos realizados na portaria.
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
    return resolved_db_path


if __name__ == "__main__":
    created_db = create_tables()
    print(f"Banco SQLite e tabelas criados com sucesso em: {created_db}")
