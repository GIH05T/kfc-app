from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# temporäre Speicherung der Anmeldungen in einer Liste
registrations = []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Daten aus dem Formular auslesen
        data = {
            "Vorname": request.form.get("Vorname"),
            "Nachname": request.form.get("Nachname"),
            "Email": request.form.get("email"),
            "Strasse": request.form.get("strasse"),
            "PLZ": request.form.get("plz"),
            "Ort": request.form.get("ort"),
            "Geburtsdatum": request.form.get("geburtsdatum"),
            "Notfallnummer": request.form.get("notfallnummer"),
            "Allergien": request.form.get("allergien"),
            "DSGVO": request.form.get("dsgvo")
        }
        registrations.append(data)
        return redirect(url_for("success"))

    return render_template("index.html")


@app.route("/success")
def success():
    return "<h2>Danke für die Anmeldung!</h2><p><a href='/'>Zurück</a></p>"

@app.route("/admin")
def admin():
    # einfache Passwort-Abfrage
    from flask import request, abort
    admin_password = "MEINADMINPASSWORT"
    pw = request.args.get("pw")
    if pw != admin_password:
        abort(403, "Zugriff verweigert")
    # Liste der Anmeldungen anzeigen
    html = "<h1>Adminbereich</h1><ul>"
    for r in registrations:
        html += f"<li>{r}</li>"
    html += "</ul>"
    return html

if __name__ == "__main__":
    app.run(debug=True)
