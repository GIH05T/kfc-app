from flask import Flask, render_template, request, redirect, url_for, send_file
import json, os, datetime
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
import base64

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

# --- Alter & Gruppe berechnen ---
def calculate_age_and_group(birthdate_str):
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if 5 <= age <= 7:
            group = "5-7"
        elif 8 <= age <= 13:
            group = "8-13"
        else:
            group = "?"
        return age, group
    except:
        return None, "?"

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        registrations = load_data()
        reg_id = generate_id()
        data = {
            "ID": reg_id,
            "Geschlecht": request.form.get("Geschlecht"),
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
            # Anmeldung: Tage & Verse
            "Tag1": bool(request.form.get("Tag1")),
            "Tag2": bool(request.form.get("Tag2")),
            "Tag3": bool(request.form.get("Tag3")),
            "Tag4": bool(request.form.get("Tag4")),
            "Tag5": bool(request.form.get("Tag5")),
            "Verse1": bool(request.form.get("Verse1")),
            "Verse2": bool(request.form.get("Verse2")),
            "Verse3": bool(request.form.get("Verse3")),
            "Verse4": bool(request.form.get("Verse4")),
            "Verse5": bool(request.form.get("Verse5")),
        }
        age, group = calculate_age_and_group(data["Geburtsdatum"])
        data["Alter"] = age
        data["Gruppe"] = group
        # Punkte berechnen: Summe von Tag + Verse
        data["Punkte"] = sum([data[f"Tag{i}"] + data[f"Verse{i}"] for i in range(1,6)])
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

    # Berechne Alter & Gruppe nochmal für Anzeige
    for r in registrations:
        age, group = calculate_age_and_group(r.get("Geburtsdatum",""))
        r["Alter"] = age
        r["Gruppe"] = group

    search_query = request.args.get("search","").lower()
    if search_query:
        registrations = [r for r in registrations if search_query in str(r["ID"]) 
                         or search_query in r["Vorname"].lower() 
                         or search_query in r["Nachname"].lower()]

    return render_template("admin.html", registrations=registrations, pw=pw, search_query=search_query)

# --- Update Eintrag ---
@app.route("/update/<int:reg_id>", methods=["POST"])
def update_entry(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    for r in registrations:
        if r["ID"] == reg_id:
            for key in r.keys():
                if key in request.form:
                    value = request.form[key]
                    # Checkboxen speichern als bool
                    if key.startswith("Tag") or key.startswith("Verse"):
                        r[key] = value == "on"
                    else:
                        r[key] = value
            # Alter & Gruppe aktualisieren
            age, group = calculate_age_and_group(r.get("Geburtsdatum",""))
            r["Alter"] = age
            r["Gruppe"] = group
            # Punkte aktualisieren
            r["Punkte"] = sum([r[f"Tag{i}"] + r[f"Verse{i}"] for i in range(1,6)])
            break
    save_data(registrations)
    return redirect(url_for("admin", pw=pw))

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
