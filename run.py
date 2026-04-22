"""Ponto de entrada local da aplicação Flask.

Expõe a variável `app` e permite iniciar o servidor em modo de desenvolvimento.
"""

from app import create_app

# Instância principal da aplicação.
app = create_app()

if __name__ == "__main__":
    # Execução local para desenvolvimento.
    app.run(debug=True, host="0.0.0.0", port=5000)
