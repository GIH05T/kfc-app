from flask import Flask, render_template, request, redirect, send_file
import openpyxl
from io import BytesIO
from datetime import date, datetime

app = Flask(__name__)

# Beispiel-Datenstruktur
class Registration:
    def __init__(self, ID, Vorname, Nachname, Geburtsdatum, Alter, Geschlecht, Gruppe, Verse, Anwesenheit, Punkte, Unterschrift):
        self.ID = ID
        self.Vorname = Vorname
        self.Nachname = Nachname
        self.Geburtsdatum = Geburtsdatum
        self.Alter = Alter
        self.Geschlecht = Geschlecht
        self.Gruppe = Gruppe
        self.Verse = Verse  # Liste von 5 bools
        self.Anwesenheit = Anwesenheit  # Liste von 5 bools
        self.Punkte = Punkte
        self.Unterschrift = Unterschrift

# Beispielregistrierungen
registrations = [
    Registration(1,"Max","Muster","2010-05-12",13,"m","8-13",[1,0,1,1,0],[1,1,1,0,1],5,"/static/sign1.png"),
    Registration(2,"Anna","Beispiel","2015-03-22",8,"w","5-7",[1,1,1,0,0],[1,0,1,1,1],7,"/static/sign2.png")
]

ADMIN_PASSWORD = "MEINADMINPASSWORT"

# ---------------- Admin-Seite ----------------
@app.route("/admin")
def admin():
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Falsches Passwort", 403
    return render_template("admin.html", registrations=registrations)

# ---------------- Update einer Zeile ----------------
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    for r in registrations:
        if r.ID == id:
            r.Vorname = request.form.get("Vorname")
            r.Nachname = request.form.get("Nachname")
            r.Geburtsdatum = request.form.get("Geburtsdatum")
            r.Geschlecht = request.form.get("Geschlecht")
            r.Verse = [int(bool(request.form.get(f"Verse{i}"))) for i in range(1,6)]
            r.Anwesenheit = [int(bool(request.form.get(f"Tag{i}"))) for i in range(1,6)]
            r.Punkte = sum(r.Verse)+sum(r.Anwesenheit)
            # Alter berechnen
            if r.Geburtsdatum:
                bd = datetime.strptime(r.Geburtsdatum, "%Y-%m-%d").date()
                today = date.today()
                r.Alter = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                # Gruppe automatisch
                if 5 <= r.Alter <= 7:
                    r.Gruppe = "5-7"
                elif 8 <= r.Alter <= 13:
                    r.Gruppe = "8-13"
    return redirect(f"/admin?pw={ADMIN_PASSWORD}")

# ---------------- Löschen ----------------
@app.route("/delete/<int:id>")
def delete(id):
    pw = request.args.get("pw")
    if pw != ADMIN_PASSWORD:
        return "Falsches Passwort", 403
    global registrations
    registrations = [r for r in registrations if r.ID != id]
    return redirect(f"/admin?pw={ADMIN_PASSWORD}")

# ---------------- Excel-Export ----------------
@app.route("/export")
def export():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registrierungen"
    ws.append(["ID","Vorname","Nachname","Geburtsdatum","Alter","Geschlecht","Gruppe","Verse","Anwesenheit","Punkte"])
    for r in registrations:
        verse_str = ",".join([str(v) for v in r.Verse])
        anwesenheit_str = ",".join([str(a) for a in r.Anwesenheit])
        ws.append([r.ID,r.Vorname,r.Nachname,r.Geburtsdatum,r.Alter,r.Geschlecht,r.Gruppe,verse_str,anwesenheit_str,r.Punkte])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name="registrierungen.xlsx", as_attachment=True)

# ---------------- App starten ----------------
if __name__ == "__main__":
    app.run(debug=True)
