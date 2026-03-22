from app.db import get_db


def inserir_participante(
    codigo_uuid,
    nome,
    email,
    cpf,
    telefone,
    foto_path,
    selfie_captura_path,
    verificado_liveness,
    score_verificacao,
    status_verificacao,
):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO participantes (
            codigo_uuid, nome, email, cpf, telefone,
            foto_path, selfie_captura_path,
            verificado_liveness, score_verificacao, status_verificacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            codigo_uuid,
            nome,
            email,
            cpf,
            telefone,
            foto_path,
            selfie_captura_path,
            verificado_liveness,
            score_verificacao,
            status_verificacao,
        ),
    )

    db.commit()
    return cursor.lastrowid



def buscar_por_cpf(cpf):
    db = get_db()
    cursor = db.execute("SELECT * FROM participantes WHERE cpf = ?", (cpf,))
    return cursor.fetchone()



def listar_participantes():
    db = get_db()
    cursor = db.execute("SELECT * FROM participantes")
    return cursor.fetchall()



def buscar_todos_participantes():
    db = get_db()
    cursor = db.execute(
        """
        SELECT id, nome, codigo_uuid, cpf, foto_path, selfie_captura_path, status_verificacao
        FROM participantes
        ORDER BY id DESC
        """
    )
    return cursor.fetchall()
