from flask import Flask, request, render_template_string, send_file
import sqlite3
import uuid
import qrcode
import io
import os

app = Flask(__name__)

# --- Datenbank initialisieren ---
DB_FILE = 'kfc.db'


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS kinder
              (
                  id
                  TEXT
                  PRIMARY
                  KEY,
                  vorname
                  TEXT,
                  nachname
                  TEXT,
                  email
                  TEXT,
                  strasse
                  TEXT,
                  plz
                  TEXT,
                  ort
                  TEXT,
                  geburtsdatum
                  TEXT,
                  notfallnummer
                  TEXT,
                  allergien
                  TEXT
              )
              ''')
    conn.commit()
    conn.close()


init_db()


# --- Route für Formularanzeige ---
@app.route('/', methods=['GET'])
def index():
    with open('form.html', 'r', encoding='utf-8') as f:
        form_html = f.read()
    return render_template_string(form_html)


# --- Route zum Verarbeiten des Formulars ---
@app.route('/anmelden', methods=['POST'])
def anmelden():
    # Daten aus Formular auslesen
    vorname = request.form['Vorname']
    nachname = request.form['Nachname']
    email = request.form['email']
    strasse = request.form['strasse']
    plz = request.form['plz']
    ort = request.form['ort']
    geburtsdatum = request.form['geburtsdatum']
    notfallnummer = request.form['notfallnummer']
    allergien = request.form['allergien']

    # Eindeutige ID generieren
    kind_id = str(uuid.uuid4())

    # Daten in DB speichern
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
              INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer,
                                  allergien)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ''', (kind_id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien))
    conn.commit()
    conn.close()

    # QR-Code generieren (nur die ID)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # In Bytes speichern
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    # QR-Code direkt im Browser anzeigen + ID als Text
    return f'''
        <h2>Vielen Dank für die Anmeldung, {vorname} {nachname}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{buf.getvalue().hex()}">
        <p><a href="/">Zurück zum Formular</a></p>
    '''


if __name__ == "__main__":
    app.run(debug=True)

