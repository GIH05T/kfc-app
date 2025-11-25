document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("signature-pad");
    const ctx = canvas.getContext("2d");
    const submitBtn = document.getElementById("submit-btn");
    const clearBtn = document.getElementById("clear-signature");
    const form = document.getElementById("registration-form");

    // Canvas Größe setzen
    function resizeCanvas() {
        const ratio = window.devicePixelRatio || 1;
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        ctx.scale(ratio, ratio);
    }
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    let drawing = false;

    // Zeichenfunktionen
    function startDraw() { drawing = true; }
    function endDraw() { drawing = false; ctx.beginPath(); }
    function draw(e) {
        if (!drawing) return;
        const rect = canvas.getBoundingClientRect();
        ctx.lineWidth = 2;
        ctx.lineCap = "round";
        ctx.strokeStyle = "#000";
        const x = e.clientX || e.touches[0].clientX;
        const y = e.clientY || e.touches[0].clientY;
        ctx.lineTo(x - rect.left, y - rect.top);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - rect.left, y - rect.top);
    }

    canvas.addEventListener("mousedown", startDraw);
    canvas.addEventListener("mouseup", endDraw);
    canvas.addEventListener("mouseleave", endDraw);
    canvas.addEventListener("mousemove", draw);

    canvas.addEventListener("touchstart", (e) => { startDraw(); draw(e.touches[0]); e.preventDefault(); });
    canvas.addEventListener("touchend", endDraw);
    canvas.addEventListener("touchmove", (e) => { draw(e.touches[0]); e.preventDefault(); });

    // Signatur löschen
    clearBtn.addEventListener("click", () => {
        ctx.clearRect(0,0,canvas.width,canvas.height);
        ctx.beginPath();
        checkForm();
    });

    // Speichern in Hidden Feld beim Absenden
    form.addEventListener("submit", () => {
        document.getElementById("signature").value = canvas.toDataURL();
    });

    // Aktivieren des Submit Buttons nur wenn alle Pflichtfelder + Signatur ausgefüllt
    function checkForm() {
        const requiredFields = form.querySelectorAll("input[required], select[required]");
        let valid = true;
        requiredFields.forEach(f => {
            if (!f.value) valid = false;
        });
        // Prüfen, ob Canvas signiert wurde
        const blank = canvas.toDataURL() === canvasBlank();
        if (blank) valid = false;
        submitBtn.disabled = !valid;
    }

    function canvasBlank() {
        const blank = document.createElement('canvas');
        blank.width = canvas.width;
        blank.height = canvas.height;
        return blank.toDataURL();
    }

    // Eventlistener für Pflichtfelder
    const requiredFields = form.querySelectorAll("input[required], select[required]");
    requiredFields.forEach(f => f.addEventListener("input", checkForm));
    canvas.addEventListener("mouseup", checkForm);
    canvas.addEventListener("touchend", checkForm);
});
