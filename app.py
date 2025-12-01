from flask import Flask, render_template, request, redirect, url_for, send_file
import json, os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
import base64
from datetime import datetime

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

# --- Gruppe berechnen ---
def calculate_group(birthdate_str):
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
        age = (datetime.now() - birthdate).days // 365
        return age, "5-7" if age <= 7 else "8-13"
    except:
        return 0, ""

# --- Punkte berechnen ---
def calculate_points(r):
    points = 0
    for i in range(5):
        if r.get(f"Tag{i+1}"): points += 1
        if r.get(f"Verse{i+1}"): points += 1
    return points

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        registrations = load_data()
        reg_id = generate_id()
        data = {
            "ID": reg_id,
            "Geschlecht": request.form.get("Geschlecht", "m"),
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("Email"),
            "Strasse": request.form.get("Strasse"),
            "PLZ": request.form.get("PLZ"),
            "Ort": request.form.get("Ort"),
            "Geburtsdatum": request.form.get("Geburtsdatum"),
            "Notfallnummer": request.form.get("Notfallnummer"),
            "Allergien": request.form.get("Allergien"),
            "Unterschrift": request.form.get("Unterschrift"),
            "DSGVO": bool(request.form.get("DSGVO")),
            "Tag1": False, "Tag2": False, "Tag3": False, "Tag4": False, "Tag5": False,
            "Verse1": False, "Verse2": False, "Verse3": False, "Verse4": False, "Verse5": False
        }
        data["Alter"], data["Gruppe"] = calculate_group(data["Geburtsdatum"])
        data["Punkte"] = calculate_points(data)
        registrations.append(data)
        save_data(registrations)
        return redirect(url_for("success", reg_id=reg_id))
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# --- Admin-Seite mit Suche ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()

    # Suche
    search_query = request.args.get("search", "").lower()
    if search_query:
        registrations = [
            r for r in registrations
            if search_query in str(r["ID"])
            or search_query in r["Vorname"].lower()
            or search_query in r["Nachname"].lower()
        ]

    return render_template("admin.html", registrations=registrations, pw=pw, search_query=search_query)

@app.route("/update/<int:reg_id>", methods=["POST"])
def update(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    for r in registrations:
        if r["ID"] == reg_id:
            r["Geschlecht"] = request.form.get("Geschlecht")
            r["Vorname"] = request.form.get("Vorname")
            r["Nachname"] = request.form.get("Nachname")
            r["Strasse"] = request.form.get("Strasse")
            r["PLZ"] = request.form.get("PLZ")
            r["Ort"] = request.form.get("Ort")
            r["Geburtsdatum"] = request.form.get("Geburtsdatum")
            r["Allergien"] = request.form.get("Allergien")
            # Kästchen speichern
            for i in range(5):
                r[f"Tag{i+1}"] = bool(request.form.get(f"Tag{i+1}"))
                r[f"Verse{i+1}"] = bool(request.form.get(f"Verse{i+1}"))
            r["Alter"], r["Gruppe"] = calculate_group(r["Geburtsdatum"])
            r["Punkte"] = calculate_points(r)
            break
    save_data(registrations)
    return redirect(url_for("admin", pw=pw))

@app.route("/delete/<int:reg_id>")
def delete(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    registrations = [r for r in registrations if r["ID"] != reg_id]
    save_data(registrations)
    return redirect(url_for("admin", pw=pw))

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

    headers = list(registrations[0].keys())
    ws.append(headers)

    row_index = 2
    for r in registrations:
        col_index = 1
        for h in headers:
            if h == "Unterschrift" and r[h]:
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

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

if __name__ == "__main__":
    app.run(debug=True)
