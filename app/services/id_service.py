import uuid


# Gera um identificador único para cada participante/captura.
def generate_code():
    return str(uuid.uuid4())
