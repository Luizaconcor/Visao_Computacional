"""Configurações centralizadas da aplicação.

Concentra caminhos, limites e segredos lidos do ambiente para evitar
valores fixos espalhados pelo projeto.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env, quando existir.
load_dotenv()

# Caminho base do projeto para facilitar a montagem de paths absolutos.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    # Chave secreta usada pelo Flask em recursos internos de segurança.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    # Local do banco SQLite.
    DATABASE_PATH = os.path.abspath(
        os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "database", "evento.db"))
    )

    # Pasta onde as imagens capturadas serão salvas.
    UPLOAD_FOLDER = os.path.abspath(
        os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads", "fotos"))
    )

    # Limite máximo de upload aceito pela aplicação.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5242880))

    # Extensões suportadas quando houver upload por arquivo.
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
