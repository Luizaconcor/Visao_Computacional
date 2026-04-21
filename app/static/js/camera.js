const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const btnCapturar = document.getElementById("btnCapturar");
const hiddenInput = document.getElementById("live_image_base64");

async function iniciarCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    video.srcObject = stream;
    video.style.transform = "scaleX(-1)";
  } catch (error) {
    alert("Não foi possível acessar a câmera. Verifique as permissões do navegador.");
    console.error(error);
  }
}

btnCapturar.addEventListener("click", () => {
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
  hiddenInput.value = dataUrl;
  alert("Verificação capturada com sucesso.");
});

iniciarCamera();
