<<<<<<< HEAD
import os
=======
from flask import Flask, request, render_template, abort
import sqlite3
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
import uuid
import io
import base64
<<<<<<< HEAD
from flask import Flask, request, render_template_string
from sqlalchemy import create_engine, text
import qrcode

app = Flask(__name__)

# -------------------------------
# --- Environment Variables ---
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_KEY = os.getenv("ADMIN_KEY", "MEINADMINPASSWORT")
PORT = int(os.getenv("PORT", 5000))

# -------------------------------
# --- DB Initialisierung ---
# -------------------------------
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text('''
=======
import os

app = Flask(__name__)

# --- Datenbank ---
DB_FILE = 'kfc.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
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

<<<<<<< HEAD
# -------------------------------
# --- Formular-Seite ---
# -------------------------------
=======
init_db()

# --- Formularanzeige ---
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

<<<<<<< HEAD
# -------------------------------
# --- Anmeldung verarbeiten ---
# -------------------------------
@app.route('/anmelden', methods=['POST'])
def anmelden():
    data = {k: request.form[k] for k in request.form.keys()}
=======
# --- Anmeldung verarbeiten ---
@app.route('/anmelden', methods=['POST'])
def anmelden():
    vorname = request.form.get('Vorname')
    nachname = request.form.get('Nachname')
    email = request.form.get('email')
    strasse = request.form.get('strasse')
    plz = request.form.get('plz')
    ort = request.form.get('ort')
    geburtsdatum = request.form.get('geburtsdatum')
    notfallnummer = request.form.get('notfallnummer')
    allergien = request.form.get('allergien')

>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
    kind_id = str(uuid.uuid4())
    data["id"] = kind_id

<<<<<<< HEAD
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
            VALUES (:id, :vorname, :nachname, :email, :strasse, :plz, :ort, :geburtsdatum, :notfallnummer, :allergien)
        '''), data)
=======
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (kind_id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien))
    conn.commit()
    conn.close()
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)

    # QR-Code generieren
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
<<<<<<< HEAD
    img = qr.make_image(fill="black", back_color="white")
=======
    img = qr.make_image(fill_color='black', back_color='white')

>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.getvalue()).decode('ascii')

    return f'''
        <h2>Vielen Dank für die Anmeldung, {data["vorname"]} {data["nachname"]}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{qr_base64}" alt="QR-Code">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

<<<<<<< HEAD
# -------------------------------
# --- Admin-Seite ---
# -------------------------------
@app.route('/admin')
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "<h3>Zugriff verweigert – falscher Schlüssel!</h3>", 403
=======
# --- Admin-Seite mit Suchfunktion ---
@app.route('/admin', methods=['GET'])
def admin():
    password = request.args.get('key')
    if password != "MEINADMINPASSWORT":  # Passwort anpassen!
        return abort(403)
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)

    search = request.args.get('search', '').strip()  # Suchfeld optional

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if search:
        # Suche nach Vorname, Nachname oder ID
        c.execute('''
            SELECT * FROM kinder 
            WHERE id LIKE ? OR vorname LIKE ? OR nachname LIKE ?
            ORDER BY vorname
        ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        c.execute('SELECT * FROM kinder ORDER BY vorname')

    kinder = c.fetchall()
    conn.close()

<<<<<<< HEAD
    table_html = "<h2>Alle Anmeldungen</h2><table border='1' cellpadding='5'>"
    table_html += "<tr><th>ID</th><th>Vorname</th><th>Nachname</th><th>Email</th><th>Straße</th><th>PLZ</th><th>Ort</th><th>Geburtsdatum</th><th>Notfallnummer</th><th>Allergien</th></tr>"
    for row in result:
        table_html += "<tr>" + "".join(f"<td>{str(cell)}</td>" for cell in row) + "</tr>"
    table_html += "</table>"

    return table_html
=======
    # HTML-Tabelle
    table_html = "<table border='1' cellpadding='5'><tr><th>ID</th><th>Vorname</th><th>Nachname</th><th>Email</th><th>Straße</th><th>PLZ</th><th>Ort</th><th>Geburtsdatum</th><th>Notfallnummer</th><th>Allergien</th></tr>"
    for k in kinder:
        table_html += "<tr>" + "".join(f"<td>{field}</td>" for field in k) + "</tr>"
    table_html += "</table>"

    # Suchfeld HTML
    search_form = f'''
        <form method="get" action="/admin">
            <input type="hidden" name="key" value="{password}">
            <input type="text" name="search" placeholder="Nach Name oder ID suchen" value="{search}">
            <button type="submit">Suchen</button>
        </form>
        <br>
    '''

    return f"<h2>Admin-Seite: Alle Anmeldungen</h2>{search_form}{table_html}<p><a href='/'>Zurück zum Formular</a></p>"
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)

# -------------------------------
# --- Main ---
# -------------------------------
if __name__ == "__main__":
<<<<<<< HEAD
    port = int(os.environ.get("PORT", 5000))  # nimmt Render-Port oder lokal 500
    app.run(host="0.0.0.0", port=PORT, debug=True)
=======
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
>>>>>>> parent of b99a284 (QR Code und Admin Seit hinzu)
