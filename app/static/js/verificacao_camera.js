// Elementos usados na etapa de verificação facial.
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const form = document.getElementById("verificacaoForm");
const hiddenInput = document.getElementById("foto_base64");
const cameraStatus = document.getElementById("cameraStatus");

// Atualiza o selo visual de status da câmera.
function atualizarStatus(texto) {
  if (cameraStatus) {
    cameraStatus.textContent = texto;
  }
}

// Inicia a câmera frontal do dispositivo para verificação ao vivo.
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

// Mantém o canvas sincronizado com a resolução real do vídeo.
video.addEventListener("loadedmetadata", () => {
  const width = video.videoWidth || 360;
  const height = video.videoHeight || 270;
  canvas.width = width;
  canvas.height = height;
});

// Captura um frame no instante do envio para comparação com o banco.
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
    alert("Não foi possível capturar a foto para verificação.");
    atualizarStatus("Falha ao capturar");
    return;
  }

  atualizarStatus("Imagem capturada");
});

iniciarCamera();
