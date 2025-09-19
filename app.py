from flask import Flask, request, render_template, send_file, abort
import sqlite3
import uuid
import qrcode
import io
import base64
import os

app = Flask(__name__)

# --- Datenbank initialisieren ---
DB_FILE = 'kfc.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS kinder (
            id TEXT PRIMARY KEY,
            vorname TEXT,
            nachname TEXT,
            email TEXT,
            strasse TEXT,
            plz TEXT,
            ort TEXT,
            geburtsdatum TEXT,
            notfallnummer TEXT,
            allergien TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Route für Formularanzeige ---
@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')  # sucht automatisch im templates/ Ordner

# --- Route zum Verarbeiten des Formulars ---
@app.route('/anmelden', methods=['POST'])
def anmelden():
    # Daten aus Formular auslesen
    vorname = request.form.get('Vorname')
    nachname = request.form.get('Nachname')
    email = request.form.get('email')
    strasse = request.form.get('strasse')
    plz = request.form.get('plz')
    ort = request.form.get('ort')
    geburtsdatum = request.form.get('geburtsdatum')
    notfallnummer = request.form.get('notfallnummer')
    allergien = request.form.get('allergien')

    # Eindeutige ID generieren
    kind_id = str(uuid.uuid4())

    # Daten in DB speichern
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (kind_id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien))
    conn.commit()
    conn.close()

    # QR-Code generieren (nur die ID)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    # QR-Code in Bytes speichern
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    # QR-Code als Base64 für HTML einbetten
    qr_base64 = base64.b64encode(buf.getvalue()).decode('ascii')

    # HTML zurückgeben
    return f'''
        <h2>Vielen Dank für die Anmeldung, {vorname} {nachname}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{qr_base64}" alt="QR-Code">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

# --- Sichere Route zum Herunterladen der Datenbank ---
@app.route('/download-db')
def download_db():
    secret_key = request.args.get("key")
    if secret_key != "MEINGEHEIMESPASSWORT":  # Passwort anpassen!
        return abort(403)
    return send_file(DB_FILE, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
