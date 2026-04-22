"""Rotas web e fluxo principal do sistema de controle facial.

Aqui ficam as páginas, o processamento dos formulários e a integração com
os serviços de imagem, banco e verificação facial.
"""

import os
from flask import Blueprint, render_template, request, current_app

from app.services.id_service import generate_code
from app.services.image_service import save_base64_image
from app.services.verification_service import compare_faces_by_path
from app.models.participante_model import (
    inserir_participante,
    buscar_por_cpf,
    buscar_todos_participantes,
)
from app.models.acesso_model import registrar_log
from app.db import get_db

# Blueprint principal: agrupa as rotas públicas da aplicação.
main = Blueprint("main", __name__)


def _ensure_reports_folder() -> str:
    # Garante a pasta onde os gráficos do relatório serão gravados.
    project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
    reports_dir = os.path.join(project_root, "app", "static", "generated")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def _gerar_dados_relatorio():
    # Consulta o banco e agrega os logs por tipo de resultado.
    db = get_db()
    rows = db.execute(
        """
        SELECT resultado, COUNT(*) AS quantidade
        FROM logs_acesso
        GROUP BY resultado
        ORDER BY quantidade DESC, resultado ASC
        """
    ).fetchall()

    dados = [{"resultado": row["resultado"], "quantidade": row["quantidade"]} for row in rows]
    total = sum(item["quantidade"] for item in dados)
    return dados, total


