from deepface import DeepFace
import cv2
import os

def verificar_acesso():
    os.makedirs("capturas_temporarias", exist_ok=True)
    caminho_temporario = "capturas_temporarias/frame.jpg"

    cap = cv2.VideoCapture(0)

    print("Pressione 's' para capturar a imagem para verificação.")
    print("Pressione 'q' para sair.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao acessar a câmera.")
            break

        cv2.imshow("Verificação de Acesso", frame)
        tecla = cv2.waitKey(1)

        if tecla == ord('s'):
            cv2.imwrite(caminho_temporario, frame)
            print("Imagem capturada.")
            break

        elif tecla == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return None, False

    cap.release()
    cv2.destroyAllWindows()

    try:
        resultado = DeepFace.find(
            img_path=caminho_temporario,
            db_path="banco_rostos",
            enforce_detection=False
        )

        if len(resultado) > 0 and not resultado[0].empty:
            caminho_encontrado = resultado[0].iloc[0]["identity"]
            nome_pessoa = caminho_encontrado.split(os.sep)[1]
            return nome_pessoa, True
        else:
            return None, False

    except Exception as e:
        print("Erro durante reconhecimento:", e)
        return None, False