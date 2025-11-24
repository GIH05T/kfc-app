from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- In-memory "Datenbank" ---
anmeldungen = []

# --- Routen ---
@app.route("/")
def index():
    return render_template("form.html")

@app.route("/anmelden", methods=["POST"])
def anmelden():
    # Prüfen, ob DSGVO angekreuzt wurde
    if not request.form.get("dsgvo"):
        return "Bitte DSGVO bestätigen.", 400

    # Alle Felder erfassen
    eintrag = {
        "Vorname": request.form.get("Vorname"),
        "Nachname": request.form.get("Nachname"),
        "email": request.form.get("email"),
        "strasse": request.form.get("strasse"),
        "plz": request.form.get("plz"),
        "ort": request.form.get("ort"),
        "geburtsdatum": request.form.get("geburtsdatum"),
        "notfallnummer": request.form.get("notfallnummer"),
        "allergien": request.form.get("allergien")
    }

    # Speichern in Liste
    anmeldungen.append(eintrag)

    return redirect(url_for("danke"))

@app.route("/danke")
def danke():
    return "<h1>Vielen Dank für die Anmeldung!</h1><a href='/'>Zurück</a>"

@app.route("/admin")
def admin():
    return render_template("admin.html", anmeldungen=anmeldungen)

# --- Admin Seite ---
# admin.html sollte eine Tabelle mit allen Anmeldungen anzeigen

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
