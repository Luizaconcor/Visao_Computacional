"""Funções de verificação facial usando dlib.

Esta versão usa o detector HOG do dlib para localizar o rosto e o modelo
ResNet do dlib para gerar um descritor facial de 128 dimensões. A comparação
é feita pela distância euclidiana entre os descritores.

É uma implementação acadêmica/didática, não uma solução biométrica pronta para
produção.
"""

import os

import cv2
import numpy as np

try:
    import dlib
    import face_recognition_models
except ImportError as exc:  # erro amigável quando as dependências faltarem
    dlib = None
    face_recognition_models = None
    _DLIB_IMPORT_ERROR = exc
else:
    _DLIB_IMPORT_ERROR = None


# Limiar clássico do dlib/face_recognition: distância <= 0.60 indica que as
# imagens provavelmente são da mesma pessoa. Valores menores são mais rígidos.
DLIB_DISTANCE_THRESHOLD = float(os.getenv("DLIB_DISTANCE_THRESHOLD", "0.60"))

# Aumentar a imagem uma vez melhora a detecção em fotos pequenas, mantendo
# desempenho aceitável para um projeto acadêmico.
DLIB_UPSAMPLE_TIMES = int(os.getenv("DLIB_UPSAMPLE_TIMES", "1"))

_dlib_detector = None
_dlib_shape_predictor = None
_dlib_face_encoder = None


# Inicializa os modelos do dlib apenas quando forem usados.
def _ensure_dlib_models():
    global _dlib_detector, _dlib_shape_predictor, _dlib_face_encoder

    if _DLIB_IMPORT_ERROR is not None:
        raise RuntimeError(
            "Dependências do dlib não instaladas. Execute: "
            "pip install -r requirements.txt"
        ) from _DLIB_IMPORT_ERROR

    if _dlib_detector is None:
        _dlib_detector = dlib.get_frontal_face_detector()

    if _dlib_shape_predictor is None:
        predictor_path = face_recognition_models.pose_predictor_five_point_model_location()
        _dlib_shape_predictor = dlib.shape_predictor(predictor_path)

    if _dlib_face_encoder is None:
        model_path = face_recognition_models.face_recognition_model_location()
        _dlib_face_encoder = dlib.face_recognition_model_v1(model_path)


