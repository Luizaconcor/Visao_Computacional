import cv2
import os

def cadastrar_pessoa(nome):
    pasta_destino = os.path.join("banco_rostos", nome)
    os.makedirs(pasta_destino, exist_ok=True)

    cap = cv2.VideoCapture(0)

    print("Pressione 's' para salvar a foto.")
    print("Pressione 'q' para sair.")

    contador = len(os.listdir(pasta_destino)) + 1

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao acessar a câmera.")
            break

        cv2.imshow("Cadastro de Rosto", frame)

        tecla = cv2.waitKey(1)

        if tecla == ord('s'):
            caminho_foto = os.path.join(pasta_destino, f"foto{contador}.jpg")
            cv2.imwrite(caminho_foto, frame)
            print(f"Foto salva em: {caminho_foto}")
            contador += 1

        elif tecla == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()