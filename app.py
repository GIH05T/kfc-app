from flask import Flask, request, render_template, abort
import sqlite3
import uuid
import qrcode
import io
import base64
import os

app = Flask(__name__)

# --- Datenbank ---
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

# --- Formularanzeige ---
@app.route('/', methods=['GET'])
def index():
    return render_template('form.html')

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

    kind_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (kind_id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien))
    conn.commit()
    conn.close()

    # QR-Code generieren
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.getvalue()).decode('ascii')

    return f'''
        <h2>Vielen Dank für die Anmeldung, {vorname} {nachname}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{qr_base64}" alt="QR-Code">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

# --- Admin-Seite mit Suchfunktion ---
@app.route('/admin', methods=['GET'])
def admin():
    password = request.args.get('key')
    if password != "MEINADMINPASSWORT":  # Passwort anpassen!
        return abort(403)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
