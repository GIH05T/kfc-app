const canvas = document.getElementById("signature-pad");
const ctx = canvas.getContext("2d");
const form = document.getElementById("registration-form");
const submitBtn = document.getElementById("submit-btn");
const resetBtn = document.getElementById("reset-btn");
const signatureInput = document.getElementById("signature");

let drawing = false;

function resizeCanvas() {
    const ratio = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    ctx.scale(ratio, ratio);
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

canvas.addEventListener("mousedown", () => drawing = true);
canvas.addEventListener("mouseup", () => { drawing = false; ctx.beginPath(); });
canvas.addEventListener("mouseleave", () => { drawing = false; ctx.beginPath(); });
canvas.addEventListener("mousemove", draw);

// Touch support
canvas.addEventListener("touchstart", (e) => { drawing = true; draw(e.touches[0]); e.preventDefault(); });
canvas.addEventListener("touchend", () => { drawing = false; ctx.beginPath(); });
canvas.addEventListener("touchmove", (e) => { draw(e.touches[0]); e.preventDefault(); });

function draw(e){
    if(!drawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#000";
    ctx.lineTo(x,y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x,y);
}

resetBtn.addEventListener("click", () => {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.beginPath();
    checkForm();
});

function isCanvasBlank(c) {
    const blank = document.createElement("canvas");
    blank.width = c.width;
    blank.height = c.height;
    return c.toDataURL() === blank.toDataURL();
}

function checkForm() {
    const allFilled = Array.from(form.querySelectorAll("[required]")).every(input => input.value.trim() !== "");
    const canvasNotEmpty = !isCanvasBlank(canvas);
    submitBtn.disabled = !(allFilled && canvasNotEmpty);
}

form.querySelectorAll("input, select").forEach(el => el.addEventListener("input", checkForm));
canvas.addEventListener("mouseup", checkForm);
canvas.addEventListener("touchend", checkForm);

form.addEventListener("submit", () => {
    signatureInput.value = canvas.toDataURL();
});
