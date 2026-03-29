from app.db import get_db


# Registra no histórico se o acesso foi liberado ou negado.
def registrar_log(participante_id, nome_detectado, resultado, score_confianca):
    db = get_db()
    db.execute(
        """
        INSERT INTO logs_acesso (participante_id, nome_detectado, resultado, score_confianca)
        VALUES (?, ?, ?, ?)
        """,
        (participante_id, nome_detectado, resultado, score_confianca),
    )
    db.commit()
