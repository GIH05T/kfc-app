<script>
const canvas = document.getElementById("signature-pad");
const ctx = canvas.getContext("2d");
let drawing = false;
let hasSignature = false;

// Canvas hochauflösend
function resizeCanvas() {
    const ratio = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    ctx.scale(ratio, ratio);
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// Pointer Events für Touch & Maus
canvas.addEventListener("pointerdown", e => { drawing=true; hasSignature=true; draw(e); checkForm(); });
canvas.addEventListener("pointermove", draw);
canvas.addEventListener("pointerup", () => { drawing=false; ctx.beginPath(); });
canvas.addEventListener("pointerleave", () => { drawing=false; ctx.beginPath(); });

// Zeichnen
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

// Signatur zurücksetzen
function resetSignature(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.beginPath();
    hasSignature = false;
    checkForm();
}

// Form validierung
const form = document.getElementById("registrationForm");
const submitBtn = document.getElementById("submitBtn");

function checkForm() {
    const allValid = form.checkValidity() && hasSignature;
    if(allValid){
        submitBtn.classList.add("active");
        submitBtn.disabled = false;
    } else {
        submitBtn.classList.remove("active");
        submitBtn.disabled = true;
    }
}

// Save signature beim Absenden
form.addEventListener("submit", e => {
    if(!hasSignature) {
        alert("Bitte unterschreiben Sie im Feld!");
        e.preventDefault();
        return false;
    }
    const dataURL = canvas.toDataURL();
    document.getElementById("signature").value = dataURL;
});

// Prüfen bei jedem Input
form.addEventListener("input", checkForm);
checkForm(); // initial
</script>