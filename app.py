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
    return max((r["ID"] for r in registrations), default=0) + 1

# --- Alter & Gruppe berechnen ---
def calculate_age_and_group(birthdate_str):
    try:
        birthdate = datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
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
        }

        # Initiale Tages-/Verswerte
        for i in range(1, 6):
            data[f"Tag{i}"] = False
            data[f"Verse{i}"] = False

        age, group = calculate_age_and_group(data["Geburtsdatum"])
        data["Alter"] = age
        data["Gruppe"] = group
        data["Punkte"] = 0

        registrations.append(data)
        save_data(registrations)
        return redirect(url_for("success", reg_id=reg_id))

    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# --- Admin ---
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()

    for r in registrations:
        age, group = calculate_age_and_group(r.get("Geburtsdatum", ""))
        r["Alter"] = age
        r["Gruppe"] = group

    search_query = request.args.get("search", "").lower()
    if search_query:
        registrations = [
            r for r in registrations
            if search_query in str(r["ID"])
            or search_query in r["Vorname"].lower()
            or search_query in r["Nachname"].lower()
        ]

    return render_template(
        "admin.html",
        registrations=registrations,
        pw=pw,
        search_query=search_query
    )

# --- Update Eintrag ---
@app.route("/update/<int:reg_id>", methods=["POST"])
def update_entry(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()

    for r in registrations:
        if r["ID"] == reg_id:

            # FIX: Checkboxen IMMER explizit setzen
            for i in range(1, 6):
                r[f"Tag{i}"] = f"Tag{i}" in request.form
                r[f"Verse{i}"] = f"Verse{i}" in request.form

            # andere Felder
            for key in r.keys():
                if key in request.form and not key.startswith(("Tag", "Verse")):
                    r[key] = request.form.get(key)

            age, group = calculate_age_and_group(r.get("Geburtsdatum", ""))
            r["Alter"] = age
            r["Gruppe"] = group

            r["Punkte"] = sum(
                r[f"Tag{i}"] + r[f"Verse{i}"] for i in range(1, 6)
            )
            break

    save_data(registrations)
    return redirect(url_for("admin", pw=pw))

# --- DELETE FIX ---
@app.route("/delete/<int:reg_id>")
def delete_entry(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    registrations = load_data()
    registrations = [r for r in registrations if r["ID"] != reg_id]
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
            if h == "Unterschrift" and r[h]:
                data_url = r[h]
                if data_url.startswith("data:image/png;base64,"):
                    img_data = base64.b64decode(data_url.split(",")[1])
                    img = XLImage(BytesIO(img_data))
                    ws.add_image(img, ws.cell(row=row_index, column=col_index).coordinate)
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
