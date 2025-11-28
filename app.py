from flask import Flask, render_template, request, redirect, send_file
import json, os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
import base64
from io import BytesIO
from datetime import datetime, date

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
    return max(r["ID"] for r in registrations) + 1

# --- Frontend Anmeldung ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        registrations = load_data()
        reg_id = generate_id()

        # Checkboxen für Tage & Verse
        verse = [int(bool(request.form.get(f"Verse{i}"))) for i in range(1,6)]
        tage = [int(bool(request.form.get(f"Tag{i}"))) for i in range(1,6)]
        geburtsdatum = request.form.get("geburtsdatum")
        # Alter berechnen
        if geburtsdatum:
            bd = datetime.strptime(geburtsdatum, "%Y-%m-%d").date()
            today = date.today()
            alter = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            # Gruppe automatisch
            if 5 <= alter <= 7: gruppe = "5-7"
            elif 8 <= alter <= 13: gruppe = "8-13"
            else: gruppe = ""
        else:
            alter = ""
            gruppe = ""

        data = {
            "ID": reg_id,
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("email"),
            "Strasse": request.form.get("strasse"),
            "PLZ": request.form.get("plz"),
            "Ort": request.form.get("ort"),
            "Geburtsdatum": geburtsdatum,
            "Alter": alter,
            "Notfallnummer": request.form.get("notfallnummer"),
            "Allergien": request.form.get("allergien"),
            "Gruppe": gruppe,
            "Verse": verse,
            "Anwesenheit": tage,
            "Punkte": sum(verse)+sum(tage),
            "Unterschrift": request.form.get("unterschrift"),
            "DSGVO": bool(request.form.get("dsgvo"))
        }

        registrations.append(data)
        save_data(registrations)
        return redirect(f"/success?reg_id={reg_id}")
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# --- Admin Seite ---
@app.route("/admin", methods=["GET","POST"])
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

    return render_template("admin.html", registrations=registrations, search_query=search_query, pw=ADMIN_PASSWORD)

# --- Admin Update ---
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    registrations = load_data()
    for r in registrations:
        if r["ID"] == id:
            r["Vorname"] = request.form.get("Vorname")
            r["Nachname"] = request.form.get("Nachname")
            r["Geburtsdatum"] = request.form.get("Geburtsdatum")
            r["Geschlecht"] = request.form.get("Geschlecht")
            r["Verse"] = [int(bool(request.form.get(f"Verse{i}"))) for i in range(1,6)]
            r["Anwesenheit"] = [int(bool(request.form.get(f"Tag{i}"))) for i in range(1,6)]
            r["Punkte"] = sum(r["Verse"]) + sum(r["Anwesenheit"])
            # Alter & Gruppe automatisch
            if r["Geburtsdatum"]:
                bd = datetime.strptime(r["Geburtsdatum"], "%Y-%m-%d").date()
                today = date.today()
                r["Alter"] = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                if 5 <= r["Alter"] <= 7:
                    r["Gruppe"] = "5-7"
                elif 8 <= r["Alter"] <= 13:
                    r["Gruppe"] = "8-13"
    save_data(registrations)
    return redirect(f"/admin?pw={ADMIN_PASSWORD}")

# --- Admin Delete ---
@app.route("/delete/<int:id>")
def delete(id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    registrations = load_data()
    registrations = [r for r in registrations if r["ID"] != id]
    save_data(registrations)
    return redirect(f"/admin?pw={ADMIN_PASSWORD}")

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

    # Header
    headers = list(registrations[0].keys())
    ws.append(headers)

    row_index = 2
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

# --- Datenschutz-Seite ---
@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")


if __name__ == "__main__":
    app.run(debug=True)
