from flask import Flask, request, render_template_string
import os
import uuid
import qrcode
import io
import base64
from sqlalchemy import create_engine, text

app = Flask(__name__)

# --- Datenbank-Verbindung (PostgreSQL) ---
DATABASE_URL = "postgresql://dbkfc_user:DEIN_PASSWORT@HOSTNAME:5432/dbkfc"
engine = create_engine(DATABASE_URL)

# --- Tabelle erstellen falls nicht vorhanden ---
with engine.begin() as conn:
    conn.execute(text('''
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
    '''))

# --- Route für Formularanzeige ---
@app.route('/', methods=['GET'])
def index():
    with open('form.html', 'r', encoding='utf-8') as f:
        form_html = f.read()
    return render_template_string(form_html)

# --- Route zum Verarbeiten des Formulars ---
@app.route('/anmelden', methods=['POST'])
def anmelden():
    vorname = request.form['Vorname']
    nachname = request.form['Nachname']
    email = request.form['email']
    strasse = request.form['strasse']
    plz = request.form['plz']
    ort = request.form['ort']
    geburtsdatum = request.form['geburtsdatum']
    notfallnummer = request.form['notfallnummer']
    allergien = request.form['allergien']

    kind_id = str(uuid.uuid4())

    # Daten speichern
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
            VALUES (:id, :vorname, :nachname, :email, :strasse, :plz, :ort, :geburtsdatum, :notfallnummer, :allergien)
        '''), {
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
        })

    # QR-Code erstellen
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return f'''
        <h2>Vielen Dank für die Anmeldung, {vorname} {nachname}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{img_b64}">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

# --- Admin-Seite mit Suchfunktion und QR-Scanner ---
@app.route('/admin')
def admin():
    key = request.args.get("key")
    if key != "MEINADMINPASSWORT":
        return "<h3>Zugriff verweigert – falscher Schlüssel!</h3>", 403

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM kinder")).fetchall()

    # HTML-Tabelle
    table_html = "<h2>Alle Anmeldungen</h2><table border='1' cellpadding='5'>"
    table_html += "<tr><th>ID</th><th>Vorname</th><th>Nachname</th><th>Email</th><th>Straße</th><th>PLZ</th><th>Ort</th><th>Geburtsdatum</th><th>Notfallnummer</th><th>Allergien</th></tr>"
    for row in result:
        table_html += "<tr>" + "".join(f"<td>{str(cell)}</td>" for cell in row) + "</tr>"
    table_html += "</table>"

    # QR-Code Scanner und ID-Suche
    html_search = '''
    <h2>Kind suchen</h2>
    <p>Scanne den QR-Code oder gib die ID manuell ein:</p>
    <input type="text" id="kind_id" placeholder="Kind-ID eingeben">
    <button onclick="sucheKind()">Suchen</button>
    <div id="ergebnis"></div>
    <h3>QR-Code Scanner:</h3>
    <div id="reader" style="width:300px"></div>

    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <script>
    function sucheKind() {
        const id = document.getElementById("kind_id").value;
        fetch("/api/suche/" + id)
          .then(res => res.text())
          .then(html => {
              document.getElementById("ergebnis").innerHTML = html;
          });
    }

    function onScanSuccess(decodedText, decodedResult) {
        document.getElementById("kind_id").value = decodedText;
        sucheKind();
    }

    let html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", { fps: 10, qrbox: 250 });
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    '''

    return table_html + html_search

# --- API für Suche ---
@app.route('/api/suche/<kind_id>')
def api_suche(kind_id):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM kinder WHERE id=:id"), {"id": kind_id}).fetchone()
    if not result:
        return "<p><b>Kein Kind gefunden!</b></p>"
    headers = ["ID","Vorname","Nachname","Email","Straße","PLZ","Ort","Geburtsdatum","Notfallnummer","Allergien"]
    html = "<h3>Gefundenes Kind:</h3><table border='1' cellpadding='5'>"
    for h, v in zip(headers, result):
        html += f"<tr><th>{h}</th><td>{v}</td></tr>"
    html += "</table>"
    return html

if __name__ == "__main__":
    app.run(debug=True)
