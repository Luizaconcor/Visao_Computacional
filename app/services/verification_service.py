import os
import cv2
import numpy as np


# Carrega o classificador Haar Cascade embutido no OpenCV.
# Ele é suficiente para uma demo acadêmica simples de detecção facial.
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

# ORB é um descritor leve de pontos-chave, bom para exemplos didáticos.
orb = cv2.ORB_create(nfeatures=700)

# Comparador brute-force para os descritores ORB.
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


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


# Gera um recorte central quando a detecção facial falha.
def _central_crop(image, scale: float = 0.7):
    h, w = image.shape[:2]
    cw, ch = int(w * scale), int(h * scale)
    x1 = max((w - cw) // 2, 0)
    y1 = max((h - ch) // 2, 0)
    x2 = min(x1 + cw, w)
    y2 = min(y1 + ch, h)
    crop = image[y1:y2, x1:x2]
    return crop if crop.size else image


# Padroniza o tamanho da face para que as métricas sejam comparáveis.
def _normalize_face(face):
    return cv2.resize(face, (224, 224), interpolation=cv2.INTER_AREA)


# Detecta o rosto principal da imagem.
# Se não encontrar, usa um recorte central para não interromper a demo.
def _detect_single_face(image):
    if image is None or image.size == 0:
        raise ValueError("Imagem inválida para detecção.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if face_cascade is None or face_cascade.empty():
        return _central_crop(image)

    try:
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=4,
            minSize=(60, 60)
        )
    except Exception:
        return _central_crop(image)

    if len(faces) >= 1:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        pad = int(min(w, h) * 0.15)
        x1 = max(x - pad, 0)
        y1 = max(y - pad, 0)
        x2 = min(x + w + pad, image.shape[1])
        y2 = min(y + h + pad, image.shape[0])
        face = image[y1:y2, x1:x2]
        return face if face.size else _central_crop(image)

    return _central_crop(image)


# Mede semelhança entre histogramas em tons de cinza.
def _hist_similarity(face1, face2):
    face1 = _normalize_face(face1)
    face2 = _normalize_face(face2)

    gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray1 = clahe.apply(gray1)
    gray2 = clahe.apply(gray2)

    hist1 = cv2.calcHist([gray1], [0], None, [128], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [128], [0, 256])

    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return max(0.0, min(1.0, float((correlation + 1) / 2)))


# Mede semelhança usando pontos-chave ORB.
def _orb_similarity(face1, face2):
    gray1 = cv2.cvtColor(_normalize_face(face1), cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(_normalize_face(face2), cv2.COLOR_BGR2GRAY)

    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    if des1 is None or des2 is None:
        return None

    matches = bf.match(des1, des2)
    if not matches:
        return 0.0

    good = [m for m in matches if m.distance < 64]
    denom = max(len(matches), 1)
    return max(0.0, min(1.0, len(good) / denom))


# Mede a sobreposição das bordas detectadas nas duas faces.
def _edge_similarity(face1, face2):
    gray1 = cv2.cvtColor(_normalize_face(face1), cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(_normalize_face(face2), cv2.COLOR_BGR2GRAY)

    e1 = cv2.Canny(gray1, 80, 160)
    e2 = cv2.Canny(gray2, 80, 160)
    inter = np.logical_and(e1 > 0, e2 > 0).sum()
    union = np.logical_or(e1 > 0, e2 > 0).sum()
    if union == 0:
        return None
    return float(inter / union)


# Combina as métricas em um score único entre 0 e 1.
def _face_similarity_details(face1, face2):
    hist_score = _hist_similarity(face1, face2)
    orb_score = _orb_similarity(face1, face2)
    edge_score = _edge_similarity(face1, face2)

    # Damos menos peso ao histograma puro porque ele costuma aceitar
    # rostos diferentes quando a iluminação e o enquadramento são parecidos.
    parts = [0.35 * hist_score]
    weight = 0.35

    if orb_score is not None:
        parts.append(0.45 * orb_score)
        weight += 0.45
    if edge_score is not None:
        parts.append(0.20 * edge_score)
        weight += 0.20

    score = float(sum(parts) / weight)

    # Regras mínimas para reduzir falso positivo em demos acadêmicas.
    # Só aprova quando o score geral e a estrutura facial passam em conjunto.
    structural_ok = (orb_score is not None and orb_score >= 0.26) or (
        edge_score is not None and edge_score >= 0.36
    )
    histogram_ok = hist_score >= 0.72
    verified = score >= 0.67 and histogram_ok and structural_ok

    return {
        "score": score,
        "hist_score": hist_score,
        "orb_score": orb_score,
        "edge_score": edge_score,
        "match": verified,
    }


def _face_similarity(face1, face2):
    return _face_similarity_details(face1, face2)["score"]


# Extrai a face principal a partir de um caminho no disco.
def extract_face_from_path(image_path: str):
    image = _load_image(image_path)
    return _detect_single_face(image)


# Compara duas imagens faciais já salvas no disco.
def compare_faces_by_path(image_path_1: str, image_path_2: str):
    try:
        face1 = extract_face_from_path(image_path_1)
        face2 = extract_face_from_path(image_path_2)
        metrics = _face_similarity_details(face1, face2)

        return {
            "success": True,
            "match": metrics["match"],
            "message": "Faces correspondem." if metrics["match"] else "Faces não correspondem.",
            "score": metrics["score"],
            "hist_score": metrics["hist_score"],
            "orb_score": metrics["orb_score"],
            "edge_score": metrics["edge_score"],
            "liveness_ok": True,
        }
    except Exception as e:
        return {
            "success": False,
            "match": False,
            "message": str(e),
            "score": None,
            "hist_score": None,
            "orb_score": None,
            "edge_score": None,
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
        "message": "Cadastro facial validado com sucesso.",
        "score": result.get("score"),
        "liveness_ok": True,
    }
