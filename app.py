from flask import Flask, render_template, request, redirect, url_for, send_file
import json, os
from datetime import date
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
import base64

app = Flask(__name__)
DATA_FILE = "registrations.json"
ADMIN_PASSWORD = "MEINADMINPASSWORT"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_id():
    regs = load_data()
    return max([r["ID"] for r in regs], default=0) + 1

def calculate_age(birthdate_str):
    y, m, d = map(int, birthdate_str.split("-"))
    today = date.today()
    age = today.year - y - ((today.month, today.day) < (m, d))
    return age

def calculate_group(age):
    if age <= 7:
        return "5-7"
    elif age <= 13:
        return "8-13"
    else:
        return "14+"

def calculate_points(bibelverse, anwesenheit):
    return bibelverse + sum(anwesenheit)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        regs = load_data()
        reg_id = generate_id()
        # Anwesenheit-Tage standardmäßig False
        anwesenheit = [False]*5
        data = {
            "ID": reg_id,
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("Email"),
            "Strasse": request.form.get("Strasse"),
            "PLZ": request.form.get("PLZ"),
            "Ort": request.form.get("Ort"),
            "Geburtsdatum": request.form.get("Geburtsdatum"),
            "Alter": calculate_age(request.form.get("Geburtsdatum")),
            "Gruppe": calculate_group(calculate_age(request.form.get("Geburtsdatum"))),
            "Notfallnummer": request.form.get("Notfallnummer"),
            "Allergien": request.form.get("Allergien"),
            "Bibelverse": int(request.form.get("Bibelverse",0)),
            "Anwesenheit": anwesenheit,
            "Punkte": int(request.form.get("Bibelverse",0)),
            "Unterschrift": request.form.get("Unterschrift"),
            "DSGVO": bool(request.form.get("DSGVO"))
        }
        regs.append(data)
        save_data(regs)
        return redirect(url_for("success", reg_id=reg_id))
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    regs = load_data()
    search_query = request.args.get("search", "").lower()
    if search_query:
        regs = [r for r in regs if search_query in str(r["ID"]) or search_query in r["Vorname"].lower() or search_query in r["Nachname"].lower()]

    return render_template("admin.html", registrations=regs, pw=pw, search_query=search_query)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    pw = request.args.get("pw", ADMIN_PASSWORD)
    regs = load_data()
    for r in regs:
        if r["ID"] == id:
            r["Vorname"] = request.form.get("Vorname")
            r["Nachname"] = request.form.get("Nachname")
            r["Ort"] = request.form.get("Ort")
            r["PLZ"] = request.form.get("PLZ")
            r["Notfallnummer"] = request.form.get("Notfallnummer")
            r["Allergien"] = request.form.get("Allergien")
            r["Bibelverse"] = int(request.form.get("Bibelverse",0))
            # Checkboxen Anwesenheit
            anwesenheit = []
            for i in range(1,6):
                anwesenheit.append(bool(request.form.get(f"Tag{i}")))
            r["Anwesenheit"] = anwesenheit
            r["Punkte"] = calculate_points(r["Bibelverse"], anwesenheit)
            r["Alter"] = calculate_age(r["Geburtsdatum"])
            r["Gruppe"] = calculate_group(r["Alter"])
            break
    save_data(regs)
    return redirect(url_for("admin", pw=pw))

@app.route("/delete/<int:id>")
def delete(id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    regs = load_data()
    regs = [r for r in regs if r["ID"] != id]
    save_data(regs)
    return redirect(url_for("admin", pw=pw))

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

@app.route("/export_excel")
def export_excel():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    regs = load_data()
    if not regs:
        return "Keine Daten", 400

    wb = Workbook()
    ws = wb.active
    ws.title = "Anmeldungen"
    headers = list(regs[0].keys())
    ws.append(headers)
    row_index = 2
    for r in regs:
        col_index = 1
        for h in headers:
            if h=="Unterschrift" and r[h]:
                data_url = r[h]
                if data_url.startswith("data:image/png;base64,"):
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
