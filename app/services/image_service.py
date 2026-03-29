import os
import re
import base64
import cv2
import numpy as np
from werkzeug.utils import secure_filename


# Verifica se um nome de arquivo possui extensão permitida.
def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


# Salva um arquivo enviado por formulário tradicional.
def save_image(file_storage, upload_folder, code):
    os.makedirs(upload_folder, exist_ok=True)
    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    filename = f"{code}.{extension}"
    file_path = os.path.join(upload_folder, filename)
    file_storage.save(file_path)
    return file_path


# Converte uma data URL base64 em imagem OpenCV.
def _decode_data_url(data_url: str) -> np.ndarray:
    if "," not in data_url:
        raise ValueError("Imagem base64 inválida.")

    header, encoded = data_url.split(",", 1)
    if not re.match(r"^data:image\/[a-zA-Z0-9.+-]+;base64$", header):
        raise ValueError("Formato da imagem capturada é inválido.")

    encoded = encoded.strip().replace(" ", "+")
    missing_padding = len(encoded) % 4
    if missing_padding:
        encoded += "=" * (4 - missing_padding)

    try:
        image_bytes = base64.b64decode(encoded, validate=False)
    except Exception as exc:
        raise ValueError("Base64 da imagem é inválido.") from exc

    np_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Não foi possível decodificar a imagem capturada pela câmera.")

    return image


# Salva a imagem usando escrita binária para evitar falhas do cv2.imwrite
# em caminhos do Windows com caracteres especiais.
def _write_image_unicode_safe(file_path: str, image: np.ndarray) -> None:
    success, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not success or encoded is None:
        raise ValueError("Não foi possível codificar a imagem capturada em JPEG.")

    try:
        with open(file_path, "wb") as f:
            f.write(encoded.tobytes())
    except Exception as exc:
        raise ValueError(f"Não foi possível gravar a imagem no disco: {file_path}") from exc

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError(f"Arquivo da imagem foi criado de forma inválida: {file_path}")


# Salva uma imagem capturada pelo navegador em formato base64.
def save_base64_image(data_url: str, upload_folder: str, code: str, suffix: str = "live") -> str:
    upload_folder = os.path.abspath(upload_folder)
    os.makedirs(upload_folder, exist_ok=True)

    image = _decode_data_url(data_url)
    if image.size == 0:
        raise ValueError("Imagem capturada vazia.")

    filename = f"{code}_{suffix}.jpg"
    file_path = os.path.abspath(os.path.join(upload_folder, filename))

    _write_image_unicode_safe(file_path, image)
    return file_path
