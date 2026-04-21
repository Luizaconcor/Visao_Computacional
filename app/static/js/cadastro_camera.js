// Elementos usados para exibir a câmera e enviar a imagem capturada ao backend.
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const form = document.getElementById("cadastroForm");
const hiddenInput = document.getElementById("foto_base64");
const cameraStatus = document.getElementById("cameraStatus");

// Atualiza o texto de status mostrado ao usuário.
function atualizarStatus(texto) {
  if (cameraStatus) {
    cameraStatus.textContent = texto;
  }
}

// Solicita acesso à câmera frontal do dispositivo.
async function iniciarCamera() {
  try {
    atualizarStatus("Solicitando permissão...");

    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });

    video.srcObject = stream;
    video.style.transform = "scaleX(-1)";
    atualizarStatus("Câmera pronta");
  } catch (error) {
    atualizarStatus("Câmera indisponível");
    alert("Não foi possível acessar a câmera. Verifique as permissões do navegador.");
    console.error(error);
  }
}

// Ajusta o canvas para o tamanho real do vídeo recebido pela câmera.
video.addEventListener("loadedmetadata", () => {
  const width = video.videoWidth || 360;
  const height = video.videoHeight || 270;
  canvas.width = width;
  canvas.height = height;
});

// Antes de enviar o formulário, captura um frame da câmera em JPEG base64.
form.addEventListener("submit", (event) => {
  if (!video.srcObject) {
    event.preventDefault();
    alert("A câmera ainda não está pronta.");
    return;
  }

  const width = video.videoWidth || canvas.width || 360;
  const height = video.videoHeight || canvas.height || 270;
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, width, height);
  hiddenInput.value = canvas.toDataURL("image/jpeg", 0.92);

  if (!hiddenInput.value) {
    event.preventDefault();
    alert("Não foi possível capturar a foto para cadastro.");
    atualizarStatus("Falha ao capturar");
    return;
  }

  atualizarStatus("Imagem capturada");
});

iniciarCamera();
