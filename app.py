from flask import Flask, render_template, request, redirect, url_for, send_file
import json, os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
import base64
from io import BytesIO
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

# --- ID generieren (lückenlos) ---
def generate_id():
    registrations = load_data()
    if not registrations:
        return 1
    existing_ids = sorted(r["ID"] for r in registrations)
    current = 1
    for eid in existing_ids:
        if eid == current:
            current += 1
        else:
            break
    return current

# --- Gruppe automatisch berechnen ---
def compute_group(geburtsdatum):
    try:
        birth_year = datetime.strptime(geburtsdatum, "%Y-%m-%d")
        age = (datetime.now() - birth_year).days // 365
        if age <= 7:
            return "5-7"
        else:
            return "8-13"
    except:
        return ""

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        registrations = load_data()
        reg_id = generate_id()
        geburtsdatum = request.form.get("Geburtsdatum")
        gruppe = compute_group(geburtsdatum)
        data = {
            "ID": reg_id,
            "Geschlecht": request.form.get("Geschlecht"),
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("Email"),
            "Strasse": request.form.get("Strasse"),
            "PLZ": request.form.get("PLZ"),
            "Ort": request.form.get("Ort"),
            "Geburtsdatum": geburtsdatum,
            "Notfallnummer": request.form.get("Notfallnummer"),
            "Allergien": request.form.get("Allergien"),
            "Unterschrift": request.form.get("Unterschrift"),
            "DSGVO": bool(request.form.get("DSGVO")),
            "Gruppe": gruppe,
            "Punkte": 0,
            "Tag1": False, "Tag2": False, "Tag3": False, "Tag4": False, "Tag5": False,
            "Verse1": False, "Verse2": False, "Verse3": False, "Verse4": False, "Verse5": False
        }
        registrations.append(data)
        save_data(registrations)
        return redirect(url_for("success", reg_id=reg_id))
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# --- Admin-Seite ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    search_query = request.args.get("search", "").lower()
    if search_query:
        registrations = [r for r in registrations if search_query in str(r["ID"])
                         or search_query in r["Vorname"].lower()
                         or search_query in r["Nachname"].lower()
                         or search_query in r["Notfallnummer"]]

    return render_template("admin.html", registrations=registrations, search_query=search_query, pw=pw)

# --- Admin Update Eintrag ---
@app.route("/update/<int:reg_id>", methods=["POST"])
def update(reg_id):
    registrations = load_data()
    for r in registrations:
        if r["ID"] == reg_id:
            # Update Felder
            r["Geschlecht"] = request.form.get("Geschlecht")
            r["Vorname"] = request.form.get("Vorname")
            r["Nachname"] = request.form.get("Nachname")
            r["Strasse"] = request.form.get("Strasse")
            r["PLZ"] = request.form.get("PLZ")
            r["Ort"] = request.form.get("Ort")
            r["Notfallnummer"] = request.form.get("Notfallnummer")
            r["Allergien"] = request.form.get("Allergien")
            r["Geburtsdatum"] = request.form.get("Geburtsdatum")
            r["Gruppe"] = compute_group(r["Geburtsdatum"])
            # Punkteberechnung: Anzahl Tage + Bibelverse
            points = 0
            for i in range(1,6):
                r[f"Tag{i}"] = True if request.form.get(f"Tag{i}") else False
                r[f"Verse{i}"] = True if request.form.get(f"Verse{i}") else False
                if r[f"Tag{i}"]:
                    points += 1
                if r[f"Verse{i}"]:
                    points +=1
            r["Punkte"] = points
            break
    save_data(registrations)
    return redirect(url_for("admin", pw=request.args.get("pw")))

# --- Delete Eintrag ---
@app.route("/delete/<int:reg_id>")
def delete(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    registrations = load_data()
    registrations = [r for r in registrations if r["ID"] != reg_id]
    save_data(registrations)
    return redirect(url_for("admin", pw=pw))

# --- Datenschutzseite ---
@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

# --- Excel Export ---
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
            if h == "Unterschrift":
                data_url = r[h]
                if data_url and data_url.startswith("data:image/png;base64,"):
                    img_data = base64.b64decode(data_url.split(",")[1])
                    img = XLImage(BytesIO(img_data))
                    cell = ws.cell(row=row_index, column=col_index)
                    ws.add_image(img, cell.coordinate)
            else:
                ws.cell(row=row_index, column=col_index, value=r[h])
            col_index +=1
        row_index +=1

    output = "registrations.xlsx"
    wb.save(output)
    return send_file(output, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