# Carrega uma imagem do disco, inclusive em caminhos com caracteres especiais.
def _load_image(path: str):
    if not path or not os.path.exists(path):
        raise ValueError(f"Imagem não encontrada: {path}")

    try:
        data = np.fromfile(path, dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise ValueError(f"Erro ao ler imagem: {path}") from exc

    if image is None:
        raise ValueError(f"Imagem inválida ou não pôde ser lida: {path}")

    return image


# Gera um recorte central apenas para visualização/fallback controlado.
def _central_crop(image, scale: float = 0.7):
    h, w = image.shape[:2]
    cw, ch = int(w * scale), int(h * scale)
    x1 = max((w - cw) // 2, 0)
    y1 = max((h - ch) // 2, 0)
    x2 = min(x1 + cw, w)
    y2 = min(y1 + ch, h)
    crop = image[y1:y2, x1:x2]
    return crop if crop.size else image


# Converte retângulo do dlib para recorte OpenCV com margem.
def _crop_dlib_rect(image, rect, padding_ratio: float = 0.18):
    h, w = image.shape[:2]

    x = max(rect.left(), 0)
    y = max(rect.top(), 0)
    x2 = min(rect.right(), w - 1)
    y2 = min(rect.bottom(), h - 1)

    face_w = max(x2 - x, 1)
    face_h = max(y2 - y, 1)
    pad = int(min(face_w, face_h) * padding_ratio)

    x1 = max(x - pad, 0)
    y1 = max(y - pad, 0)
    x2 = min(x2 + pad, w)
    y2 = min(y2 + pad, h)

    face = image[y1:y2, x1:x2]
    return face if face.size else _central_crop(image)


# Detecta o rosto principal com dlib.
def _detect_main_face_rect(image_rgb):
    _ensure_dlib_models()

    detections = _dlib_detector(image_rgb, DLIB_UPSAMPLE_TIMES)
    if not detections:
        raise ValueError("Nenhum rosto detectado pelo dlib na imagem.")

    # Seleciona o maior rosto detectado, útil quando há mais de uma pessoa.
    return max(detections, key=lambda r: r.width() * r.height())


# Extrai a face principal a partir de um array de imagem.
def _detect_single_face(image):
    if image is None or image.size == 0:
        raise ValueError("Imagem inválida para detecção.")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rect = _detect_main_face_rect(image_rgb)
    return _crop_dlib_rect(image, rect)


# Gera o descritor facial de 128 dimensões do dlib.
def _face_descriptor_from_image(image):
    if image is None or image.size == 0:
        raise ValueError("Imagem inválida para extração de descritor facial.")

    _ensure_dlib_models()

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rect = _detect_main_face_rect(image_rgb)
    shape = _dlib_shape_predictor(image_rgb, rect)
    descriptor = _dlib_face_encoder.compute_face_descriptor(image_rgb, shape)

    return np.array(descriptor, dtype=np.float32)


# Converte distância do dlib em score amigável entre 0 e 1.
def _distance_to_score(distance: float) -> float:
    # Fórmula suave: distância 0.00 => 1.00; distância 0.60 => ~0.625.
    # Assim o score continua legível na tela sem perder o limiar técnico.
    return float(max(0.0, min(1.0, 1.0 / (1.0 + distance))))


# Compara dois descritores dlib.
def _face_similarity_details(descriptor1, descriptor2):
    distance = float(np.linalg.norm(descriptor1 - descriptor2))
    score = _distance_to_score(distance)
    verified = distance <= DLIB_DISTANCE_THRESHOLD

    return {
        "score": score,
        "dlib_distance": distance,
        "dlib_score": score,
        "match": verified,
    }


# Extrai a face principal a partir de um caminho no disco.
def extract_face_from_path(image_path: str):
    image = _load_image(image_path)
    return _detect_single_face(image)


# Extrai o descritor facial dlib a partir de um caminho no disco.
def extract_descriptor_from_path(image_path: str):
    image = _load_image(image_path)
    return _face_descriptor_from_image(image)


# Compara duas imagens faciais já salvas no disco.
def compare_faces_by_path(image_path_1: str, image_path_2: str):
    try:
        descriptor1 = extract_descriptor_from_path(image_path_1)
        descriptor2 = extract_descriptor_from_path(image_path_2)
        metrics = _face_similarity_details(descriptor1, descriptor2)

        return {
            "success": True,
            "match": metrics["match"],
            "message": "Faces correspondem." if metrics["match"] else "Faces não correspondem.",
            "score": metrics["score"],
            "dlib_score": metrics["dlib_score"],
            "dlib_distance": metrics["dlib_distance"],
            "liveness_ok": True,
        }
    except Exception as e:
        return {
            "success": False,
            "match": False,
            "message": str(e),
            "score": None,
            "dlib_score": None,
            "dlib_distance": None,
            "liveness_ok": False,
        }


# Usa a mesma lógica de comparação para validar se a pessoa do cadastro
# realmente corresponde à imagem enviada no momento da captura.
def verify_registration_person(live_image_path: str, selfie_image_path: str) -> dict:
    result = compare_faces_by_path(live_image_path, selfie_image_path)

    if not result["success"]:
        return {
            "success": False,
            "message": result.get("message", "Não foi possível validar o cadastro facial."),
            "score": result.get("score"),
            "liveness_ok": False,
        }

    if not result.get("match"):
        return {
            "success": False,
            "message": "Cadastro facial não corresponde à pessoa da câmera.",
            "score": result.get("score"),
            "liveness_ok": True,
        }

    return {
        "success": True,
        "message": "Cadastro facial validado com sucesso usando dlib.",
        "score": result.get("score"),
        "liveness_ok": True,
    }
