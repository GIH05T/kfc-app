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

def generate_id():
    registrations = load_data()
    return max([r["ID"] for r in registrations], default=0) + 1

def calculate_age(birthdate):
    if not birthdate:
        return ""
    try:
        bdate = datetime.strptime(birthdate, "%Y-%m-%d")
        today = datetime.today()
        return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
    except:
        return ""

def calculate_points(reg):
    points = 0
    for i in range(1,6):
        points += int(reg.get(f"Tag{i}", 0))
        points += int(reg.get(f"Verse{i}", 0))
    return points

# --- Routes ---
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
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
        # Tag und Verse Checkboxen
        for i in range(1,6):
            data[f"Tag{i}"] = 1 if request.form.get(f"Tag{i}")=="on" else 0
            data[f"Verse{i}"] = 1 if request.form.get(f"Verse{i}")=="on" else 0

        data["Punkte"] = calculate_points(data)
        data["Alter"] = calculate_age(data["Geburtsdatum"])
        
        regs = load_data()
        regs.append(data)
        save_data(regs)
        return redirect(url_for("success", reg_id=reg_id))
    return render_template("index.html")

@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

@app.route("/admin", methods=["GET","POST"])
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    regs = load_data()
    
    # Suche
    search = request.args.get("search","").lower()
    if search:
        regs = [r for r in regs if search in str(r["ID"]) or search in r["Vorname"].lower() or search in r["Nachname"].lower()]

    # Sortierung
    sort_by = request.args.get("sort_by","ID")
    reverse = request.args.get("reverse","0")=="1"
    if sort_by in ["ID","Vorname","Nachname"]:
        regs.sort(key=lambda r: r[sort_by], reverse=reverse)

    return render_template("admin.html", registrations=regs, pw=pw, search_query=search, sort_by=sort_by, reverse=reverse)

@app.route("/update/<int:reg_id>", methods=["POST"])
def update(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    regs = load_data()
    for r in regs:
        if r["ID"] == reg_id:
            # Update Felder
            for key in request.form.keys():
                r[key] = request.form[key]
            # Tag/Verse checkboxes
            for i in range(1,6):
                r[f"Tag{i}"] = 1 if request.form.get(f"Tag{i}")=="on" else 0
                r[f"Verse{i}"] = 1 if request.form.get(f"Verse{i}")=="on" else 0
            r["Punkte"] = calculate_points(r)
            r["Alter"] = calculate_age(r["Geburtsdatum"])
            break
    save_data(regs)
    return redirect(url_for("admin", pw=pw))

@app.route("/delete/<int:reg_id>")
def delete(reg_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    regs = load_data()
    regs = [r for r in regs if r["ID"] != reg_id]
    save_data(regs)
    return redirect(url_for("admin", pw=pw))

@app.route("/export_excel")
def export_excel():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403
    regs = load_data()
    if not regs:
        return "Keine Daten",400

    wb = Workbook()
    ws = wb.active
    ws.title = "Anmeldungen"
    headers = ["ID","Geschlecht","Vorname","Nachname","Strasse","PLZ","Ort","Notfallnummer","Allergien","Tag1","Tag2","Tag3","Tag4","Tag5",
               "Verse1","Verse2","Verse3","Verse4","Verse5","Punkte","Alter","Unterschrift"]
    ws.append(headers)

    for r in regs:
        row=[]
        for h in headers:
            if h=="Unterschrift" and r.get("Unterschrift"):
                data_url = r["Unterschrift"]
                if data_url.startswith("data:image/png;base64,"):
                    img_data = base64.b64decode(data_url.split(",")[1])
                    img = XLImage(BytesIO(img_data))
                    row.append("") # placeholder
            else:
                row.append(r.get(h,""))
        ws.append(row)
    # Images einfügen
    for idx,r in enumerate(regs, start=2):
        if r.get("Unterschrift") and r["Unterschrift"].startswith("data:image/png;base64,"):
            img_data = base64.b64decode(r["Unterschrift"].split(",")[1])
            img = XLImage(BytesIO(img_data))
            ws.add_image(img, f"R{idx}")
    output="registrations.xlsx"
    wb.save(output)
    return send_file(output, as_attachment=True)

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

if __name__=="__main__":
    app.run(debug=True)
