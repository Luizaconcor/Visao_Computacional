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

main = Blueprint("main", __name__)


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


# Página inicial: redireciona visualmente para a tela de cadastro.
@main.route("/", methods=["GET"])
def index():
    return render_template("cadastro.html")


# Página de formulário de cadastro.
@main.route("/cadastro", methods=["GET"])
def cadastro_page():
    return render_template("cadastro.html")


# Página de verificação facial na entrada do evento.
@main.route("/verificacao", methods=["GET"])
def verificacao_page():
    return render_template("verificacao.html")


# Recebe os dados do formulário e salva o participante no banco.
@main.route("/cadastro", methods=["POST"])
def cadastro():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    cpf = request.form.get("cpf", "").strip()
    telefone = request.form.get("telefone", "").strip()
    foto_base64 = request.form.get("foto_base64", "").strip()

    if not nome or not email or not cpf or not telefone or not foto_base64:
        return "Todos os campos são obrigatórios, inclusive a foto capturada pela câmera.", 400

    participante_existente = buscar_por_cpf(cpf)
    if participante_existente:
        return "CPF já cadastrado.", 400

    code = generate_code()
    foto_path = None

    try:
        # Salva a foto capturada pelo navegador na pasta de uploads.
        foto_path = save_base64_image(
            data_url=foto_base64,
            upload_folder=current_app.config["UPLOAD_FOLDER"],
            code=code,
            suffix="cadastro"
        )

        # Persiste os dados principais do participante.
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
        # Se algo falhar após salvar a imagem, remove o arquivo para evitar lixo.
        if foto_path and os.path.exists(foto_path):
            os.remove(foto_path)
        return f"Erro ao processar cadastro: {str(e)}", 500


# Recebe uma imagem ao vivo e compara com todos os participantes cadastrados.
@main.route("/verificar", methods=["POST"])
def verificar():
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
        # Salva temporariamente a foto da verificação.
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
        melhor_score = -1.0

        erros_ignorados = 0
        comparacoes_validas = 0
        mensagens_erro = []

        # Percorre todos os participantes e mantém o maior score encontrado.
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

            if resultado.get("score") is not None and resultado["score"] > melhor_score:
                melhor_score = resultado["score"]
                melhor_participante = participante

        # Score mínimo adotado para liberar a pessoa na demonstração.
        aprovado = melhor_participante is not None and melhor_score >= 0.53

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
                detalhe_tecnico=None,
                score=melhor_score,
            )

        mensagem = "Pessoa não cadastrada no sistema."
        detalhe_tecnico = None
        if comparacoes_validas == 0:
            mensagem = "Não foi possível comparar a imagem capturada com as fotos cadastradas."
            if mensagens_erro:
                detalhe_tecnico = " | ".join(mensagens_erro[:3])

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
        # Remove a imagem temporária da verificação para não acumular arquivos.
        if captura_path and os.path.exists(captura_path):
            os.remove(captura_path)