def _gerar_grafico_logs():
    # Gera um PNG com a distribuição dos resultados de acesso.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dados, total = _gerar_dados_relatorio()
    reports_dir = _ensure_reports_folder()
    image_path = os.path.join(reports_dir, "grafico_logs_resultado.png")

    fig = plt.figure(figsize=(9, 5))

    if not dados:
        plt.text(0.5, 0.5, "Sem dados em logs_acesso", ha="center", va="center", fontsize=14)
        plt.axis("off")
        plt.title("Distribuição de resultados dos logs de acesso")
    else:
        labels = [item["resultado"] for item in dados]
        values = [item["quantidade"] for item in dados]
        plt.bar(labels, values)
        plt.title(f"Distribuição de resultados dos logs de acesso (total: {total})")
        plt.xlabel("Resultado")
        plt.ylabel("Quantidade")
        plt.xticks(rotation=20)
        plt.tight_layout()

    fig.savefig(image_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    return "generated/grafico_logs_resultado.png", dados, total


# Resolve caminhos de imagens salvos no banco.
# Isso ajuda quando o projeto muda de pasta ou quando há caminhos relativos.
def _resolve_image_path(path: str) -> str | None:
    if not path:
        return None
    if os.path.isabs(path) and os.path.exists(path):
        return path

    project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
    candidates = [
        path,
        os.path.join(project_root, path),
        os.path.join(current_app.root_path, path),
    ]

    for candidate in candidates:
        candidate = os.path.abspath(candidate)
        if os.path.exists(candidate):
            return candidate

    return os.path.abspath(os.path.join(project_root, path))


@main.route("/", methods=["GET"])
def index():
    return render_template("cadastro.html")


@main.route("/cadastro", methods=["GET"])
def cadastro_page():
    return render_template("cadastro.html")


@main.route("/verificacao", methods=["GET"])
def verificacao_page():
    return render_template("verificacao.html")


@main.route("/relatorios/logs", methods=["GET"])
def relatorio_logs():
    grafico_path, dados, total = _gerar_grafico_logs()
    return render_template(
        "relatorio_logs.html",
        grafico_path=grafico_path,
        dados=dados,
        total=total,
    )


@main.route("/cadastro", methods=["POST"])
def cadastro():
    # Recebe os dados do formulário de cadastro e salva um novo participante.
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    cpf = request.form.get("cpf", "").strip()
    telefone = request.form.get("telefone", "").strip()
    foto_base64 = request.form.get("foto_base64", "").strip()

    # Validação mínima: sem todos os campos, o cadastro não prossegue.
    if not nome or not email or not cpf or not telefone or not foto_base64:
        return "Todos os campos são obrigatórios, inclusive a foto capturada pela câmera.", 400

    # Evita duplicidade de cadastro usando o CPF como referência única.
    participante_existente = buscar_por_cpf(cpf)
    if participante_existente:
        return "CPF já cadastrado.", 400

    code = generate_code()
    foto_path = None

    try:
        # Primeiro salvamos a foto capturada para então persistir o cadastro.
        foto_path = save_base64_image(
            data_url=foto_base64,
            upload_folder=current_app.config["UPLOAD_FOLDER"],
            code=code,
            suffix="cadastro"
        )

        participante_id = inserir_participante(
            codigo_uuid=code,
            nome=nome,
            email=email,
            cpf=cpf,
            telefone=telefone,
            foto_path=foto_path,
            selfie_captura_path=foto_path,
            verificado_liveness=1,
            score_verificacao=None,
            status_verificacao="foto_capturada"
        )

        return render_template(
            "sucesso.html",
            nome=nome,
            codigo=code,
            participante_id=participante_id,
            score=None
        )

    except Exception as e:
        if foto_path and os.path.exists(foto_path):
            os.remove(foto_path)
        return f"Erro ao processar cadastro: {str(e)}", 500


@main.route("/verificar", methods=["POST"])
def verificar():
    # Captura a foto enviada pela tela de verificação e compara com o banco.
    foto_base64 = request.form.get("foto_base64", "").strip()

    if not foto_base64:
        return render_template(
            "resultado_verificacao.html",
            sucesso=False,
            mensagem="Capture uma foto antes de verificar.",
            participante=None,
            detalhe_tecnico=None,
            score=None
        ), 400

    captura_path = None

    try:
        captura_path = save_base64_image(
            data_url=foto_base64,
            upload_folder=current_app.config["UPLOAD_FOLDER"],
            code=generate_code(),
            suffix="verificacao"
        )

        participantes = buscar_todos_participantes()
        if not participantes:
            return render_template(
                "resultado_verificacao.html",
                sucesso=False,
                mensagem="Nenhum participante cadastrado ainda.",
                participante=None,
                detalhe_tecnico=None,
                score=None
            )

        melhor_participante = None
        melhor_resultado = None
        melhor_score = -1.0
        segundo_melhor_score = -1.0

        erros_ignorados = 0
        comparacoes_validas = 0
        mensagens_erro = []

        # Percorre todos os cadastrados para encontrar a maior similaridade.
        for participante in participantes:
            foto_participante = _resolve_image_path(participante["foto_path"])
            if not foto_participante:
                erros_ignorados += 1
                continue

            resultado = compare_faces_by_path(captura_path, foto_participante)
            if not resultado.get("success"):
                erros_ignorados += 1
                if resultado.get("message"):
                    mensagens_erro.append(f"{participante['nome']}: {resultado.get('message')}")
                continue

            comparacoes_validas += 1
            score_atual = resultado.get("score")
            if score_atual is None:
                continue

            if score_atual > melhor_score:
                segundo_melhor_score = melhor_score
                melhor_score = score_atual
                melhor_participante = participante
                melhor_resultado = resultado
            elif score_atual > segundo_melhor_score:
                segundo_melhor_score = score_atual

        margem_minima = 0.08
        score_minimo_unico = 0.75
        score_minimo_geral = 0.67
        diferenca_top2 = melhor_score - segundo_melhor_score if segundo_melhor_score >= 0 else None

        # Regras de decisão: exigimos score mínimo e distância suficiente do 2º colocado.
        aprovado = (
            melhor_participante is not None
            and melhor_resultado is not None
            and melhor_resultado.get("match") is True
            and (
                (comparacoes_validas == 1 and melhor_score >= score_minimo_unico)
                or (
                    comparacoes_validas > 1
                    and melhor_score >= score_minimo_geral
                    and diferenca_top2 is not None
                    and diferenca_top2 >= margem_minima
                )
            )
        )

        success_detail = None
        if melhor_resultado is not None:
            orb_txt = f"{melhor_resultado.get('orb_score'):.4f}" if melhor_resultado.get('orb_score') is not None else "n/a"
            edge_txt = f"{melhor_resultado.get('edge_score'):.4f}" if melhor_resultado.get('edge_score') is not None else "n/a"
            success_detail = (
                f"hist={melhor_resultado.get('hist_score'):.4f}, "
                f"orb={orb_txt}, bordas={edge_txt}"
            )

        if aprovado:
            registrar_log(
                participante_id=melhor_participante["id"],
                nome_detectado=melhor_participante["nome"],
                resultado="liberado",
                score_confianca=melhor_score,
            )
            return render_template(
                "resultado_verificacao.html",
                sucesso=True,
                mensagem=f"Acesso liberado para {melhor_participante['nome']}.",
                participante=melhor_participante,
                detalhe_tecnico=success_detail,
                score=melhor_score,
            )

        mensagem = "Pessoa não cadastrada no sistema."
        detalhe_tecnico = None
        if comparacoes_validas == 0:
            mensagem = "Não foi possível comparar a imagem capturada com as fotos cadastradas."
            if mensagens_erro:
                detalhe_tecnico = " | ".join(mensagens_erro[:3])
        elif melhor_resultado is not None:
            orb_txt = f"{melhor_resultado.get('orb_score'):.4f}" if melhor_resultado.get('orb_score') is not None else "n/a"
            edge_txt = f"{melhor_resultado.get('edge_score'):.4f}" if melhor_resultado.get('edge_score') is not None else "n/a"
            margem_txt = f"{diferenca_top2:.4f}" if diferenca_top2 is not None else "n/a"
            detalhe_tecnico = (
                f"Melhor candidato: {melhor_participante['nome']} | "
                f"hist={melhor_resultado.get('hist_score'):.4f}, "
                f"orb={orb_txt}, bordas={edge_txt}, margem_top2={margem_txt}"
            )

        registrar_log(
            participante_id=None,
            nome_detectado="desconhecido",
            resultado="negado",
            score_confianca=melhor_score if melhor_score >= 0 else None,
        )
        return render_template(
            "resultado_verificacao.html",
            sucesso=False,
            mensagem=mensagem,
            detalhe_tecnico=detalhe_tecnico,
            participante=None,
            score=melhor_score if melhor_score >= 0 else None,
        )

    except Exception as e:
        return render_template(
            "resultado_verificacao.html",
            sucesso=False,
            mensagem=f"Erro na verificação: {str(e)}",
            participante=None,
            detalhe_tecnico=None,
            score=None
        ), 500
    finally:
        if captura_path and os.path.exists(captura_path):
            os.remove(captura_path)
