from flask import Flask, render_template, request, redirect, url_for, send_file, abort
import json, os, qrcode
from io import BytesIO
import pandas as pd

app = Flask(__name__)

DATA_FILE = "registrations.json"
QR_FOLDER = "static/qrcodes"

# Ordner für QR-Codes erstellen, falls nicht vorhanden
os.makedirs(QR_FOLDER, exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_id():
    registrations = load_data()
    if not registrations:
        return 1
    else:
        return max(r["ID"] for r in registrations) + 1

def generate_qr_code(reg_id):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(f"ID:{reg_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(QR_FOLDER, f"{reg_id}.png")
    img.save(qr_path)
    return qr_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        registrations = load_data()

        reg_id = generate_id()

        data = {
            "ID": reg_id,
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("email"),
            "Strasse": request.form.get("strasse"),
            "PLZ": request.form.get("plz"),
            "Ort": request.form.get("ort"),
            "Geburtsdatum": request.form.get("geburtsdatum"),
            "Notfallnummer": request.form.get("notfallnummer"),
            "Allergien": request.form.get("allergien"),
            "Unterschrift": request.form.get("unterschrift"),
            "DSGVO": bool(request.form.get("dsgvo")),
            "QR_Code": f"{reg_id}.png"
        }

        registrations.append(data)
        save_data(registrations)

        generate_qr_code(reg_id)

        return redirect(url_for("success", reg_id=reg_id))

    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return f"""
    <h2>Danke für die Anmeldung!</h2>
    <p>Ihre Anmelde-ID ist: <strong>{reg_id}</strong></p>
    <img src='/static/qrcodes/{reg_id}.png' alt='QR-Code'>
    <p><a href='/'>Zurück</a></p>
    """

@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != "MEINADMINPASSWORT":
        return "Zugriff verweigert", 403

    registrations = load_data()
    return render_template("admin.html", registrations=registrations)

@app.route("/export_excel")
def export_excel():
    pw = request.args.get("pw")
    if pw != "MEINADMINPASSWORT":
        return "Zugriff verweigert", 403

    registrations = load_data()
    if not registrations:
        return "Keine Daten zum Exportieren", 400

    df = pd.DataFrame(registrations)
    df['Unterschrift'] = df['Unterschrift'].apply(lambda x: '[Bild]')
    df['QR_Code'] = df['QR_Code'].apply(lambda x: '[QR-Bild]')

    output = "registrations.xlsx"
    df.to_excel(output, index=False)

    return send_file(output, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
