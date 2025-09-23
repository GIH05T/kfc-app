import os
import uuid
import io
import base64
from flask import Flask, request, render_template_string
from sqlalchemy import create_engine, text
import qrcode

app = Flask(__name__)

# -------------------------------
# --- Render-Environment ---
# -------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_KEY = os.getenv("ADMIN_KEY", "MEINADMINPASSWORT")
PORT = int(os.getenv("PORT", 5000))  # Render setzt automatisch PORT

# -------------------------------
# --- DB Initialisierung ---
# -------------------------------
engine = create_engine(DATABASE_URL)

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

# -------------------------------
# --- Formular-Seite ---
# -------------------------------
@app.route('/', methods=['GET'])
def index():
    with open('form.html', 'r', encoding='utf-8') as f:
        form_html = f.read()
    return render_template_string(form_html)

# -------------------------------
# --- Anmeldung verarbeiten ---
# -------------------------------
@app.route('/anmelden', methods=['POST'])
def anmelden():
    data = {k: request.form[k] for k in request.form.keys()}
    kind_id = str(uuid.uuid4())
    data["id"] = kind_id

    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO kinder (id, vorname, nachname, email, strasse, plz, ort, geburtsdatum, notfallnummer, allergien)
            VALUES (:id, :vorname, :nachname, :email, :strasse, :plz, :ort, :geburtsdatum, :notfallnummer, :allergien)
        '''), data)

    # QR-Code generieren
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(kind_id)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return f'''
        <h2>Vielen Dank für die Anmeldung, {data["vorname"]} {data["nachname"]}!</h2>
        <p>Ihre eindeutige Kind-ID: <strong>{kind_id}</strong></p>
        <p>QR-Code für diese Anmeldung:</p>
        <img src="data:image/png;base64,{img_b64}">
        <p><a href="/">Zurück zum Formular</a></p>
    '''

# -------------------------------
# --- Admin-Seite ---
# -------------------------------
@app.route('/admin')
def admin():
    key = request.args.get("key")
    if key != ADMIN_KEY:
        return "<h3>Zugriff verweigert – falscher Schlüssel!</h3>", 403

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM kinder")).fetchall()

    table_html = "<h2>Alle Anmeldungen</h2><table border='1' cellpadding='5'>"
    table_html += "<tr><th>ID</th><th>Vorname</th><th>Nachname</th><th>Email</th><th>Straße</th><th>PLZ</th><th>Ort</th><th>Geburtsdatum</th><th>Notfallnummer</th><th>Allergien</th></tr>"
    for row in result:
        table_html += "<tr>" + "".join(f"<td>{str(cell)}</td>" for cell in row) + "</tr>"
    table_html += "</table>"

    return table_html

# -------------------------------
# --- Main ---
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
