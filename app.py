from flask import Flask, request, render_template
import uuid
import qrcode
import io
import base64

app = Flask(__name__)

# --- Temporäre Liste für angemeldete Kinder ---
kinder_liste = []

# --- Route für das Formular ---
@app.route('/', methods=['GET'])
def index():
    return render_template("form.html")

# --- Route zum Verarbeiten der Anmeldung ---
@app.route('/anmelden', methods=['POST'])
def anmelden():
    vorname = request.form['Vorname']
    nachname = request.form['Nachname']
    email = request.form.get('email', '')
    strasse = request.form['strasse']
    plz = request.form['plz']
    ort = request.form['ort']
    geburtsdatum = request.form['geburtsdatum']
    notfallnummer = request.form['notfallnummer']
    allergien = request.form['allergien']

    # Eindeutige ID
    kind_id = str(uuid.uuid4())

    # Anmeldung speichern (in der Liste)
    kind = {
        "id": kind_id,
        "vorname": vorname,
        "nachname": nachname,
        "email": email,
        "strasse": strasse,
        "plz": plz,
        "ort": ort,
        "geburtsdatum": geburtsdatum,
        "notfallnummer": notfallnummer,
        "allergien": allergien
    }
    kinder_liste.append(kind)

    # QR-Code generieren
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return f'''
        <h2>Vielen Dank für die Anmeldung, {vorname} {nachname}!</h2>
        <p>Ihre Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code:</p>
        <img src="data:image/png;base64,{qr_base64}">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

# --- Admin-Seite ---
ADMIN_PASSWORD = "MEINADMINPASSWORT"

@app.route('/admin', methods=['GET'])
def admin():
    key = request.args.get('key', '')
    if key != ADMIN_PASSWORD:
        return "Zugriff verweigert!"
    
    html = "<h1>Admin - Liste der Anmeldungen</h1><ul>"
    for k in kinder_liste:
        html += f"<li>{k['vorname']} {k['nachname']} ({k['id']}) - Allergien: {k['allergien']}</li>"
    html += "</ul><p><a href='/'>Zurück zur Anmeldung</a></p>"
    return html

if __name__ == "__main__":
    app.run(debug=True)
