from flask import Flask, render_template, request, redirect, url_for, jsonify
import json, os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "registrations.json"
ADMIN_PASSWORD = "MEINADMINPASSWORT"

# -------------------------
# JSON HILFSFUNKTIONEN
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_id():
    data = load_data()
    used_ids = sorted([d["ID"] for d in data])
    new_id = 1
    for i in used_ids:
        if i != new_id:
            break
        new_id += 1
    return new_id

def calculate_age(birthdate):
    if not birthdate:
        return ""
    b = datetime.strptime(birthdate, "%Y-%m-%d")
    today = datetime.today()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


# -------------------------
# ANMELDUNG
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = load_data()

        new_id = generate_id()
        age = calculate_age(request.form.get("geburtsdatum"))

        child = {
            "ID": new_id,
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("email"),
            "Strasse": request.form.get("strasse"),
            "PLZ": request.form.get("plz"),
            "Ort": request.form.get("ort"),
            "Geburtsdatum": request.form.get("geburtsdatum"),
            "Alter": age,
            "Notfallnummer": request.form.get("notfallnummer"),
            "Allergien": request.form.get("allergien"),
            "Unterschrift": request.form.get("unterschrift"),

            # Admin-Felder (leer vorbelegt)
            "Geschlecht": "",
            "Gruppe": "",
            "Verse": 0,
            "Anwesenheit": 0,
            "Punkte": 0
        }

        data.append(child)
        save_data(data)

        return redirect(url_for("success", reg_id=new_id))

    return render_template("index.html")


@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return f"""
    <h2>Danke für die Anmeldung!</h2>
    <p>Deine ID: <b>{reg_id}</b></p>
    <a href="/">Weiteres Kind anmelden</a>
    """


# -------------------------
# ADMIN SEITE
# -------------------------
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Zugriff verweigert", 403

    data = load_data()
    return render_template("admin.html", registrations=data)


# -------------------------
# KIND SPEICHERN (ADMIN)
# -------------------------
@app.route("/update/<int:child_id>", methods=["POST"])
def update_child(child_id):
    data = load_data()

    for child in data:
        if child["ID"] == child_id:
            child["Vorname"] = request.form.get("Vorname")
            child["Nachname"] = request.form.get("Nachname")
            child["Email"] = request.form.get("Email")
            child["Strasse"] = request.form.get("Strasse")
            child["PLZ"] = request.form.get("PLZ")
            child["Ort"] = request.form.get("Ort")
            child["Notfallnummer"] = request.form.get("Notfallnummer")
            child["Allergien"] = request.form.get("Allergien")

            child["Geschlecht"] = request.form.get("Geschlecht")
            child["Gruppe"] = request.form.get("Gruppe")
            child["Verse"] = int(request.form.get("Verse", 0))
            child["Anwesenheit"] = int(request.form.get("Anwesenheit", 0))

            # Punkte berechnen
            child["Punkte"] = child["Verse"] + child["Anwesenheit"]

    save_data(data)
    return redirect(request.referrer)


# -------------------------
# KIND LÖSCHEN (ADMIN)
# -------------------------
@app.route("/delete/<int:child_id>")
def delete_child(child_id):
    data = load_data()
    data = [c for c in data if c["ID"] != child_id]
    save_data(data)
    return redirect(request.referrer)


# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
