from flask import Flask, render_template, request, redirect, url_for, abort
import json, os
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "registrations.json"
ADMIN_PASSWORD = "MEINADMINPASSWORT"

# -----------------------------
# JSON Laden / Speichern
# -----------------------------
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
    used_ids = [d["ID"] for d in data]
    i = 1
    while i in used_ids:
        i += 1
    return i

# -----------------------------
# INDEX / ANMELDUNG
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = load_data()
        new_id = generate_id()

        entry = {
            "ID": new_id,
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
            "DSGVO": True,
            "Zeitstempel": datetime.now().isoformat()
        }

        data.append(entry)
        save_data(data)

        return redirect(url_for("success", reg_id=new_id))

    return render_template("index.html")

# -----------------------------
# SUCCESS SEITE (MIT GROSSER ID)
# -----------------------------
@app.route("/success")
def success():
    reg_id = request.args.get("reg_id")
    return render_template("success.html", reg_id=reg_id)

# -----------------------------
# ADMIN SEITE MIT SUCHE
# -----------------------------
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        abort(403)

    query = request.args.get("q", "").lower()
    data = load_data()

    if query:
        data = [
            d for d in data
            if query in str(d["ID"]).lower()
            or query in d["Vorname"].lower()
            or query in d["Nachname"].lower()
        ]

    return render_template("admin.html", registrations=data)

# -----------------------------
# KIND LÖSCHEN
# -----------------------------
@app.route("/delete/<int:child_id>")
def delete(child_id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        abort(403)

    data = load_data()
    data = [d for d in data if d["ID"] != child_id]
    save_data(data)

    return redirect(f"/admin?pw={ADMIN_PASSWORD}")

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
