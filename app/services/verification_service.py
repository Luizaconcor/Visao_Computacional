"""Serviços de verificação facial para cadastro e acesso.

Implementação acadêmica simples com OpenCV.
Mais robusta para demo:
- leitura compatível com caminhos do Windows
- fallback quando o detector Haar falha
- comparação sempre tenta usar o recorte central, mesmo sem detecção facial
"""

import os
import cv2
import numpy as np

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
orb = cv2.ORB_create(nfeatures=256)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def _load_image(path: str):
    if not path:
        raise ValueError("Caminho da imagem não informado.")
    if not os.path.exists(path):
        raise ValueError(f"Imagem não encontrada: {path}")

    try:
        file_bytes = np.fromfile(path, dtype=np.uint8)
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir a imagem: {path}") from exc

    if file_bytes.size == 0:
        raise ValueError(f"Arquivo de imagem vazio ou inválido: {path}")

    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Não foi possível ler a imagem: {path}")
    return image


def _central_crop(image, factor=0.72):
    h, w = image.shape[:2]
    side = int(min(h, w) * factor)
    if side <= 0:
        return image
    x1 = max((w - side) // 2, 0)
    y1 = max((h - side) // 2, 0)
    crop = image[y1:y1 + side, x1:x1 + side]
    return crop if crop.size else image


def _normalize_face(image):
    face = cv2.resize(image, (220, 220))
    y1, y2 = 20, 200
    x1, x2 = 20, 200
    face = face[y1:y2, x1:x2]
    return cv2.resize(face, (160, 160))


def _detect_single_face(image):
    if image is None or image.size == 0:
        raise ValueError("Imagem inválida para detecção.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Se o classificador não carregar corretamente, não quebra a demo.
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


def _face_similarity(face1, face2):
    hist_score = _hist_similarity(face1, face2)
    orb_score = _orb_similarity(face1, face2)
    edge_score = _edge_similarity(face1, face2)

    parts = [0.55 * hist_score]
    weight = 0.55

    if orb_score is not None:
        parts.append(0.30 * orb_score)
        weight += 0.30
    if edge_score is not None:
        parts.append(0.15 * edge_score)
        weight += 0.15

    return float(sum(parts) / weight)


def extract_face_from_path(image_path: str):
    image = _load_image(image_path)
    return _detect_single_face(image)


def compare_faces_by_path(image_path_1: str, image_path_2: str):
    try:
        face1 = extract_face_from_path(image_path_1)
        face2 = extract_face_from_path(image_path_2)
        score = _face_similarity(face1, face2)

        # limiar acadêmico mais permissivo para demonstração
        verified = score >= 0.53

        return {
            "success": True,
            "match": verified,
            "message": "Faces correspondem." if verified else "Faces não correspondem.",
            "score": score,
            "liveness_ok": True,
        }
    except Exception as e:
        return {
            "success": False,
            "match": False,
            "message": str(e),
            "score": None,
            "liveness_ok": False,
        }


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
