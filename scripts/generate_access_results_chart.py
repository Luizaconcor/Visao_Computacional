"""Script utilitário para gerar o gráfico dos logs de acesso.

Serve para testar a geração do relatório fora da interface web.
"""

import os
import sqlite3

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_chart(
    db_path: str = "database/evento.db",
    output_image: str = "app/static/generated/grafico_logs_resultado.png",
):
    """
    Gera um gráfico de barras com a quantidade de ocorrências
    de cada tipo de resultado registrado na tabela logs_acesso.

    Parâmetros:
        db_path: caminho do banco de dados SQLite.
        output_image: caminho onde a imagem do gráfico será salva.
    """

    # Converte os caminhos relativos em caminhos absolutos,
    # evitando problemas caso o script seja executado de outra pasta.
    db_path = os.path.abspath(db_path)
    output_image = os.path.abspath(output_image)

    # Garante que a pasta onde a imagem será salva exista.
    # Se não existir, ela será criada automaticamente.
    os.makedirs(os.path.dirname(output_image), exist_ok=True)

    # Abre conexão com o banco de dados SQLite.
    conn = sqlite3.connect(db_path)

    # Consulta SQL:
    # - seleciona o campo "resultado"
    # - conta quantas vezes cada resultado aparece
    # - agrupa pelo resultado
    # - ordena do maior para o menor número de ocorrências
    query = """
        SELECT resultado, COUNT(*) AS quantidade
        FROM logs_acesso
        GROUP BY resultado
        ORDER BY quantidade DESC, resultado ASC
    """

    # Executa a consulta e armazena o resultado em um DataFrame do pandas.
    df = pd.read_sql_query(query, conn)

    # Fecha a conexão com o banco após a leitura.
    conn.close()

    # Se o DataFrame estiver vazio, significa que não há registros
    # na tabela logs_acesso.
    if df.empty:
        # Cria uma figura vazia com tamanho 8x5.
        fig = plt.figure(figsize=(8, 5))

        # Escreve uma mensagem no centro da imagem.
        plt.text(
            0.5,
            0.5,
            "Sem dados em logs_acesso",
            ha="center",
            va="center",
            fontsize=14
        )

        # Remove os eixos para deixar a imagem mais limpa.
        plt.axis("off")

        # Adiciona título ao gráfico.
        plt.title("Distribuição de resultados dos logs de acesso")

        # Salva a imagem gerada no caminho definido.
        fig.savefig(output_image, bbox_inches="tight")

        # Fecha a figura para liberar memória.
        plt.close(fig)

        # Exibe mensagem no terminal informando onde a imagem foi salva.
        print(f"Sem dados. Gráfico vazio salvo em: {output_image}")
        return

    # Caso existam dados, cria uma nova figura para o gráfico de barras.
    fig = plt.figure(figsize=(9, 5))

    # Gera o gráfico de barras:
    # eixo X -> valores da coluna "resultado"
    # eixo Y -> valores da coluna "quantidade"
    plt.bar(df["resultado"], df["quantidade"])

    # Define o título do gráfico, incluindo o total geral de registros.
    plt.title(
        f"Distribuição de resultados dos logs de acesso "
        f"(total: {int(df['quantidade'].sum())})"
    )

    # Nome do eixo X.
    plt.xlabel("Resultado")

    # Nome do eixo Y.
    plt.ylabel("Quantidade")

    # Rotaciona os rótulos do eixo X para melhorar a leitura.
    plt.xticks(rotation=20)

    # Ajusta automaticamente os espaçamentos da figura.
    plt.tight_layout()

    # Salva a imagem com boa resolução.
    fig.savefig(output_image, dpi=200, bbox_inches="tight")

    # Fecha a figura para evitar consumo desnecessário de memória.
    plt.close(fig)

    # Exibe mensagem no terminal indicando sucesso.
    print(f"Gráfico salvo em: {output_image}")


# Este bloco garante que a função será executada apenas
# se o arquivo for rodado diretamente.
# Se ele for importado em outro arquivo, essa parte não será executada.
if __name__ == "__main__":
    generate_chart()