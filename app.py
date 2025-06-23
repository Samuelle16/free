import os
from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import json
from flask import send_file
import io

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

# Initialisation Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crée le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Vérifie l'extension du fichier
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Page principale
@app.route('/')
def home():
    return render_template('FREE.html')

# Route d'upload du fichier Excel principal
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'excelFile' not in request.files:
        return "Aucun fichier trouvé", 400

    file = request.files['excelFile']

    if file and allowed_file(file.filename):
        filename = "dernier_fichier.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath)

            # ✅ Conversion en tableau brut
            df_str = df.astype(str)
            data_list = [df_str.columns.tolist()] + df_str.values.tolist()

            with open("static/donnees.json", "w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False)

        except Exception as e:
            return f"Erreur de lecture Excel : {e}", 500

        return redirect('/?reload=1')

    return "Fichier non autorisé", 400




@app.route('/import_penalites', methods=['POST'])
def import_penalites():
    file = request.files.get('penaliteFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    df = pd.read_excel(file)
    vendeur_to_penalite = {}

    for _, row in df.iterrows():
        vendeur = str(row["Vendeur"]).strip()
        penalite = float(row["Penalite"])
        if vendeur:
            vendeur_to_penalite[vendeur] = penalite

    with open("static/penalites.json", "w", encoding="utf-8") as f:
        json.dump(vendeur_to_penalite, f, ensure_ascii=False, indent=2)

    return redirect("/?reload=1")



@app.route("/static/donnees.json")
def serve_donnees():
    return send_from_directory("static", "donnees.json")

@app.route('/save_bonus_malus', methods=['POST'])
def save_bonus_malus():
    data = request.get_json()
    with open("static/bonus_malus.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"message": "Bonus/malus enregistré"}


# Route d'import des formateurs
@app.route('/import_formateurs', methods=['POST'])
def import_formateurs():
    file = request.files.get('formateurFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    df = pd.read_excel(file)
    vendeur_to_formateurs = {}

    for _, row in df.iterrows():
        vendeur = str(row[0]).strip()     # Colonne 1 : vendeur
        formateur = str(row[1]).strip()   # Colonne 2 : formateur
        if vendeur and formateur:
            vendeur_to_formateurs.setdefault(vendeur, []).append(formateur)

    # Supprimer les doublons
    for vendeur in vendeur_to_formateurs:
        vendeur_to_formateurs[vendeur] = list(set(vendeur_to_formateurs[vendeur]))

    # ✅ Sauvegarder dans formateurs.json
    with open("static/formateurs.json", "w", encoding="utf-8") as f:
        json.dump(vendeur_to_formateurs, f, ensure_ascii=False, indent=2)

    # 🔄 Charger les ventes actuelles
    try:
        with open("static/donnees.json", "r", encoding="utf-8") as f:
            ventes = json.load(f)
    except:
        ventes = []

    if ventes:
        headers = ventes[0]
        data = ventes[1:]

        # Liste des vendeurs déjà présents
        vendeurs_existants = {row[6] for row in data if len(row) > 6}

        # Ajouter une ligne factice pour chaque formateur absent (juste pour stats)
        for formateurs in vendeur_to_formateurs.values():
            for f in formateurs:
                if f not in vendeurs_existants:
                    ligne_vierge = [""] * len(headers)
                    ligne_vierge[6] = f  # Colonne 7 = vendeur
                    data.append(ligne_vierge)

        with open("static/donnees.json", "w", encoding="utf-8") as f:
            json.dump([headers] + data, f, ensure_ascii=False, indent=2)

    return redirect("/?reload=1")


@app.route("/save_bonus", methods=["POST"])
def save_bonus():
    data = request.get_json()
    vendeur = data.get("vendeur")
    value = data.get("value")

    try:
        path = "static/bonus_manuels.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                bonus_data = json.load(f)
        else:
            bonus_data = {}

        bonus_data[vendeur] = value

        with open(path, "w", encoding="utf-8") as f:
            json.dump(bonus_data, f, ensure_ascii=False, indent=2)

        return "OK", 200
    except Exception as e:
        return f"Erreur: {str(e)}", 500


@app.route("/save_palier", methods=["POST"])
def save_palier():
    data = request.get_json()
    with open("static/paliers_voulus.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"message": "Paliers enregistrés"}


@app.route('/import_vrais_vendeurs', methods=['POST'])
def import_vrais_vendeurs():
    file = request.files.get('vraisFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    try:
        df_vrais = pd.read_excel(file, header=None)
        corrections = df_vrais.values.tolist()

        with open("static/donnees.json", encoding="utf-8") as f:
            ventes = json.load(f)

        headers = ventes[0]
        ventes_data = ventes[1:]

        for correction in corrections:
            try:
                if len(correction) < 2:
                    continue

                code_emprunte = str(correction[0]).strip()  # colonne 1
                vrai_vendeur = str(correction[1]).strip()   # colonne 2

                for ligne in ventes_data:
                    vendeur = str(ligne[6]).strip()  # colonne 7 = vendeur
                    if vendeur == code_emprunte:
                        ligne[6] = vrai_vendeur
            except Exception as e:
                print("Erreur traitement ligne vrai vendeur :", e)

        with open("static/donnees.json", "w", encoding="utf-8") as f:
            json.dump([headers] + ventes_data, f, ensure_ascii=False, indent=2)

        return redirect("/?reload=1")

    except Exception as e:
        return f"Erreur de traitement : {e}", 500



@app.route('/import_anomalies', methods=['POST'])
def import_anomalies():
    file = request.files.get('anomalieFile')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        return "Fichier non valide", 400

    try:
        df_anomalies = pd.read_excel(file, header=None)
        anomalies = df_anomalies.values.tolist()

        with open("static/donnees.json", encoding="utf-8") as f:
            ventes = json.load(f)

        headers = ventes[0]
        ventes_data = ventes[1:]

        for anomaly in anomalies:
            try:
                bon_vendeur = str(anomaly[2]).strip()  # colonne 3
                fo_anomaly = str(anomaly[3]).strip()   # colonne 4

                for ligne in ventes_data:
                    fo_vente = str(ligne[3]).strip()   # colonne 4 dans ventes
                    if fo_vente == fo_anomaly:
                        ligne[6] = bon_vendeur         # remplace le vendeur (colonne 7)
            except Exception as e:
                print("Erreur traitement ligne :", e)

        with open("static/donnees.json", "w", encoding="utf-8") as f:
            json.dump([headers] + ventes_data, f, ensure_ascii=False, indent=2)

        return redirect("/?reload=1")

    except Exception as e:
        return f"Erreur de traitement : {e}", 500

@app.route("/reset_bonus", methods=["POST"])
def reset_bonus():
    with open("static/bonus_manuels.json", "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False)
    return "Bonus réinitialisés", 200

@app.route("/reset_penalites", methods=["POST"])
def reset_penalites():
    with open("static/penalites.json", "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False)
    return "Pénalités réinitialisées", 200

@app.route('/reset_paliers', methods=['POST'])
def reset_paliers():
    try:
        path = "static/paliers_voulus.json"
        if os.path.exists(path):
            os.remove(path)
        return "OK", 200
    except Exception as e:
        return f"Erreur : {e}", 500




# Lancement local
if __name__ == '__main__':
    app.run(debug=True)