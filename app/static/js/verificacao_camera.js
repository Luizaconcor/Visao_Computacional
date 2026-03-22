const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const form = document.getElementById("verificacaoForm");
const hiddenInput = document.getElementById("foto_base64");

async function iniciarCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    video.srcObject = stream;
  } catch (error) {
    alert("Não foi possível acessar a câmera. Verifique as permissões do navegador.");
    console.error(error);
  }
}

video.addEventListener("loadedmetadata", () => {
  const width = video.videoWidth || 360;
  const height = video.videoHeight || 270;
  canvas.width = width;
  canvas.height = height;
});

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
  hiddenInput.value = canvas.toDataURL("image/jpeg", 0.9);

  if (!hiddenInput.value) {
    event.preventDefault();
    alert("Não foi possível capturar a foto para verificação.");
  }
});

iniciarCamera();
