"""Serviço simples para geração de identificadores únicos.

Os UUIDs são usados para evitar colisão entre usuários e imagens salvas.
"""

import uuid


# Gera um identificador único para cada participante/captura.
def generate_code():
    return str(uuid.uuid4())
