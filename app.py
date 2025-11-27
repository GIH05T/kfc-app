from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import json
import os
from datetime import datetime, date

app = Flask(__name__)

DATA_FILE = "registrations.json"

# --- Hilfsfunktionen: Laden / Speichern ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- ID-Generierung: kleinste freie positive ganze Zahl ---
def generate_id():
    regs = load_data()
    used = sorted([r.get("ID", 0) for r in regs if isinstance(r.get("ID", None), int)])
    i = 1
    for u in used:
        if u == i:
            i += 1
        elif u > i:
            break
    return i

# --- Alter berechnen aus Geburtsdatum (YYYY-MM-DD) ---
def calc_age(birthdate_str):
    if not birthdate_str:
        return None
    try:
        bd = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    except Exception:
        return None
    today = date.today()
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return age

# --- Gruppe bestimmen (5-7 oder 8-13) ---
def group_for_age(age):
    if age is None:
        return None
    if 5 <= age <= 7:
        return "5-7"
    elif 8 <= age <= 13:
        return "8-13"
    else:
        return None

# --- Punkte berechnen aus days + verses (beide dicts mit mo..fr boolean/int) ---
def compute_points(reg):
    days = reg.get("days", {})
    verses = reg.get("verses", {})
    days_count = sum(1 for k in ["mo","di","mi","do","fr"] if days.get(k))
    verses_count = sum(1 for k in ["mo","di","mi","do","fr"] if verses.get(k))
    return days_count + verses_count

# --- Startseite / Anmeldung (minimal, damit Admin funktioniert) ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        regs = load_data()
        reg_id = generate_id()
        # Daten aus Formular
        vorname = request.form.get("Vorname", "").strip()
        nachname = request.form.get("Nachname", "").strip()
        email = request.form.get("email", "").strip()
        strasse = request.form.get("strasse", "").strip()
        plz = request.form.get("plz", "").strip()
        ort = request.form.get("ort", "").strip()
        geburtsdatum = request.form.get("geburtsdatum", "").strip()
        notfall = request.form.get("notfallnummer", "").strip()
        allergien = request.form.get("allergien", "").strip()
        unterschrift = request.form.get("unterschrift", "").strip()  # dataURL
        dsgvo = bool(request.form.get("dsgvo"))

        new = {
            "ID": reg_id,
            "Vorname": vorname,
            "Nachname": nachname,
            "Email": email,
            "Strasse": strasse,
            "PLZ": plz,
            "Ort": ort,
            "Geburtsdatum": geburtsdatum,
            "Notfallnummer": notfall,
            "Allergien": allergien,
            "Unterschrift": unterschrift,
            "DSGVO": dsgvo,
            # Admin-Felder initial leer/default
            "Gender": "",  # "M" oder "W"
            "days": {"mo": False, "di": False, "mi": False, "do": False, "fr": False},
            "verses": {"mo": False, "di": False, "mi": False, "do": False, "fr": False},
            # computed
            "Age": calc_age(geburtsdatum),
            "Group": group_for_age(calc_age(geburtsdatum)),
            "Points": 0
        }
        new["Points"] = compute_points(new)
        regs.append(new)
        save_data(regs)
        return render_template("index.html", success=True, reg_id=reg_id)
    return render_template("index.html")

# --- Admin Seite: Anzeigen ---
@app.route("/admin")
def admin():
    # einfache Passwortabfrage per Query param? (nicht sicher, aber minimal)
    pw = request.args.get("pw")
    ADMIN_PASSWORD = "MEINADMINPASSWORT"
    if pw != ADMIN_PASSWORD:
        abort(403)
    regs = load_data()
    # Recompute age/group/points for display safety
    for r in regs:
        r["Age"] = calc_age(r.get("Geburtsdatum", "")) or r.get("Age")
        r["Group"] = group_for_age(r.get("Age")) if r.get("Age") is not None else r.get("Group")
        r["Points"] = compute_points(r)
    return render_template("admin.html", registrations=regs, pw=pw)

# --- Admin: Save (bulk) ---
@app.route("/admin/save", methods=["POST"])
def admin_save():
    pw = request.args.get("pw")
    ADMIN_PASSWORD = "MEINADMINPASSWORT"
    if pw != ADMIN_PASSWORD:
        abort(403)
    regs = load_data()
    # Expect many fields like Vorname_<id>, Gender_<id>, day_mo_<id> etc.
    updated = []
    id_map = {r["ID"]: r for r in regs}
    for key, val in request.form.items():
        # parse
        # We'll iterate by IDs present in current data
        pass

    # Simpler approach: iterate over existing regs and update from form
    for r in regs:
        rid = r["ID"]
        prefix = f"ID_{rid}_"  # we'll name fields like ID_{rid}_Vorname etc.
        # If form uses this naming scheme:
        # Vorname: Vorname_<id> etc. (we accept both)
        def getf(name):
            # try name_{id} then ID_{id}_{name}
            v = request.form.get(f"{name}_{rid}")
            if v is None:
                v = request.form.get(f"ID_{rid}_{name}")
            return v

        # Text fields
        r["Vorname"] = getf("Vorname") or r.get("Vorname","")
        r["Nachname"] = getf("Nachname") or r.get("Nachname","")
        r["Email"] = getf("Email") or r.get("Email","")
        r["Strasse"] = getf("Strasse") or r.get("Strasse","")
        r["PLZ"] = getf("PLZ") or r.get("PLZ","")
        r["Ort"] = getf("Ort") or r.get("Ort","")
        r["Geburtsdatum"] = getf("Geburtsdatum") or r.get("Geburtsdatum","")
        r["Notfallnummer"] = getf("Notfallnummer") or r.get("Notfallnummer","")
        r["Allergien"] = getf("Allergien") or r.get("Allergien","")
        # Gender
        gender_val = getf("Gender")
        if gender_val is not None:
            r["Gender"] = gender_val

        # Days & Verses: checkboxes; form sends "on" or value for checked boxes
        days = {}
        verses = {}
        for d in ["mo","di","mi","do","fr"]:
            day_field1 = f"{d}_{rid}"
            day_field2 = f"ID_{rid}_day_{d}"
            verses_field1 = f"v_{d}_{rid}"
            verses_field2 = f"ID_{rid}_verse_{d}"
            # attendance
            if request.form.get(day_field1) or request.form.get(day_field2):
                days[d] = True
            else:
                days[d] = False
            # verse
            if request.form.get(verses_field1) or request.form.get(verses_field2):
                verses[d] = True
            else:
                verses[d] = False
        r["days"] = days
        r["verses"] = verses

        # recompute age/group/points
        r["Age"] = calc_age(r.get("Geburtsdatum","")) or r.get("Age")
        r["Group"] = group_for_age(r.get("Age")) if r.get("Age") is not None else r.get("Group")
        r["Points"] = compute_points(r)

    save_data(regs)
    return redirect(url_for("admin", pw=pw))

# --- Admin: Delete single child ---
@app.route("/admin/delete/<int:child_id>", methods=["POST"])
def admin_delete(child_id):
    pw = request.args.get("pw")
    ADMIN_PASSWORD = "MEINADMINPASSWORT"
    if pw != ADMIN_PASSWORD:
        abort(403)
    regs = load_data()
    new_regs = [r for r in regs if r.get("ID") != child_id]
    if len(new_regs) == len(regs):
        # not found
        abort(404)
    save_data(new_regs)
    # Note: ID reuse will happen in generate_id() next time someone registers
    return redirect(url_for("admin", pw=pw))

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
