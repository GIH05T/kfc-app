from flask import Flask, render_template, request, redirect, url_for, send_file
import json, os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
import base64
from io import BytesIO

app = Flask(__name__)

DATA_FILE = "registrations.json"
ADMIN_PASSWORD = "MEINADMINPASSWORT"

# --- JSON Laden/Speichern ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- ID generieren ---
def generate_id():
    registrations = load_data()
    if not registrations:
        return 1
    else:
        return max(r["ID"] for r in registrations) + 1

# --- Routes ---
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
            "DSGVO": bool(request.form.get("dsgvo"))
        }
        registrations.append(data)
        save_data(registrations)
        return redirect(url_for("success", reg_id=reg_id))
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# --- Admin-Seite mit Suche ---
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    search_query = request.args.get("search", "").lower()
    if search_query:
        registrations = [r for r in registrations if search_query in str(r["ID"]) 
                         or search_query in r["Vorname"].lower() 
                         or search_query in r["Nachname"].lower()]

    return render_template("admin.html", registrations=registrations, search_query=search_query)

# --- Excel Export mit Signaturen ---
@app.route("/export_excel")
def export_excel():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    if not registrations:
        return "Keine Daten zum Exportieren", 400

    wb = Workbook()
    ws = wb.active
    ws.title = "Anmeldungen"

    # Header
    headers = list(registrations[0].keys())
    ws.append(headers)

    row_index = 2  # Header ist Zeile 1
    for r in registrations:
        col_index = 1
        for h in headers:
            if h == "Unterschrift":
                data_url = r[h]
                if data_url.startswith("data:image/png;base64,"):
                    img_data = base64.b64decode(data_url.split(",")[1])
                    img = XLImage(BytesIO(img_data))
                    cell = ws.cell(row=row_index, column=col_index)
                    ws.add_image(img, cell.coordinate)
            else:
                ws.cell(row=row_index, column=col_index, value=r[h])
            col_index += 1
        row_index += 1

    output = "registrations.xlsx"
    wb.save(output)
    return send_file(output, as_attachment=True)

if __name__ == "__main__":
    # Lokal testen (nicht für Render)
    app.run(debug=True)
