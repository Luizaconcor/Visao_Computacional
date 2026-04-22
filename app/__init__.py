"""Inicialização da aplicação Flask.

Este arquivo monta o app, carrega configurações, cria a estrutura mínima
do projeto e registra os componentes principais.
"""

import os
from flask import Flask
from app.config import Config
from app.db import close_db
from scripts.create_tables import create_tables


# Factory principal da aplicação Flask.
# Centraliza a criação do app, o carregamento das configurações
# e o registro dos componentes essenciais.
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Garante as pastas mínimas antes de qualquer operação.
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Garante a criação do banco e das tabelas em ambientes novos,
    # como deploy em hospedagem ou primeira execução local.
    create_tables(app.config["DATABASE_PATH"])

    # Registra as rotas definidas no blueprint principal.
    from app.routes import main
    app.register_blueprint(main)

    # Garante que a conexão com o banco seja encerrada ao final da requisição.
    app.teardown_appcontext(close_db)
    return app
